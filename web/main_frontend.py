# local includes
from configuration import main_configuration as config
from database_models import *

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

@app.route('/')
def index_view():
	return render_template('index.html')

@app.route('/teams')
def teams_view():
	# get list of global scores for header row
	all_score_types = ScoreType.query.filter_by(tournament_id=None).order_by(ScoreType.id).all()
	all_score_data = []
	for score_type in all_score_types:
		all_score_data.append(score_type.name)
	
	# get all global teams from DB
	all_teams = Team.query.all()
	all_team_data = []
	for team in all_teams:
		# general team info
		team_info = {'name':team.name, 'country_code':team.country_code}
		# get all score ratings
		all_scores = Score.query.filter_by(team_id=team.id, tournament_id=None).order_by(Score.type_id).all()
		assert len(all_scores) == len(all_score_types)
		team_score_data = []
		for score in all_scores:
			team_score_data.append(score.value)
		team_info['scores'] = team_score_data
		# add team to output
		all_team_data.append(team_info)
	
	return render_template('teams.html', scores=all_score_data, teams=all_team_data)

@app.route('/create')	
def new_tournament_view():
	all_tournament_types = TournamentType.query.all()
	return render_template('create.html', types=all_tournament_types)

@app.route('/json/rules/tournament:<int:id>')
def rules_json(id):
		all_rules = RuleType.query.all()
		rules = []
		for rule in all_rules:
			rules.append(rule.toDictionary())
		return json.dumps({'rules':rules})

@app.route('/json/teams', methods=['POST'])
def teams_json():
	info = json.loads(request.form["info"])
	print "INFO____________________________________"
	print info
	# we also return the maximum amount of players for the correct table layout
	tournament = TournamentType.query.filter_by(id=info["tournament"]).first()
	# we need to get all existing teams and for every team all the scores that are needed for the rules
	all_team_data = {'teams':[], 'team_count':tournament.team_count}
	all_score_data = {}
	
	# collect all score types for the active rules
	for rule in info["rules"]:
		rule_type = RuleType.query.filter_by(id=rule).first()
		for score_type in rule_type.score_types:
			all_score_data[str(score_type.id)] = {"name":score_type.name, "desc":score_type.description}
		
	# now the teams
	all_teams = Team.query.all()
	for team in all_teams:
		team_data = {'name':team.name, 'country_code':team.country_code, 'scores': {}}
		
		# for every passed rule-type-ID fetch the fitting scores for this team
		for rule in info["rules"]:
			team_scores = Score.query.filter_by(team_id=team.id, tournament_id=None, type_id=rule).all()
			for score in team_scores:
				team_data["scores"][str(score.type_id)] = score.value;
		all_team_data["teams"].append(team_data)
	all_team_data["scores"] = all_score_data;
	print all_team_data
	return json.dumps(all_team_data)
	
if __name__ == '__main__':
	app.run(host=config.flask_host, port=config.flask_port)
