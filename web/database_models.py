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
db.engine.echo = config.echo_sql

from sqlalchemy.orm import scoped_session, sessionmaker
Session = scoped_session( sessionmaker() )
Session.configure(bind=db.engine)
def getSession():
	session = Session()
	session._model_changes = {}
	return session

nonURLChars = ''.join(c for c in map(chr, range(256)) if not c.isalnum())
URLCharTranslation = ''.join('-' for c in nonURLChars)
URLCharTranslationTable = string.maketrans(nonURLChars, URLCharTranslation)

class TournamentType(db.Model):
	__tablename__ = "tournament_types"
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	icon = db.Column(db.String(128), unique=False)
	team_count = db.Column(db.Integer, unique=False)
	 # for communication with the simulator
	internal_identifier = db.Column(db.String(128), unique=False)
	# for rendering the results
	custom_view_function = db.Column(db.String(128), unique=False)
	
	def __init__(self, name, description, team_count, icon, internal_identifier, custom_view_function=None):
		self.name = name
		self.description = description
		self.team_count = team_count
		self.icon = icon
		self.internal_identifier = internal_identifier
		self.custom_view_function = custom_view_function
	
	def __repr__(self):
		return "[Tournament " + name + "]"

class TournamentState:
	pending, running, finished, error = range(1, 5)

class Tournament(db.Model):
	__tablename__ = "tournaments"
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	state = db.Column(db.SmallInteger, unique=False, default=TournamentState.pending)
	hash = db.Column(db.Integer)
	user_id = db.Column(db.Integer)
	
	type_id = db.Column(db.Integer, db.ForeignKey('tournament_types.id'))
	tournament_type = db.relationship('TournamentType')
	
	def __init__(self, type_id, hash, user_id):
		self.type_id = type_id
		self.hash = hash
		self.user_id = user_id
	
	def __repr__(self):
		return "[Play-Off " + str(self.id) + " - type " + str(self.type_id) + "]"

	def getStateName(self):
		if self.state == TournamentState.pending:
			return "pending"
		if self.state == TournamentState.running:
			return "running"
		if self.state == TournamentState.finished:
			return "finished"
		if self.state == TournamentState.error:
			return "error"
		return "unknown"
		
class Team(db.Model):
	__tablename__ = "teams"
	query = None
	
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
		session = getSession()
		all_teams = []
		for participation in session.query(Participation).filter_by(tournament_id=tournament_id):
			team = session.query(Team).filter_by(id=participation.team_id).first()
			all_teams.append(team)
			
		return all_teams

class Participation(db.Model):
	__tablename__ = "participations"
	query = None
	
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
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	score_types = db.relationship("ScoreType", secondary=rule_score_table)
	
	# for communication with the simulator
	internal_function_identifier = db.Column(db.String(128), unique=False)
	
	# standard rules that are displayed in the quick-creation dialog
	standard_weight = db.Column(db.Float, unique=False)
	is_default_rule = db.Column(db.Boolean, unique=False)
	
	def __init__(self, name, description, internal_function_identifier):
		self.name = name
		self.description = description
		self.internal_function_identifier = internal_function_identifier
		
		self.standard_weight = 0.0
		self.is_default_rule = False
	
	def makeDefaultRule(self, standard_weight):
		self.is_default_rule = True
		self.standard_weight = standard_weight
		
	def __repr__(self):
		return "[Rule " + self.name + "]"
	
	def toDictionary(self):
		return {'id':self.id, 'name':self.name, 'desc':self.description}

class Rule(db.Model):
	__tablename__ = "rules"
	query = None
	
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
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128), unique=False)
	long_name = db.Column(db.String(128), unique=False)
	description = db.Column(db.String(512), unique=False)
	
	# set if the score type was customized for a specific tournament
	#tournament = db.relationship('Tournament', backref=db.backref('score_types', lazy='dynamic'))
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	#parent = db.relationship('ScoreType', backref=db.backref('score_types', lazy='dynamic'))
	parent_id = db.Column(db.Integer, db.ForeignKey('score_types.id'))
	
	def __init__(self, name, description, long_name=None):
		self.name = name
		self.long_name = self.name
		self.description = description
		
		if long_name:
			self.long_name = long_name
	
	def __repr__(self):
		return "[Score " + self.name + "]"

		
