from configuration import main_configuration as config
from flask import Flask, request
from flask import session as user_session
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import AdminIndexView
import md5

from database_models import *

admin = None

class LoginView(AdminIndexView):
	@expose('/', methods=['POST', 'GET'])
	def index(self):
		if "pw" in request.form: # login
			user_session["adminpw"] = md5.new(request.form["pw"]).digest()
			return self.render("admin_login.html", refresh=True, logged_in=True)
		elif request.method == 'POST': # logout
			user_session["adminpw"] = ""
		return self.render("admin_login.html", refresh=False, logged_in=LoginView.is_logged_in())
		
	@staticmethod
	def is_logged_in():
		if not "adminpw" in user_session:
			return False
		if user_session["adminpw"] != md5.new(config.flask_admin_password).digest():
			return False
		return True
		
	def is_accessible(self):
		return True
	
class AuthModelView(ModelView):
	def is_accessible(self):
		return LoginView.is_logged_in()

def init(app):
	global admin
	admin = Admin(app, index_view=LoginView(name='Login/Logout'))
	session = getSession()
	admin.add_view(AuthModelView(RuleType, session))
	admin.add_view(AuthModelView(ScoreType, session))
	admin.add_view(AuthModelView(TournamentType, session))
	admin.add_view(AuthModelView(Team, session))
	admin.add_view(AuthModelView(TournamentExecutionError, session))
	Session.remove()