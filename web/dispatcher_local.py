from dispatcher import *

class DispatcherLocal(Dispatcher):
	
	def executeDispatchment(self, json_object):	
		dispatchment_thread = threading.Thread(target=self.localDispatchment, args=(json_object, ))
		dispatchment_thread.start()
	
	# this should run in a different thread
	def localDispatchment(self, json_object):
		session = getSession()
		# construct command to start the simulation client
		command = self.config.getCompleteSimulationProgramPath()
		# the JSON input will the given via stdin
		json_string = json.dumps(json_object)
		self.config.logger.debug("TOURNAMENTING " + json_string)
		# run and wait for termination
		process = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = process.communicate(json_string)
		
		self.config.logger.debug("PROGRAM TERMINATED WITH CODE " + str(process.returncode))
		self.config.logger.debug("STDOUT ---------------------" + stdout)
		if stderr:
			self.config.logger.warning("STDERR ---------------------" + stderr)
		
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
		finally:
			session.commit()