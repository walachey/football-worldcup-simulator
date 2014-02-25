import sys

# local includes
from configuration import main_configuration as config
from database_models import *
import dispatcher

# third-party includes
from flask import abort, redirect, url_for, render_template, flash, request, session, make_response, Response
from flask import Flask
import re, md5
import subprocess
import json

import smtplib
from email.mime.text import MIMEText
import socket # for catching socket.error

app = config.getFlaskApp()
simulation_dispatcher = dispatcher.Dispatcher(db, config)

@app.route('/')
def index_view():
	return render_template('index.html')

@app.route('/teams')
def teams_view():
	session = getSession()
	
	# get list of global scores for header row
	all_score_types = session.query(ScoreType).filter_by(tournament_id=None).order_by(ScoreType.id).all()
	all_score_data = []
	for score_type in all_score_types:
		all_score_data.append(score_type.name)
	
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
	
	# get all tournaments including their states
	all_tournaments = session.query(Tournament).all()
	all_tournaments_data = []
	for tournament in all_tournaments:
		all_tournaments_data.append({
			"name": tournament.tournament_type.name + " #" + str(tournament.id),
			"state": tournament.getStateName(),
			"id": tournament.id
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
	all_teams = Team.getAllTeamsForTournament(tournament.id)
	all_result_place_types = session.query(ResultPlaceType).filter_by(tournament_id=tournament.id).order_by(ResultPlaceType.place).all()
	
	colors = ['#dddd00', '#eeeeee', '#ee9900', '#000099', '#00eeee', '#ff0000']
	color_count = len(colors)
	
	all_team_data = []
	for team in all_teams:
		team_data = {"name":team.name, "country_code":team.country_code}
		results = []
		color_counter = 0
		for result_place_type in all_result_place_types:
			result_place = session.query(ResultPlace).filter_by(tournament_id=tournament.id, team_id=team.id, place=result_place_type.place).first()
			results.append({
				"name":result_place_type.name, 
				"percentage":int(100 * result_place.percentage),
				"color":(colors[color_counter % color_count])
				})
			color_counter += 1
		team_data["results"] = results
		
		team_data["general"] = session.query(Result).filter_by(tournament_id=tournament.id, team_id=team.id).first()
		all_team_data.append(team_data)
	
	custom_view_function = tournament.tournament_type.custom_view_function
	Session.remove()
	
	# now allow for custom rendering
	if custom_view_function:
		return getattr(sys.modules[__name__], custom_view_function)(tournament, all_teams, all_result_place_types, all_team_data)
	return render_template('tournament.html', teams=all_team_data)
	
@app.route('/create')	
def new_tournament_view():
	session = getSession()
	all_tournament_types = session.query(TournamentType).all()
	Session.remove()
	return render_template('create.html', types=all_tournament_types)

@app.route('/create_simple')	
def simple_new_tournament_view():
	session = getSession();
	tournament_type = Session.query(TournamentType).filter_by(internal_identifier="worldcup").first()
	all_standard_rule_types = Session.query(RuleType).filter_by(is_default_rule=True).all()
	all_teams = Session.query(Team).limit(tournament_type.team_count).all()
	Session.remove()
	return render_template('create_simple.html', tournament_type=tournament_type, rules=all_standard_rule_types, teams=all_teams)
	
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
	print "INFO____________________________________"
	print info
	print "HASH____________________________________\t" + str(hash_code)
	
	return_value = {"status":"OK", "message":"Your tournament has been created!"}
	def abort(message):
		return_value["status"] = "FAIL"
		return_value["message"] = message
		print message
		return json.dumps(return_value)
		
	all_rules = []
	all_teams = []
	
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
			all_rules.append((rule, float(rule_data["weight"])))
		if len(all_rules) == 0:
			raise Exception("You need to have active rules.")
		
	except ValueError:
		Session.remove()
		return abort("Type check failed.")
	except Exception as e:
		Session.remove()
		return abort(str(e))
	
	# all checks passed
	# we can now create a new tournament execution request
	tournament = Tournament(tournament_type.id, hash_code)
	session.add(tournament)
	# commit so that we have a correct ID
	session.commit()
	print "new tournament of id " + str(tournament.id)
	return_value["tournament_id"] = tournament.id
	# make the teams join the tournament
	for i in range(0, len(all_teams)):
		team = all_teams[i]
		participation = Participation(tournament.id, team.id, i + 1)
		session.add(participation)
	# active rule setup
	for (rule_type, weight) in all_rules:
		rule = Rule(tournament.id, rule_type.id, weight)
		session.add(rule)
	
	# tournament is go
	session.commit()
	simulation_dispatcher.checkDispatchment()
	
	Session.remove()
	return json.dumps(return_value)

# custom view function for FIFA style tournament
def worldcup_view(tournament, all_teams, all_result_place_types, all_team_data):
	return render_template('tournament_fifa.html', teams=all_team_data)
	
if __name__ == '__main__':
	# "threaded=True" to fix an error with the IE9..
	app.run(host=config.flask_host, port=config.flask_port, threaded=True)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_Session.remove()