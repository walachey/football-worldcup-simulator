from flask import Flask

class WCSConfiguration:
	# flask configuration
	flask_host = '0.0.0.0' # '0.0.0.0' for public network - use only with debug off; None for localhost
	flask_port = 5000
	flask_template_folder = "templates"
	flask_application_name = "World-Cup Sim"
	
	# database configuration
	database_connection_string = "mysql://worldcup_admin:JPpbueH5vX4Ee6Th@localhost/worldcup"
	database_connection_password = "JPpbueH5vX4Ee6Th"
	
	# session configuration
	session_secret_key = "hello i am a pretty secret key"
	
	# debugging
	is_debug_mode_enabled = True
	log_file_name = "WCSLog.log"
	
	def getFlaskApp(self):
		app = Flask(self.flask_application_name, template_folder=self.flask_template_folder)
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
		if not self.log_file_name: return
		
		import logging
		file_handler = logging.FileHandler(self.log_file_name)
		file_handler.setLevel(logging.DEBUG)
		flask_application.logger.addHandler(file_handler)


main_configuration = WCSConfiguration()