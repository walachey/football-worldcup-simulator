import sys
import random
from datetime import datetime
from os.path import abspath, dirname # to fix app.root_path issues when deploying via wsgi
import hashlib

# local includes
from configuration import main_configuration as config
from database_models import *
import admin_interface

# third-party includes
from flask import abort, redirect, url_for, render_template, flash, request, session as user_session, make_response, Response
from flask import Flask
from flask.ext.cache import Cache
from sqlalchemy import func
import jinja2
import re, md5
import subprocess
import json


import smtplib
from email.mime.text import MIMEText
import socket # for catching socket.error

app = config.getFlaskApp()
app.root_path = abspath(dirname(__file__)) # this fixes incorrect root-path deployment issues
cache = Cache(app, config={'CACHE_TYPE': 'simple'}) # "null" to disable caching, "simple" for default
admin_interface.init(app, cache)
simulation_dispatcher = config.dispatcher_class(db, config)
# initialize random numbers for user ID generation
random.seed()

# set some global config options that are used in the base template
@app.context_processor
def define_globals():
	return {
		"show_custom_tournament_page": config.show_custom_tournament_page,
		"google_analytics_code": config.google_analytics_code
	}

@app.route('/')
@cache.cached()
def index_view():
	session = getSession()
	all_team_data = []
	
	if config.show_progress_graphs:
		# get current odds
		date = session.query(func.max(OddsData.date)).filter_by(source="bets")
		teams = []
		# there is a set of default teams that are always displayed (even if out of tournament)
		for country_code in config.progress_graphs_force_teams:
			team = session.query(Team).filter_by(country_code=country_code).first()
			teams.append(team)
		# get X highest teams
		for odd in session.query(OddsData).filter_by(date=date, source="bets").order_by(OddsData.odds.desc()):
			if len(teams) >= 7 or odd.odds <= 0.001:
				break
			team = session.query(Team).filter_by(id=odd.team_id).first()
			if not (team in teams):
				teams.append(team)
		# and now just get all odds for those teams..
		all_team_data = []
		for team in teams:
			team_data = {"name":team.name}
			for odd in session.query(OddsData).filter_by(team_id=team.id).order_by(OddsData.date):
				if not odd.source in team_data:
					team_data[odd.source] = []
				team_data[odd.source].append(odd.odds)
			all_team_data.append(team_data)
		# and then sort all teams for last betting odds
		def betting_odds(team_data):
			return team_data["bets"][-1]
		all_team_data = sorted(all_team_data, key=betting_odds, reverse=True)
	
	# if the tournament is already over, the index page will display the tournament results
	# at this point, this is hardcoded (todo)
	rankings = []
	groups = []
	if config.show_tournament_results:
		rankings = ["DE", "AR", "NL", "BR"]
		groups = [
				["BR", "MX"],
				["NL", "CL"],
				["CO", "GR"],
				["CR", "UY"],
				["FR", "CH"],
				["AR", "NG"],
				["DE", "US"],
				["BE", "DZ"]
				]
		for i in range(len(rankings)):
			team = session.query(Team).filter_by(country_code=rankings[i]).first()
			rankings[i] = {"name": team.name, "country_code": team.country_code}
		for group in groups:
			for i in range(len(group)):
				team = session.query(Team).filter_by(country_code=group[i]).first()
				group[i] = {"name": team.name, "country_code": team.country_code}
	
	cleanupSession()
	return render_template('index.html', run_count_max=config.simulation_max_run_count, team_data_json=json.dumps(all_team_data), show_tournament_results=config.show_tournament_results, tournament_results=json.dumps({"rankings": rankings, "groups": groups}))

@app.route('/impressum')
@cache.cached()
def impressum_view():
	return render_template('impressum.html')

@app.route('/technical_details')
@cache.cached()
def technical_details_view():
	return render_template('technical_details.html')

@app.route('/documentation')
@cache.cached()
def documentation_view():
	return render_template('documentation.html')

