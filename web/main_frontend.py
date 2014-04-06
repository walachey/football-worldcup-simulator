import sys
import random
from datetime import datetime

# local includes
from configuration import main_configuration as config
from database_models import *
import dispatcher
import dispatcher_local
import admin_interface

# third-party includes
from flask import abort, redirect, url_for, render_template, flash, request, session as user_session, make_response, Response
from flask import Flask
from flask.ext.cache import Cache
import jinja2
import re, md5
import subprocess
import json


import smtplib
from email.mime.text import MIMEText
import socket # for catching socket.error

app = config.getFlaskApp()
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
admin_interface.init(app)
simulation_dispatcher = dispatcher_local.DispatcherLocal(db, config)
# initialize random numbers for user ID generation
random.seed()

# set some global config options that are used in the base template
@app.context_processor
def define_globals():
	return {
		"show_custom_tournament_page": config.show_custom_tournament_page
	}

@app.route('/')
@cache.cached()
def index_view():
	return render_template('index.html')

@app.route('/teams')
@cache.cached()
def teams_view():
	session = getSession()
	
	# get list of global scores for header row
	all_score_types = session.query(ScoreType).filter_by(tournament_id=None, hidden=False).order_by(ScoreType.id).all()
	all_score_data = []
	for score_type in all_score_types:
		all_score_data.append({"name":jinja2.Markup(score_type.long_name), "desc":score_type.description})
	
	# get all global teams from DB
	all_teams = session.query(Team).all()
	all_team_data = []
	for team in all_teams:
		# general team info
		team_info = {'name':team.name, 'country_code':team.country_code}
		# get all score ratings
		all_scores = session.query(Score).filter_by(team_id=team.id, tournament_id=None).order_by(Score.type_id).all()
		assert len(all_scores) == len(all_score_types)
		team_score_data = []
		for score in all_scores:
			team_score_data.append(score.value)
		team_info['scores'] = team_score_data
		# add team to output
		all_team_data.append(team_info)
	
	Session.remove()
	return render_template('teams.html', scores=all_score_data, teams=all_team_data)

@app.route("/tournaments")
def tournaments_view():
	session = getSession()
	# this shows the tournaments for one user identified by their user ID!
	user_id = user_session["user_id"] if "user_id" in user_session else None
	user = session.query(User).filter_by(id=user_id).first() if user_id else None
	all_tournaments_data = []
	if user:
		# get all tournaments including their states
		for association in user.tournaments:
			tournament = association.tournament
			all_tournaments_data.append({
				"name": tournament.tournament_type.name + " #" + str(tournament.id),
				"state": tournament.getStateName(),
				"id": tournament.id,
				"rules": tournament.rule_weight_json
				})
			
	Session.remove()
	return render_template('tournaments.html', tournaments=all_tournaments_data)

