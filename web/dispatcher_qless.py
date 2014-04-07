from dispatcher import *
from time import sleep

import qless

class DispatcherQLess(Dispatcher):
	
	client = None
	
	def executeDispatchment(self, json_object):	
		if not self.client:
			self.client = qless.Client(self.config.qless_connection_string)
			
		self.client.queues["simulate"].put("simulation_job.SimulationJob", json_object)

		dispatchment_thread = threading.Thread(target=self.waitForJob)
		dispatchment_thread.start()
	
	# this should run in a different thread
	def waitForJob(self):
		job = None
		while job == None:
			sleep(1.0)
			job = self.client.queues["finished"].pop() or self.client.queues["failed"].pop()

		job.complete()
		job_data = job.data
		job_results = None
		if "stdout" in job_data and job_data["stdout"]:
			job_results = job_data["stdout"]
			if isinstance(job_results, basestring):
				job_results = json.loads(job_results)
		session = getSession()
		
		tournament = None
		if "tournament_id" in job_data:
			tournament = job_data["tournament_id"]
		elif job_results and "tournament_id" in job_results:
			tournament = job_results["tournament_id"]
		if tournament:
			tournament = session.query(Tournament).filter_by(id=tournament).first()
			
		try:
			returncode = job_data["code"]
			if returncode == 0 and job_results:
				tournament.state = TournamentState.finished
				self.parseJSONResults(job_results, tournament)
			else:
				if tournament:
					tournament.state = TournamentState.error
					
					if job_data["stderr"]:
						for error_text in job_data["stderr"].split("\n"):
							if len(error_text) > 2:
								error = TournamentExecutionError(tournament.id, error_text)
								session.add(error)
				else:
					if job_data["stderr"]:
						self.config.logger.warning("STDERR ---------------------" + job_data["stderr"]);
		except:
			if tournament:
				tournament.state = TournamentState.error
		finally:
			session.commit()