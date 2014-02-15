from configuration import main_configuration as config

from flask import Flask
from flask import abort, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
import base64, random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.database_connection_string
db = SQLAlchemy(app)

nonURLChars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
URLCharTranslation = ''.join('-' for c in nonURLChars)
URLCharTranslationTable = string.maketrans(nonURLChars, URLCharTranslation)

class TournamentType(db.Model):
	__tablename__ = "tournament_types"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	icon = db.Column(db.String(128), unique=False)
	team_count = db.Column(db.Integer, unique=False)
	
	def __init__(self, name, description, team_count, icon):
		self.name = name
		self.description = description
		self.team_count = team_count
		self.icon = icon
	
	def __repr__(self):
		return "[Tournament " + name + "]"

class TournamentState:
	pending, running, finished = range(1, 4)

class Tournament(db.Model):
	__tablename__ = "tournaments"
	id = db.Column(db.Integer, primary_key=True)
	state = db.Column(db.SmallInteger, unique=False, default=TournamentState.pending)
	hash = db.Column(db.Integer)
	
	type_id = db.Column(db.Integer, db.ForeignKey('tournament_types.id'))
	tournament_type = db.relationship('TournamentType')
	
	def __init__(self, type_id, hash):
		self.type_id = type_id
		self.hash = hash
	
	def __repr__(self):
		return "[Play-Off " + str(self.id) + " - type " + str(self.type_id) + "]"

	def getStateName(self):
		if self.state == TournamentState.pending:
			return "pending"
		if self.state == TournamentState.running:
			return "running"
		if self.state == TournamentState.finished:
			return "finished"
		return "unknown"
		
class Team(db.Model):
	__tablename__ = "teams"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	country_code = db.Column(db.String(3), unique=False)
	
	def __init__(self, name, country_code):
		self.name = name
		self.country_code = country_code
	
	def __repr__(self):
		return "[Team " + self.name + " from " + self.country_code + "]"
	
	@staticmethod
	def getAllTeamsForTournament(tournament_id):
		all_teams = []
		for participation in Participation.query.filter_by(tournament_id=tournament_id):
			team = Team.query.filter_by(id=participation.team_id).first()
			all_teams.append(team)
			
		return all_teams

class Participation(db.Model):
	__tablename__ = "participations"
	id = db.Column(db.Integer, primary_key=True)
	order = db.Column(db.Integer, unique=False)
	
	#tournament = db.relationship('Tournament', backref=db.backref('participations', lazy='dynamic'))
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	#team = db.relationship('Team', backref=db.backref('participations', lazy='dynamic'))
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	
	def __init__(self, tournament_id, team_id, order):
		self.tournament_id = tournament_id
		self.team_id = team_id
		self.order = order
		
	def __repr__(self):
		return "[Participation of " + str(self.team_id) + " in play-off " + str(self.tournament_id) + "]"

rule_score_table = db.Table("rule2scores", db.metadata,
	db.Column("rule_type_id", db.Integer, db.ForeignKey("rule_types.id")),
	db.Column("score_type_id", db.Integer, db.ForeignKey("score_types.id"))
	)
		
class RuleType(db.Model):
	__tablename__ = "rule_types"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	score_types = db.relationship("ScoreType", secondary=rule_score_table)
	
	def __init__(self, name, description):
		self.name = name
		self.description = description
	
	def __repr__(self):
		return "[Rule " + self.name + "]"
	
	def toDictionary(self):
		return {'id':self.id, 'name':self.name, 'desc':self.description}

class Rule(db.Model):
	__tablename__ = "rules"
	id = db.Column(db.Integer, primary_key=True)
	type_id = db.Column(db.Integer, db.ForeignKey('rule_types.id'))
	weight = db.Column(db.Float, unique=False)
	
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
		
	def __init__(self, tournament_id, type_id, weight):
		self.tournament_id = tournament_id
		self.type_id = type_id
		self.weight = weight
	
	def __repr__(self):
		return "[Rule " + str(self.type_id) + " set to " + str(self.weight) + "]"
	
class ScoreType(db.Model):
	__tablename__ = "score_types"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	
	# set if the score type was customized for a specific tournament
	#tournament = db.relationship('Tournament', backref=db.backref('score_types', lazy='dynamic'))
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	#parent = db.relationship('ScoreType', backref=db.backref('score_types', lazy='dynamic'))
	parent_id = db.Column(db.Integer, db.ForeignKey('score_types.id'))
	
	def __init__(self, name, description):
		self.name = name
		self.description = description
	
	def __repr__(self):
		return "[Score " + self.name + "]"

		
class Score(db.Model):
	__tablename__ = "scores"
	id = db.Column(db.Integer, primary_key=True)
	type_id = db.Column(db.Integer, db.ForeignKey('score_types.id'))
	value = db.Column(db.Float, unique=False)
	
	#tournament = db.relationship('Tournament', backref=db.backref('scores', lazy='dynamic'))
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	#team = db.relationship('Team', backref=db.backref('teams', lazy='dynamic'))
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	
	def __init__(self, type_id, team_id, value):
		self.type_id = type_id
		self.value = value
		self.team_id = team_id
	
	def __repr__(self):
		return "[Rating " + str(self.id) + " for play-off " + str(self.tournament_id) + " of team " + str(self.team_id) + "]"
	
	# returns the score value for a team
	# this can either the the global value or the tournament-specific one
	@staticmethod
	def getForTournament(type_id, tournament_id, team_id):
		local_score = Score.query.filter_by(type_id=type_id, tournament_id=tournament_id, team_id=team_id).first()
		if local_score:
			return local_score
		return Score.query.filter_by(type_id=type_id, team_id=team_id).first()



class ResultPlaceType(db.Model):
	__tablename__ = "result_place_types"
	id = db.Column(db.Integer, primary_key=True)
	place = db.Column(db.SmallInteger, unique=False)
	name = db.Column(db.String(64), unique=False)
	
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	
	def __init__(self, tournament_id, place, name):
		self.place = place
		self.name = name
		self.tournament_id = tournament_id
	
	def __repr__(self):
		return "[Place " + self.name + " tournament " + str(self.tournament_id) + "]"
	
class ResultPlace(db.Model):
	__tablename__ = "result_places"
	id = db.Column(db.Integer, primary_key=True)
	place = db.Column(db.SmallInteger, unique=False)
	percentage = db.Column(db.Float, unique=False)
	
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	
	def __init__(self, tournament_id, team_id, place, percentage):
		self.tournament_id = tournament_id
		self.team_id = team_id
		self.place = place
		self.percentage = percentage
	
	def __repr__(self):
		return "[Ranked team " + str(self.team_id) + " on " + str(self.place) + " ~" + str(self.percentage) + "]"