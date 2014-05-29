from configuration import main_configuration as config
from flask import Flask, request
from flask import session as user_session
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import AdminIndexView
import md5

from database_models import *

admin = None
cache = None

class LoginView(AdminIndexView):
	@expose('/', methods=['POST', 'GET'])
	def index(self):
		cachecleared = False
		invalidated_tournaments = False
		result_entered = ""
		
		try:
			if "pw" in request.form: # login
				user_session["adminpw"] = md5.new(request.form["pw"]).digest()
				return self.render("admin_login.html", refresh=True, logged_in=True)
			elif "bof_round" in request.form:
				result_entered = "Incorrect Data"
				bof_round = int(request.form["bof_round"])
				team_ccs = (request.form["team_left"], request.form["team_right"])
				goals = [request.form["goals_left"], request.form["goals_right"]]
				
				is_ok = bof_round != None and (bof_round != -1) and not "" in team_ccs and not "" in goals
				
				if is_ok:
					result_entered = "ERROR"
					session = getSession()
					(cc1, cc2) = team_ccs
					teams = [session.query(Team).filter_by(country_code=cc1).first(), session.query(Team).filter_by(country_code=cc2).first()]
					
					if not None in teams:
						result = DatabaseMatchResult(bof_round, teams[0], teams[1], int(goals[0]), int(goals[1]))
						session.add(result)
						session.commit()
						result_entered = "Result saved!"
					else:
						result_entered = "Invalid Country Code"
					cleanupSession()
					
				
			elif "invalidate_tournament_cache" in request.form:
				session = getSession()
				tournaments = session.query(Tournament).all()
				for tournament in tournaments:
					tournament.hash = ""
				session.commit()
				cleanupSession()
				invalidated_tournaments = True
			elif "clearcache" in request.form:
				cache.clear()
				cachecleared = True
			elif request.method == 'POST': # logout
				user_session["adminpw"] = ""
		except:
			pass
		return self.render("admin_login.html", refresh=False, logged_in=LoginView.is_logged_in(), cachecleared=cachecleared, invalidated_tournaments=invalidated_tournaments, result_entered=result_entered)
		
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

def init(app, new_cache):
	global admin
	global cache
	session = getSession()
	cache = new_cache
	admin = Admin(app, index_view=LoginView(name='Login/Logout'))

	admin.add_view(AuthModelView(RuleType, session))
	admin.add_view(AuthModelView(ScoreType, session))
	admin.add_view(AuthModelView(TournamentType, session))
	admin.add_view(AuthModelView(Team, session))
	admin.add_view(AuthModelView(TournamentExecutionError, session))
	cleanupSession()