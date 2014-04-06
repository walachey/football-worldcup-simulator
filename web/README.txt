The Python backend has the following dependencies:
Python packages (can usually be installed via "pip install <name>":
	Flask
	Flask-SQLAlchemy
	Flask-Admin
	Flask-Cache

The Web Frontend has the following dependencies, that need to be placed in web/static for deployment:
	Chart.js as Chart.min.js
	jquery as jquery-1.11.0.min.js
	jquery-tablesorter as jquery.tablesorter.min.js
	jquery-metadata as jquery.metadata.js

INSTALLATION:
	You will need Python2.7 installed.
	It is suggested to use virtualenv to manage the installation and dependencies:
		I.) pip install virtualenv
		or:
			I.2.) easy-install virtualenv
			I.3.) apt-get install python-virtualenv (for Ubuntu) 
		II.1.) cd this-folder
		II.2.) virtualenv venv
		and then activate it with:
			. venv/bin/activate (Linux/OSX)
			venv\scripts\activate (Windows)
		
		For more information, see:
			http://flask.pocoo.org/docs/installation/#virtualenv
		
	To do a first-time setup, run setup.py, which does the following:
		- get all the requirements via "pip install"
		- create a "configuration_custom.py" file
		- run "default.py" to setup the database with default values