@app.route('/matchtable')
@cache.cached()
def matchtable_view():	
	session = getSession()
	all_database_matches = session.query(DatabaseMatchResult).order_by(DatabaseMatchResult.bof_round, DatabaseMatchResult.id.desc()).all()
	
	database_matches = []
	for db_match in all_database_matches:
		team1 = session.query(Team).filter_by(id=db_match.team_left_id).first()
		team2 = session.query(Team).filter_by(id=db_match.team_right_id).first()
		name = "Group Phase"
		if db_match.bof_round == 8:
			name = "Round Of Sixteen"
		elif db_match.bof_round == 4:
			name = "Quarter Finals"
		elif db_match.bof_round == 2:
			name = "Semi Finals"
		elif db_match.bof_round == 1:
			name = "Finals &amp; Third"
			
		db_match_data = {
			"name": name,
			"bof_round": db_match.bof_round,
			"teams": [
					{"name": team1.name, "CC": team1.country_code, "goals": db_match.goals_left},
					{"name": team2.name, "CC": team2.country_code, "goals": db_match.goals_right}
				]
		}
		database_matches.append(db_match_data)
	cleanupSession()
	return render_template('matchtable.html', matches=database_matches)
	
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
	
	cleanupSession()
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
			tournament_type = session.query(TournamentType).filter_by(id=tournament.type_id).first()
			all_tournaments_data.append({
				"name": tournament_type.name,
				"state": tournament.getStateName(),
				"id": tournament.id,
				"rules": tournament.rule_weight_json,
				"run_count": tournament.run_count,
				"time": int((association.timestamp - datetime(1970, 1, 1)).total_seconds())
				})
			
	cleanupSession()
	return render_template('tournaments.html', tournaments=all_tournaments_data)

@app.route("/tournament/<int:id>")
def tournament_view(id):
	session = getSession()
	
	tournament = session.query(Tournament).filter_by(id=id).first()
	if not tournament:
		cleanupSession()
		abort(404)
	if tournament.state == TournamentState.running or tournament.state == TournamentState.pending:
		cleanupSession()
		return render_template('tournament_running.html')
	elif tournament.state == TournamentState.error:
		all_errors = session.query(TournamentExecutionError).filter_by(tournament_id=id).all()
		cleanupSession()
		return render_template('tournament_errors.html', errors=all_errors)
		
	all_teams = Team.getAllTeamsForTournament(tournament.id, session)
	all_result_place_types = session.query(ResultPlaceType).filter_by(tournament_id=tournament.id).order_by(ResultPlaceType.place).all()
	unique_different_outcomes = len(all_result_place_types)
	# Prepare a few different colors for different possibilities (which mostly make the last rank always grey).
	colors = ['#dddd00', '#eeeeee', '#ee9900', '#a4a4ff', '#cccccc', '#bbbbbb']
	if unique_different_outcomes == 4:
		colors = ['#dddd00', '#eeeeee', '#ee9900', '#cccccc']
	elif unique_different_outcomes == 3:
		colors = ['#dddd00', '#eeeeee', '#cccccc']
	
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
	
	tournament_type = session.query(TournamentType).filter_by(id=tournament.type_id).first()
	custom_view_function = tournament_type.custom_view_function
	cleanupSession()
	

	if custom_view_function:
		return getattr(sys.modules[__name__], custom_view_function)(id, all_teams, all_result_place_types, all_team_data, general)
	return render_template('tournament.html', teams=all_team_data, general=general)
	
@app.route('/create')
@cache.cached()
def new_tournament_view():
	session = getSession()
	all_tournament_types = session.query(TournamentType).all()
	run_count_par = session.query(RuleParameterType).filter_by(internal_identifier="simulation_run_count").first()
	use_match_db_par = session.query(RuleParameterType).filter_by(internal_identifier="use_match_database").first()
	cleanupSession()
	return render_template('create.html', types=all_tournament_types, run_count_max=config.simulation_max_run_count, run_count_par=run_count_par, use_match_db_par=use_match_db_par)

@app.route('/create_simple')
@cache.cached()
def simple_new_tournament_view():
	session = getSession();
	tournament_type = session.query(TournamentType).filter_by(internal_identifier="eurocup").first()
	all_standard_rule_types = session.query(RuleType).filter_by(is_default_rule=True).all()
	all_teams = session.query(Team).limit(tournament_type.team_count).all()
	run_count_par = session.query(RuleParameterType).filter_by(internal_identifier="simulation_run_count").first()
	use_match_db_par = session.query(RuleParameterType).filter_by(internal_identifier="use_match_database").first()
	# special treatment for the "custom score" rule
	custom_score_info = {}
	for rule_type in all_standard_rule_types:
		if rule_type.name != "Custom":
			continue
		custom_score_info["score_type"] = rule_type.getScoreTypes(session)[0].id
		custom_score_info["par_type"] = rule_type.getParameterTypes(session)[0].id
		break
	
	cleanupSession()
	return render_template('create_simple.html', tournament_type=tournament_type, rules=all_standard_rule_types, teams=all_teams, run_count_max=config.simulation_max_run_count, custom_score_rule=custom_score_info, run_count_par=run_count_par, use_match_db_par=use_match_db_par)

