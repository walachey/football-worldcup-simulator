
def customize(config):
	# use None for localhost and '0.0.0.0' for public networks
	# Attention: only use it on public networks with debug disabled
	config.flask_host = None
	# config.flask_port = 5000
	
	# please choose a secret and unique admin password yourself
	config.flask_admin_password = 
	
	# database setup. This takes a database connection string for SQLAlchemy
	# f.e.: "mysql://user:password@localhost/databasename"
	config.database_connection_string = 
	config.database_connection_password = 
	
	# this is used for storing session data
	# please choose a random sequence of letters
	config.session_secret_key =
	
	# path to the simulator
	config.simulation_path = None
	# the actual program name
	config.simulation_program_name = None
	
	# logging will be enabled when a file is specified
	config.log_file_name = None
	
	# there are more options that can be changed
	# check out "configuration.py" for the option names
	
	
	