import os

print "Installing dependencies.."
os.system("pip install Flask")
os.system("pip install Flask-SQLAlchemy")
os.system("pip install Flask-Admin")
os.system("pip install Flask-Cache")
print "\tDependencies installed."

print "Checking dependencies.."
try:
	import flask
except Exception as e:
	print "\tERROR: Flask does not appear to be installed."
	print e.msg

try:
	from flask.ext.cache import Cache
except Exception as e:
	print "\tERROR: Flask-Cache does not appear to be installed."
	print e.msg
	
try:
	from flask.ext.sqlalchemy import SQLAlchemy
except Exception as e:
	print "\tERROR: Flask-SQLAlchemy does not appear to be installed."
	print e.msg
	
try:
	from sqlalchemy.ext.declarative import declarative_base
except Exception as e:
	print "\tERROR: SQLAlchemy not appear to be installed."
	print e.msg
	
try:
	from flask.ext.admin import Admin
except Exception as e:
	print "\tERROR: Flask-Admin does not appear to be installed."
	print e.msg
	
print "\tDependency check complete."

# create custom config if it doesn't exist
print "Checking custom configuration.."
import os.path
import shutil
custom_config_filename = "configuration_custom.py"
custom_config_template_filename = "configuration_custom_template.py"
folder = "."
if os.path.isfile(folder + "/" + custom_config_filename):
	print "\tExisting custom configuration found."
else:
	created = False
	try:
		shututil.copyfile(folder + "/" + custom_config_template_filename, folder + "/" + custom_config_filename)
		created = True
	except Exception as e:
		print "\tError when trying to create custom configuration file."
		print e.msg
	if created:
		print "\tSuccessfully created custom configuration file."

