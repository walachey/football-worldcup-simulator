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
		session = getSession()
		
		open_tournament = session.query(Tournament).filter_by(state=TournamentState.pending).with_lockmode("update").first()
		# no open jobs?
		if not open_tournament:
			return
		open_tournament.state = TournamentState.running
		session.commit()
		
		# from here on everything needs to be protected to reset tournaments in case of failures
		try:
			json_object = self.toDictForSimulationInput(open_tournament)
			open_tournament = None
			dispatchment_thread = threading.Thread(target=self.dispatchJob, args=(json_object, ))
			dispatchment_thread.start()
		except Exception as e:
			print "EXCEPTION: " + str(e)
			open_tournament.state = TournamentState.error
			session.commit()
			import traceback
			traceback.print_exc()
		finally:
			pass
	
	# this should run in a different thread
	def dispatchJob(self, json_object):
		session = getSession()
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
		
		tournament = session.query(Tournament).filter_by(id=json_object["tournament_id"]).first()
		try:
			if process.returncode == 0:
				tournament.state = TournamentState.finished
				self.parseJSONResults(json.loads(stdout), tournament)
			else:
				tournament.state = TournamentState.error
				if stderr:
					for error_text in stderr.split("\n"):
						if len(error_text) > 2:
							error = TournamentExecutionError(tournament.id, error_text)
							session.add(error)
			
		except Exception as e:
			import traceback
			error_message = traceback.format_exc()
			print "An error occurred: " + str(e)
			print error_message
			tournament.state = TournamentState.error
			
			for error_text in error_message.split("\n"):
				if len(error_text) > 2:
					error = TournamentExecutionError(tournament.id, error_text)
					session.add(error)
		finally:
			session.commit()
	
	# creates a dictionary that can be used to create JSON from it and pass it to the simulation program
	def toDictForSimulationInput(self, tournament):
		session = getSession()
		
		# this is the root of the tree with all global config settings for the simulation
		dict = {
			"thread_count": self.config.simulation_thread_count,
			"tournament_id": tournament.id,
			"run_count": self.config.simulation_run_count,
			"tournament_type": tournament.tournament_type.internal_identifier
			}
		
		# get all active rules for this tournament and calculate needed scores
		rules = []
		all_rules = session.query(Rule).filter_by(tournament_id=tournament.id).all()
		all_unique_score_types = []
		
		for rule in all_rules:
			rule_type = session.query(RuleType).filter_by(id=rule.type_id).first()
			rule_data = {
				"weight": rule.weight,
				"function": rule_type.internal_function_identifier
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
		all_participations = session.query(Participation).filter_by(tournament_id=tournament.id).all()
		for participation in all_participations:
			team = session.query(Team).filter_by(id=participation.team_id).first()
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
		session = getSession()
		
		# first get the general ranking layout (aka "1, 2, 3, 4, REST") and save it
		rank_counter = 0 # for correct sorting later
		for rank_data in json_object["ranks"]:
			result_place_type = ResultPlaceType(tournament.id, rank_counter, rank_data["name"])
			session.add(result_place_type)
			rank_counter += 1
		# then get the rank percentage for every team
		for team_data in json_object["matches"]["all"]["teams"]:
			rank_counter = 0
			for result in team_data["ranks"]:
				result_place = ResultPlace(tournament.id, team_data["id"], rank_counter, result["percentage"])
				session.add(result_place)
				rank_counter += 1
			# general results
			average_goals = team_data["avg_goals"]
			average_place = team_data["avg_place"]
			result = Result(tournament.id, team_data["id"], average_goals, average_place)
			session.add(result)
		# then all the match cluster results
		for match_name in json_object["matches"]:
			# first_result = True
			bof_round = json_object["matches"][match_name]["bof_round"]
			game_in_round = json_object["matches"][match_name]["game_in_round"]
			# for match in json_object["matches"][match_name]["results"]:
				# result = MatchResult(tournament.id, bof_round, game_in_round, tuple(match["teams"]), tuple(match["goals"]), match["count"])
				# # the list is sorted, so the first result is the most probable one
				# if first_result:
					# first_result = False
					# result.most_frequent = True
				# session.add(result)
			bracket_team_results = []
			for team in json_object["matches"][match_name]["teams"]:
				result = BracketTeamResult(tournament.id, bof_round, game_in_round, team["id"], team["match_data"]["wins"], team["match_data"]["matches"])
				bracket_team_results.append(result)
				session.add(result)
			# figure out highest bracket result and mark as most_frequent
			best = (0, None)
			for result in bracket_team_results:
				(current, team) = best
				if current < result.wins:
					best = (result.wins, result)
			(max_wins, best_result) = best
			best_result.most_frequent = True
		session.commit()