@app.route("/tournament/<int:id>")
def tournament_view(id):
	session = getSession()
	
	tournament = session.query(Tournament).filter_by(id=id).first()
	if not tournament:
		Session.remove()
		abort(404)
	if tournament.state == TournamentState.running:
		return "Tournament still running.."
	elif tournament.state == TournamentState.pending:
		return "Tournament not yet started.."
	elif tournament.state == TournamentState.error:
		all_errors = session.query(TournamentExecutionError).filter_by(tournament_id=id).all()
		Session.remove()
		return render_template('tournament_errors.html', errors=all_errors)
		
	all_teams = Team.getAllTeamsForTournament(tournament.id)
	all_result_place_types = session.query(ResultPlaceType).filter_by(tournament_id=tournament.id).order_by(ResultPlaceType.place).all()
	
	colors = ['#dddd00', '#eeeeee', '#ee9900', '#a4a4ff', '#cccccc', '#bbbbbb']
	color_count = len(colors)
	max_used_place = 0
	
	all_team_data = []
	for team in all_teams:
		team_data = {"name":team.name, "country_code":team.country_code}
		results = []
		color_counter = 0
		percentage_count = 0
		distribution_sorting_value = 1
		for result_place_type in all_result_place_types:
			result_place = session.query(ResultPlace).filter_by(tournament_id=tournament.id, team_id=team.id, place=result_place_type.place).first()
			percentage = int(100 * result_place.percentage + 0.5)
			distribution_sorting_value = distribution_sorting_value * 100 + percentage
			percentage_count += percentage
			results.append({
				"name":result_place_type.name, 
				"percentage":percentage,
				"color":(colors[color_counter % color_count]),
				"place":result_place_type.place
				})
			color_counter += 1
		# add rounding errors to the percentage of the last place (usually "draw" or "rest")..
		if percentage_count != 100 and results:
			results[-1]["percentage"] += 100 - percentage_count
		team_data["results"] = results
		team_data["distribution_sorting_value"] = distribution_sorting_value
		
		team_data["general"] = session.query(Result).filter_by(tournament_id=tournament.id, team_id=team.id).first()
		all_team_data.append(team_data)
	
	# now allow for custom rendering
	general = {
		"colors": colors[:len(all_result_place_types)],
		"result_names": [x.name for x in all_result_place_types],
		"run_count": tournament.run_count
		}
	
	custom_view_function = tournament.tournament_type.custom_view_function
	Session.remove()
	

	if custom_view_function:
		return getattr(sys.modules[__name__], custom_view_function)(id, all_teams, all_result_place_types, all_team_data, general)
	return render_template('tournament.html', teams=all_team_data, general=general)
	
@app.route('/create')
@cache.cached()
def new_tournament_view():
	session = getSession()
	all_tournament_types = session.query(TournamentType).all()
	Session.remove()
	return render_template('create.html', types=all_tournament_types, run_count=config.simulation_run_count)

@app.route('/create_simple')
@cache.cached()
def simple_new_tournament_view():
	session = getSession();
	tournament_type = Session.query(TournamentType).filter_by(internal_identifier="worldcup").first()
	all_standard_rule_types = Session.query(RuleType).filter_by(is_default_rule=True).all()
	all_teams = Session.query(Team).limit(tournament_type.team_count).all()
	# special treatment for the "custom score" rule
	custom_score_info = {}
	for rule_type in all_standard_rule_types:
		if rule_type.name != "Custom":
			continue
		custom_score_info["score_type"] = rule_type.score_types[0].id
		custom_score_info["par_type"] = rule_type.parameter_types[0].id
		break
	
	Session.remove()
	return render_template('create_simple.html', tournament_type=tournament_type, rules=all_standard_rule_types, teams=all_teams, run_count=config.simulation_run_count, custom_score_rule=custom_score_info)

@app.route('/json/state/tournament:<int:id>')
def tournament_state_json(id):
	session = getSession()
	tournament = session.query(Tournament).filter_by(id=id).first()
	Session.remove();
	return json.dumps({"state":tournament.getStateName()})
	
@app.route('/json/rules/tournament:<int:id>')
def rules_json(id):
	session = getSession()
	all_rules = session.query(RuleType).all()
	rules = []
	for rule in all_rules:
		rules.append(rule.toDictionary())
	Session.remove()
	return json.dumps({'rules':rules})

@app.route('/json/teams', methods=['POST'])
def teams_json():
	session = getSession()
	info = json.loads(request.form["info"])
	# we also return the maximum amount of players for the correct table layout
	tournament = session.query(TournamentType).filter_by(id=info["tournament"]).first()
	# we need to get all existing teams and for every team all the scores that are needed for the rules
	all_team_data = {'teams':[], 'team_count':tournament.team_count}
	all_score_data = {}
	
	# collect all score types for the active rules
	for rule in info["rules"]:
		rule_type = session.query(RuleType).filter_by(id=rule).first()
		for score_type in rule_type.score_types:
			all_score_data[str(score_type.id)] = {"name":score_type.name, "desc":score_type.description}
		
	# now the teams
	all_teams = session.query(Team).all()
	for team in all_teams:
		team_data = {'id':team.id, 'name':team.name, 'country_code':team.country_code, 'scores': {}}
		
		# for every passed rule-type-ID fetch the fitting scores for this team
		for rule in info["rules"]:
			team_scores = session.query(Score).filter_by(team_id=team.id, tournament_id=None, type_id=rule).all()
			for score in team_scores:
				team_data["scores"][str(score.type_id)] = score.value;
		all_team_data["teams"].append(team_data)
	all_team_data["scores"] = all_score_data;
	Session.remove()
	# print all_team_data
	return json.dumps(all_team_data)
	
