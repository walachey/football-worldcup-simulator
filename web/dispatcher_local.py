from dispatcher import *

class DispatcherLocal(Dispatcher):
	
	def executeDispatchment(self, json_object):	
		dispatchment_thread = threading.Thread(target=self.localDispatchment, args=(json_object, ))
		dispatchment_thread.start()
	
	# this should run in a different thread
	def localDispatchment(self, json_object):
		# construct command to start the simulation client
		command = self.config.getCompleteSimulationProgramPath()
		# the JSON input will the given via stdin
		json_string = json.dumps(json_object)
		self.config.logger.debug("TOURNAMENTING " + json_string)
		
		tournament_id = json_object["tournament_id"]
		tournament = None
		
		try:
			# run and wait for termination
			process = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdout, stderr) = process.communicate(json_string)
			
			self.config.logger.debug("PROGRAM TERMINATED WITH CODE " + str(process.returncode))
			self.config.logger.debug("STDOUT ---------------------" + stdout)
			if stderr:
				self.config.logger.warning("STDERR ---------------------" + stderr)
		
			session = getSession()
			tournament = session.query(Tournament).filter_by(id=tournament_id).first()
			
			if process.returncode == 0:
				tournament.state = TournamentState.finished
				self.parseJSONResults(json.loads(stdout), tournament, session)
			else:
				tournament.state = TournamentState.error
				if stderr:
					for error_text in stderr.split("\n"):
						if len(error_text) > 2:
							error = TournamentExecutionError(tournament.id, error_text)
							session.add(error)
		except Exception as e:
			if not tournament:
				session = getSession()
				tournament = session.query(Tournament).filter_by(id=tournament_id).first()
			if tournament:
				tournament.state = TournamentState.error
				
				for error_text in str(e).split("\n"):
					if len(error_text) > 2:
						error = TournamentExecutionError(tournament.id, error_text)
						session.add(error)
				import os
				session.add(TournamentExecutionError(tournament.id, 
					"Filepath: " + os.path.dirname(os.path.realpath(__file__))))
				session.add(TournamentExecutionError(tournament.id, 
					"Working Directory: " + os.getcwd()))
		finally:
			session.commit()
			session.close()
			cleanupSession()