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
	def checkDispatchment(self, tournament_id, session):
		open_tournament = session.query(Tournament).filter_by(state=TournamentState.pending).with_lockmode("update").first()
		# no open jobs?
		if not open_tournament:
			return
			
		self.dispatchTournament(open_tournament, session)
		
	# prepare tournament data and finally executeDispatchment
	def dispatchTournament(self, tournament_id, session):
		# from here on everything needs to be protected to reset tournaments in case of failures
		tournament = None
		try:
			tournament = session.query(Tournament).filter_by(id=tournament_id).first()
			if not tournament:
				config.logger.warning("Tournament object not found for dispatchment.. ID " + str(tournament_id))
				return
			tournament.state = TournamentState.running
			session.commit()
			
			json_object = self.toDictForSimulationInput(tournament, session)
			self.executeDispatchment(json_object)
		except Exception as e:
			tournament.state = TournamentState.error
			session.commit()
			
			self.config.logger.error("EXCEPTION: " + str(e))
			if self.config.is_debug_mode_enabled:
				import traceback
				traceback.print_exc()
			error = TournamentExecutionError(tournament.id, str(e))
			session.add(error)
			session.commit()
		finally:
			pass
	
	def executeDispatchment(self, json_object):
		pass
		
	# creates a dictionary that can be used to create JSON from it and pass it to the simulation program
	def toDictForSimulationInput(self, tournament, session):	
		# this is the root of the tree with all global config settings for the simulation
		tournament_type = session.query(TournamentType).filter_by(id=tournament.type_id).first()
		dict = {
			"thread_count": self.config.simulation_thread_count,
			"tournament_id": tournament.id,
			"run_count": self.config.simulation_run_count,
			"tournament_type": tournament_type.internal_identifier
			}
		# get all active rules for this tournament and calculate needed scores
		rules = []
		all_rules = session.query(Rule).filter_by(tournament_id=tournament.id).all()
		all_unique_score_types = []
		
		for rule in all_rules:
			rule_type = session.query(RuleType).filter_by(id=rule.type_id).first()
			rule_data = {
				"weight": rule.weight,
				"function": rule_type.internal_function_identifier,
				"backref": rule_type.is_backref_rule
				}
			
			# every rule has certain scores associated
			needed_score_types_data = []
			for score_type in rule_type.getScoreTypes(session):
				needed_score_types_data.append(score_type.name)
				
				# remember score type for later
				if not score_type in all_unique_score_types:
					all_unique_score_types.append(score_type)
			rule_data["scores"] = needed_score_types_data

			# rules might need custom parameters from the user
			parameters = {}
			for parameter_type in rule_type.getParameterTypes(session):
				# check if parameter for this tournament exists
				parameter = session.query(RuleParameter).filter_by(type_id=parameter_type.id, tournament_id=tournament.id).first()
				value = parameter.value if parameter != None else parameter_type.default_value
				parameters[parameter_type.internal_identifier] = value
			if parameters:
				rule_data["parameters"] = parameters
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
				score = Score.getForTournament(score_type.id, tournament.id, team.id, session)
				score_data[score_type.name] = score.value
			team_data["scores"] = score_data
			
			teams.append(team_data)
		dict["teams"] = teams

		return dict
	
	# after a successful simulation, the result needs to be put into the DB
	def parseJSONResults(self, json_object, tournament, session):
		try:
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
					result = BracketTeamResult(tournament.id, bof_round, game_in_round, team["id"], team["match_data"]["wins"], team["match_data"]["draws"], team["match_data"]["matches"])
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
		
		except Exception as e:
			import traceback
			error_message = traceback.format_exc()
			self.config.logger.error("An error occurred: " + str(e) + "\n" + error_message)
			tournament.state = TournamentState.error
			
			for error_text in error_message.split("\n"):
				if len(error_text) > 2:
					error = TournamentExecutionError(tournament.id, error_text)
					session.add(error)
		
		session.commit()