@app.route('/json/register_tournament', methods=['POST'])
def register_tournament_json():
	session = getSession()
	
	info = json.loads(request.form["info"])
	hash_code = hash(repr(info))
	
	return_value = {"status":"OK", "message":"Your tournament has been created!"}
	def abort(message):
		return_value["status"] = "FAIL"
		return_value["message"] = message
		return json.dumps(return_value)
		
	all_rules = []
	all_teams = []
	all_custom_scores = [] # {team_id, score_type_id, score}
	all_rule_parameters = [] # {par_type_id, value}
	
	try:
		# check valid tournament type
		tournament_type = session.query(TournamentType).filter_by(id=int(info["tournament_type"])).first()
		if not tournament_type:
			raise Exception("No valid tournament type selected.")
		# check all teams
		for team_data in info["teams"]:
			team = session.query(Team).filter_by(id=int(team_data["id"])).first()
			if not team:
				raise Exception("Invalid team selected (ID " + str(team_data["id"]) + ").")
			if team in all_teams:
				raise Exception("Selected team twice.")
			all_teams.append(team)
			
			# now go through customized ratings and add them iff they differ from the default rating
			for custom_rating in team_data["ratings"]:
				score_type_id = int(custom_rating)
				custom_score = float(team_data["ratings"][custom_rating])
				
				default_score = Session.query(Score).filter_by(tournament_id=None, team_id=team.id, type_id=score_type_id).first()
				if default_score and default_score.value == custom_score:
					continue
				else:
					all_custom_scores.append({"team_id": team.id, "score_type_id":score_type_id, "score":custom_score})
			
		# every tournament type has an obligatory team count
		if len(all_teams) != tournament_type.team_count:
			return abort("Selected an invalid amount of teams.")
		# and every tournament needs active rules
		needed_rule_parameters = []
		for rule_data in info["rules"]:
			rule = session.query(RuleType).filter_by(id=int(rule_data["id"])).first()
			if not rule:
				abort("Invalid rule selected.")
			for (old_rule, old_weight) in all_rules:
				if old_rule == rule:
					raise Exception("Selected rule twice.")
			rule_weight = float(rule_data["weight"])
			if rule_weight < 0.0:
				# the only possibility to reach this code-point is when the user tampered with the POST data..
				raise Exception("Rules with negative weight not allowed.")
			if rule_weight == 0.0:
				continue
			all_rules.append((rule, rule_weight)) # add as tuple
			# and require parameters for that rule
			for parameter_type in rule.parameter_types:
				needed_rule_parameters.append(parameter_type)
		if len(all_rules) == 0:
			raise Exception("You need to have active rules.")
		
		# the rules can have custom parameters
		for parameter in info["rule_parameters"]:
			par_id = int(parameter)
			par_value = float(info["rule_parameters"][parameter])
			
			# only remember if required
			for i in range(len(needed_rule_parameters)):
				parameter = needed_rule_parameters[i]
				if not parameter or parameter.id != par_id:
					continue
				all_rule_parameters.append({"par_type_id": par_id, "value":par_value})
				needed_rule_parameters[i] = None
				break
		
	except ValueError:
		Session.remove()
		return abort("Type check failed.")
	except Exception as e:
		Session.remove()
		return abort(str(e))
	
	# all checks passed
	# firstly, get the user ID from the browser session or generate a new one that is not in use yet
	user_id = user_session["user_id"] if "user_id" in user_session else None
	user = session.query(User).filter_by(id=user_id).first() if user_id else None
	user_existed = False
	if not user:
		user = User()
		session.add(user)
		session.commit()
	
		user_session["user_id"] = user.id
		user_session.permanent = True
	else:
		user_existed = True
	# we can now check whether a tournament with the exact same parameters has already been simulated.
	# instead of running the simulation another time, we can simply present that tournament to the user.
	existing_tournament = session.query(Tournament).filter_by(hash=hash_code).filter(Tournament.state!=TournamentState.error).first()
		
	# we can now create a new tournament execution request
	tournament = existing_tournament or Tournament(tournament_type.id, hash_code, config.simulation_run_count)
	
	# check if the user already did the simulation before
	# if so, move it to the end of the My Tournaments list by adjusting the timestamp
	existing_association = None
	if user_existed and existing_tournament:
		existing_association = session.query(UserTournamentMapping).filter_by(user_id=user.id, tournament_id=tournament.id).first()
		if existing_association:
			existing_association.timestamp = datetime.utcnow()
	# otherwise, add it to the user's tournaments	
	if not existing_association: 
		session.add(UserTournamentMapping(user, tournament))
	
	if not existing_tournament:
		session.add(tournament)
		# commit so that we have a correct ID
		session.commit()
		
		# make the teams join the tournament
		for i in range(0, len(all_teams)):
			team = all_teams[i]
			participation = Participation(tournament.id, team.id, i + 1)
			session.add(participation)
		
		# set the user-defined ratings for the tournament
		for custom_score in all_custom_scores:
			score = Score(custom_score["score_type_id"], custom_score["team_id"], custom_score["score"], tournament.id)
			session.add(score)
		
		# active rule setup
		rule_quick_lookup = {}
		for (rule_type, weight) in all_rules:
			rule = Rule(tournament.id, rule_type.id, weight)
			session.add(rule)
			# optimization for the tournament list
			rule_quick_lookup[rule_type.name] = weight
		# and add parameters to the rules if necessary
		for rule_parameter in all_rule_parameters:
			par = RuleParameter(tournament.id, rule_parameter["par_type_id"], rule_parameter["value"])
			session.add(par)
		# save rule setup quick-access for tournaments list
		tournament.rule_weight_json = json.dumps(rule_quick_lookup)
		# tournament is go
		session.commit()
		simulation_dispatcher.checkDispatchment()
	else:
		# commit the new user-tournament relationship
		session.commit()
	return_value["tournament_id"] = tournament.id
	Session.remove()
	return json.dumps(return_value)

