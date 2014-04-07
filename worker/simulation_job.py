import simulation_job_config as config

import threading
import subprocess
import json

class SimulationJob:

	@staticmethod
	def simulate(job):
		json_input = job.data
		returncode = 1
		
		stderr = ""
		stdout = json_input # mirror back input in case of errors
		
		try:
			process = subprocess.Popen(config.simulation_path_program_path, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdout, stderr) = process.communicate(json.dumps(json_input))
			returncode = process.returncode
		except Exception as e:
			stderr = stderr + "\n" + str(e)
			print stderr
			
		job.data = {"stdout": stdout, "stderr": stderr, "code": returncode}
		
		if returncode == 0:
			job.complete("finished")
		else:
			job.complete("failed")
		