class Score(db.Model):
	__tablename__ = "scores"
	query = None
	
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
		session = getSession()
		local_score = session.query(Score).filter_by(type_id=type_id, tournament_id=tournament_id, team_id=team_id).first()
		if local_score:
			return local_score
		return session.query(Score).filter_by(type_id=type_id, team_id=team_id).first()



class ResultPlaceType(db.Model):
	__tablename__ = "result_place_types"
	query = None
	
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
	query = None
	
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
		
class Result(db.Model):
	__tablename__ = "results"
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	
	average_goals = db.Column(db.Float, unique=False)
	average_place = db.Column(db.Float, unique=False)
	
	def __init__(self, tournament_id, team_id, average_goals, average_place):
		self.tournament_id = tournament_id
		self.team_id = team_id
		self.average_goals = average_goals
		self.average_place = average_place
		
	def __repr__(self):
		return "[Result " + str(self.id) + "]"
		
class MatchResult(db.Model):
	__tablename__ = "match_results"
	query = None
	
	id = db.Column(db.Integer, primary_key=True)
	tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'))
	team_left_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	team_right_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
	
	bof_round = db.Column(db.Integer, unique=False)
	game_in_round = db.Column(db.Integer, unique=False)
	
	average_goals_left = db.Column(db.Float, unique=False)
	average_goals_right = db.Column(db.Float, unique=False)
	number_of_games = db.Column(db.Integer, unique=False)
	
	# optimization, the most frequent result will always be shown first
	most_frequent = db.Column(db.Boolean, unique=False)
	
	def __init__(self, tournament_id, bof_round, game_in_round, teams, goals, number_of_games):
		self.tournament_id = tournament_id
		self.bof_round = bof_round
		self.game_in_round = game_in_round
		(self.team_left_id, self.team_right_id) = teams
		(self.average_goals_left, self.average_goals_right) = goals
		self.number_of_games = number_of_games
		self.most_frequent = False
		
		# and normalize
		if self.number_of_games != 0:
			(self.average_goals_left, self.average_goals_right) = (self.average_goals_left / float(self.number_of_games), self.average_goals_right / float(self.number_of_games))
	
	def getMatchName(self):
		return "game_" + str(self.bof_round) + "_" + str(self.game_in_round)
	
	def __repr__(self):
		return "[MatchResult " + self.match_name + " - " + self.team_left_id + " vs " + self.team_right_id + "]"
		
	def toDictionary(self):
		return {
			"teams": [self.team_left_id, self.team_right_id],
			"goals": [self.average_goals_left, self.average_goals_right]
		}
	
	# returns a list with all matches that lead to this match
	# usually, this method is called on a finals game and returns the complete brackets
	def resolveBrackets(self):
		session = getSession() # no need to clean up, since this will not create a duplicate object but just return the currently active one (which will be cleaned up by a parent function)
		
		resolved = [self]
		# best of 32? nothing more to resolve..
		if self.bof_round == 16:
			return resolved
		# get all (two) matches that lead to this match
		for team_id in [self.team_left_id, self.team_right_id]:
			parent_match = session.query(MatchResult)\
				.filter(MatchResult.tournament_id==self.tournament_id, MatchResult.bof_round==self.bof_round*2)\
				.filter((MatchResult.team_left_id==team_id) | (MatchResult.team_right_id==team_id))\
				.order_by(MatchResult.number_of_games.desc())\
				.first()
			for previous_match in parent_match.resolveBrackets():
				resolved.append(previous_match)
		return resolved