# custom view function for FIFA style tournament
def worldcup_view(tournament_id, all_teams, all_result_place_types, all_team_data, general):
	# get match data for this tournament
	session = getSession()
	run_count = general["run_count"]
	# get all matches from that tournament
	match_dict = {}
	all_brackets = [16, 1, 2, 4, 8]
	for bracket in all_brackets:
		number_of_games = bracket
		use_round_robin_scores = False
		if bracket == 16:
			number_of_games = 8
			use_round_robin_scores = True
		for game_in_round in range(1, number_of_games+1):
			team_list = []
			for result in session.query(BracketTeamResult)\
				.filter(BracketTeamResult.tournament_id==tournament_id, BracketTeamResult.bof_round==bracket, BracketTeamResult.game_in_round==game_in_round)\
				.order_by(BracketTeamResult.wins.desc()):
				if result.matches > 0:
					chance = (
						(result.wins if not use_round_robin_scores else (3.0 * result.wins + 1.0 * result.draws))
						/ float(run_count))
					if chance >= 0.005:
						team_list.append({
							"team": result.team_id,
							"chance" : chance
							});

			match_dict["game_" + str(bracket) + "_" + str(game_in_round)] = team_list
	
	Session.remove()
	
	# create a quick lookup table for team names
	team_lookup = {}
	for team in all_teams:
		team_lookup[team.id] = {"name": team.name, "country_code":team.country_code}
	
	return render_template('tournament_fifa.html', teams=all_team_data, matches=json.dumps(match_dict), team_lookup=json.dumps(team_lookup), general=general)
	
if __name__ == '__main__':
	# "threaded=True" to fix an error with the IE9..
	app.run(host=config.flask_host, port=config.flask_port, threaded=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_Session.remove()