from database_models import *
import threading
import subprocess
import json

class Dispatcher():
	db = None
	config = None
	
	def __init__(self, db, config):
		self.db = db
		self.config = config
		
	# looks for a pending tournament and starts a simulation if one is found
	def checkDispatchment(self):
		open_tournament = Tournament.query.filter_by(state=TournamentState.pending).with_lockmode("update").first()
		# no open jobs?
		if not open_tournament:
			return
		open_tournament.state = TournamentState.running
		self.db.session.commit()
		
		# from here on everything needs to be protected to reset tournaments in case of failures
		try:

			json_object = self.toDictForSimulationInput(open_tournament)
			dispatchment_thread = threading.Thread(target=self.dispatchJob, args=(json_object,))
			dispatchment_thread.start()
		except Exception as e:
			print "EXCEPTION: " + str(e)
			open_tournament.state = TournamentState.pending
			self.db.session.commit()
	
	# this should run in a different thread
	def dispatchJob(self, json_object):
		# construct command to start the simulation client
		command = self.config.getCompleteSimulationProgramPath()
		# the JSON input will the given via stdin
		json_string = json.dumps(json_object)
		print "TOURNAMENTING " + json_string
		# run and wait for termination
		process = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = process.communicate(json_string)
		
		print "PROGRAM TERMINATED WITH CODE " + str(process.returncode)
		print "STDERR ---------------------"
		print stderr
		print "STDOUT ---------------------"
		print stdout
		print "----------------------------"
		
		tournament = Tournament.query.filter_by(id=json_object["tournament_id"]).first()
		try:
			if process.returncode == 0:
				tournament.state = TournamentState.finished
				self.parseJSONResults(json.loads(stdout), tournament)
			else:
				tournament.state = TournamentState.pending
		except Exception as e:
			import traceback
			print "An error occurred: " + str(e)
			print traceback.format_exc()
			tournament.state = TournamentState.pending
		finally:
			self.db.session.commit()
	
	# creates a dictionary that can be used to create JSON from it and pass it to the simulation program
	def toDictForSimulationInput(self, tournament):
	
		# this is the root of the tree with all global config settings for the simulation
		dict = {
			"thread_count": self.config.simulation_thread_count,
			"tournament_id": tournament.id
			}
		
		# get all active rules for this tournament and calculate needed scores
		rules = []
		all_rules = Rule.query.filter_by(tournament_id=tournament.id).all()
		all_unique_score_types = []
		
		for rule in all_rules:
			rule_type = RuleType.query.filter_by(id=rule.type_id).first()
			rule_data = {
				"name": rule_type.name,
				"weight": rule.weight
				}
			needed_score_types_data = []
			for score_type in rule_type.score_types:
				needed_score_types_data.append(score_type.name)
				
				# remember score type for later
				if not score_type in all_unique_score_types:
					all_unique_score_types.append(score_type)
			rule_data["scores"] = needed_score_types_data
			rules.append(rule_data)
		dict["rules"] = rules
			
		# add teams and rules for that tournament
		teams = []
		all_participations = Participation.query.filter_by(tournament_id=tournament.id).all()
		for participation in all_participations:
			team = Team.query.filter_by(id=participation.team_id).first()
			team_data = {"id": team.id}
			score_data = {}
			for score_type in all_unique_score_types:
				score = Score.getForTournament(score_type.id, tournament.id, team.id)
				score_data[score_type.name] = score.value
			team_data["scores"] = score_data
			
			teams.append(team_data)
		dict["teams"] = teams
			
		return dict
	
	# after a successful simulation, the result needs to be put into the DB
	def parseJSONResults(self, json_object, tournament):
		# first get the general ranking layout (aka "1, 2, 3, 4, REST") and save it
		rank_counter = 0 # for correct sorting later
		for rank_data in json_object["ranks"]:
			result_place_type = ResultPlaceType(tournament.id, rank_counter, rank_data["name"])
			self.db.session.add(result_place_type)
			rank_counter += 1
		# then get the rank percentage for every team
		for team_data in json_object["teams"]:
			rank_counter = 0
			for result in team_data["ranks"]:
				result_place = ResultPlace(tournament.id, team_data["id"], rank_counter, result["percentage"])
				self.db.session.add(result_place)
				rank_counter += 1
		self.db.session.commit()