@app.route('/json/state/tournament:<int:id>')
def tournament_state_json(id):
	session = getSession()
	tournament = session.query(Tournament).filter_by(id=id).first()
	cleanupSession()
	if not tournament:
		abort(404)
		
	state_info = json.dumps({"state":tournament.getStateName()})
	return state_info
	
@app.route('/json/rules/tournament:<int:id>')
def rules_json(id):
	session = getSession()
	all_rules = session.query(RuleType).all()
	rules = []
	for rule in all_rules:
		rules.append(rule.toDictionary())
	cleanupSession()
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
		for score_type in rule_type.getScoreTypes(session):
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
	cleanupSession()
	# print all_team_data
	return json.dumps(all_team_data)
	
@app.route('/json/register_tournament', methods=['POST'])
def register_tournament_json():
	# some preparations
	session = getSession()

	return_value = {"status":"OK", "message":"Your tournament has been created!"}
	def abort(message):
		cleanupSession()
		return_value["status"] = "FAIL"
		return_value["message"] = message
		return json.dumps(return_value)
		
	all_rules = []
	all_teams = []
	all_custom_scores = [] # {team_id, score_type_id, score}
	all_simulation_parameters = [] # {par_type_id, value}, contains both rule and global simulation parameters
	needed_simulation_parameters = [] # the parameter types that are needed by the tournament
	tournament_run_count = None # shortcut for the parameter value
	
	# get request string from parameters and create a hash
	# only one tournament per hash will ever be simulated
	json_request_string = request.form["info"]
	hash_code = hashlib.md5(json_request_string).hexdigest()

	# We can now check whether a tournament with the exact same parameters has already been simulated.
	# Instead of running the simulation another time, we can simply present that tournament to the user.
	existing_tournament = session.query(Tournament).filter_by(hash=hash_code).filter(Tournament.state!=TournamentState.error, Tournament.run_count > 10).first()
	
	
	# if no existing tournament was found, we actually have to parse the parameters
	if not existing_tournament:
		try:
			info = json.loads(json_request_string)
			
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
					
					default_score = session.query(Score).filter_by(tournament_id=None, team_id=team.id, type_id=score_type_id).first()
					if default_score and default_score.value == custom_score:
						continue
					else:
						all_custom_scores.append({"team_id": team.id, "score_type_id":score_type_id, "score":custom_score})
				
			# every tournament type has an obligatory team count
			if len(all_teams) != tournament_type.team_count:
				return abort("Selected an invalid amount of teams.")
			# and every tournament needs active rules
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
				for parameter_type in rule.getParameterTypes(session):
					needed_simulation_parameters.append(parameter_type)
			if len(all_rules) == 0:
				raise Exception("You need to have active rules.")
			
			# the tournament always needs a few parameters
			# run count parameter
			simulation_run_count_parameter = session.query(RuleParameterType).filter_by(internal_identifier="simulation_run_count").first()
			needed_simulation_parameters.append(simulation_run_count_parameter)
			# match database usage parameter
			match_database_parameter = session.query(RuleParameterType).filter_by(internal_identifier="use_match_database").first()
			needed_simulation_parameters.append(match_database_parameter)
			
			# the rules can have custom parameters
			for parameter in info["rule_parameters"]:
				par_id = int(parameter)
				par_value = float(info["rule_parameters"][parameter])
				
				# only remember if required
				for i in range(len(needed_simulation_parameters)):
					parameter = needed_simulation_parameters[i]
					if not parameter or parameter.id != par_id:
						continue
					all_simulation_parameters.append({"par_type_id": par_id, "value":par_value})
					needed_simulation_parameters[i] = None
					
					# safety checks
					# run count
					if parameter == simulation_run_count_parameter:
						number_of_runs = int(par_value)
						if number_of_runs <= 0 or number_of_runs > config.simulation_max_run_count:
							raise Exception("Number of runs must be between 1 and " + str(config.simulation_max_run_count) + ".")
							
						tournament_run_count = number_of_runs
					break
			
		except ValueError:
			return abort("Type check failed.")
		except Exception as e:
			return abort(repr(e))
	
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
		
	# we can now create a new tournament execution request
	tournament = existing_tournament or Tournament(tournament_type.id, hash_code, tournament_run_count)
	
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
	
	tournament_id = None
	if not existing_tournament:
		session.add(tournament)
		# commit so that we have a correct ID
		session.commit()
		tournament_id = tournament.id
		
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
		for rule_parameter in all_simulation_parameters:
			par = RuleParameter(tournament.id, rule_parameter["par_type_id"], rule_parameter["value"])
			session.add(par)
		# save rule setup quick-access for tournaments list
		tournament.rule_weight_json = json.dumps(rule_quick_lookup)
		# tournament is go
		session.commit()

		simulation_dispatcher.dispatchTournament(tournament_id, session)
	else:
		# commit the new user-tournament relationship
		session.commit()
		tournament_id = tournament.id
	cleanupSession()
		
	# note that the original "tournament" object is not valid anymore since the session has been removed
	return_value["tournament_id"] = tournament_id
	
	return json.dumps(return_value)

