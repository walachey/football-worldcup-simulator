from flask import Flask

class WCSConfiguration:
	# flask configuration
	flask_host = None # '0.0.0.0' for public network - use only with debug off; None for localhost
	flask_port = 5000
	flask_template_folder = "templates"
	flask_application_name = "World-Cup Sim"
	flask_admin_password = "secret admin pw"
	
	# database configuration
	database_connection_string = "mysql://user:password@localhost/databasename"
	database_connection_password = "secret database pw"
	
	# session configuration
	session_secret_key = "secret session key"
	session_auto_timeout = 7200
	
	# for running the actual simulation
	simulation_path = "./"
	simulation_program_name = "WorldCupSimulator"
	simulation_thread_count = 2
	simulation_run_count = 1000 # total runs per simulation
	
	# debugging
	is_debug_mode_enabled = False
	log_file_name = None
	echo_sql = False
		
	# this will be set on initialization
	logger = None
	
	def getFlaskApp(self):
		app = Flask(self.flask_application_name, template_folder=self.flask_template_folder)
		if self.session_auto_timeout != None:
			app.config["SQLALCHEMY_POOL_RECYCLE"] = self.session_auto_timeout
		self.setupFlaskApplication(app)
		return app
	
	# do necessary initial setup for the flask application object
	def setupFlaskApplication(self, flask_application):
		flask_application.secret_key = self.session_secret_key
		flask_application.debug = self.is_debug_mode_enabled
		# enable line statements for Jinja templates
		flask_application.jinja_env.line_statement_prefix = '#'
		flask_application.jinja_env.line_comment_prefix = '##'
		
		self.setupLogging(flask_application)
		
	# enable logging to file if applicable
	def setupLogging(self, flask_application):
		self.logger = flask_application.logger
		
		if not self.log_file_name: return
		
		import logging
		file_handler = logging.FileHandler(self.log_file_name)
		level = logging.DEBUG if self.is_debug_mode_enabled else logging.WARNING
		file_handler.setLevel(level)
		flask_application.logger.addHandler(file_handler)

	def getCompleteSimulationProgramPath(self):
		return self.simulation_path + self.simulation_program_name

main_configuration = WCSConfiguration()

try:
	import configuration_custom
	configuration_custom.customize(main_configuration)
except ImportError:
	print "Could not find custom configuration."