# custom view function for UEFA Euro 2016 style tournament
def eurocup_view(tournament_id, all_teams, all_result_place_types, all_team_data, general):
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
					if chance >= 0.005 or bracket == 16:
						team_list.append({
							"team": result.team_id,
							"chance" : chance,
							"avg_rank": result.average_group_rank
							});
			
			# In a round robin tournament, we don't want to sort by absolute wins (and can't use the score either).
			# Instead we sort for the average rank in the group.
			if use_round_robin_scores:
				team_list = sorted(team_list, key=lambda x: x["avg_rank"])
			match_dict["game_" + str(bracket) + "_" + str(game_in_round)] = team_list
	
	cleanupSession()
	
	# create a quick lookup table for team names
	team_lookup = {}
	for team in all_teams:
		team_lookup[team.id] = {"name": team.name, "country_code":team.country_code}
	
	return render_template('tournament_euro.html', teams=all_team_data, matches=json.dumps(match_dict), team_lookup=json.dumps(team_lookup), general=general)

	
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
					if chance >= 0.005 or bracket == 16:
						team_list.append({
							"team": result.team_id,
							"chance" : chance
							});
			
			# sort for chance, does not necessarily have to be sorted already
			# this only happens in the group phase, though, where the number of wins is not the only factor
			if use_round_robin_scores:
				def get_chance(team_data):
					return team_data["chance"]
				team_list = sorted(team_list, key=get_chance, reverse=True)
				# also it is possible that two teams finish with the exact same amount of goals.
				# in that case, it is necessary to have a second sorting criteria - for example the success in the next round.
				# (as the goal difference is currently not available here)
				have_two_of_equal_points = False
				for i in range(1, len(team_list)):
					if team_list[i-1]["chance"] == team_list[i]["chance"]:
						have_two_of_equal_points = True
						break
				if have_two_of_equal_points:
					# get all victories in next round for participating teams
					for team_data in team_list:
						next_result = session.query(BracketTeamResult).filter_by(tournament_id=tournament_id, team_id=team_data["team"], bof_round=bracket/2).first()
						team_data["next_wins"] = next_result.wins
					# and sort again, for victories in next round
					def better_round_robin_sorting_criteria(team_data):
						return (team_data["chance"], team_data["next_wins"])
					team_list = sorted(team_list, key=better_round_robin_sorting_criteria, reverse=True)
			match_dict["game_" + str(bracket) + "_" + str(game_in_round)] = team_list
	
	cleanupSession()
	
	# create a quick lookup table for team names
	team_lookup = {}
	for team in all_teams:
		team_lookup[team.id] = {"name": team.name, "country_code":team.country_code}
	
	return render_template('tournament_fifa.html', teams=all_team_data, matches=json.dumps(match_dict), team_lookup=json.dumps(team_lookup), general=general)

# this apparently needs to be before the app.run() call to work correctly
@app.teardown_request
def teardown_request(exception):
	cleanupSession()
	
if __name__ == '__main__':
	# "threaded=True" to fix an error with the IE9 in local deployment mode..
	# the IE9 might hang the whole application that way. There is a fix available, but not in the released packages.
	app.run(host=config.flask_host, port=config.flask_port, threaded=True)

	
