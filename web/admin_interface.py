from configuration import main_configuration as config
from flask import Flask, request
from flask import session as user_session
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import AdminIndexView
import md5
import datetime

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
						# enter new match result
						result = DatabaseMatchResult(bof_round, teams[0], teams[1], int(goals[0]), int(goals[1]))
						session.add(result)
						
						# reset all tournaments with match database enabled
						parameter_type = session.query(RuleParameterType).filter_by(internal_identifier="use_match_database").first()
						all_parameters = session.query(RuleParameter).filter_by(type_id=parameter_type.id).all()
						
						for par in all_parameters:
							if par.value == 0.0:
								continue
							
							tournament = session.query(Tournament).filter_by(id=par.tournament_id).first()
							tournament.hash = ""
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

class EnterOddsView(BaseView):

	@expose('/', methods=['POST', 'GET'])
	def index(self):
		session = getSession()
		fetched = False
		result_entered = False
		results = []
		date = None
		zero_point_teams = []
		if "fetch" in request.form:
			date = str(datetime.today().date())
			if request.form["source"] == "bets":
				import retrieve_betting_odds
				odds = retrieve_betting_odds.getResults()
				
				for odd in odds:
					team = session.query(Team).filter_by(name=odd.name).first()
					if team:
						results.append({"team_name": team.name, "CC": team.country_code, "odds": 1.0 / (1.0 + odd.getAvg())})
					else:
						results.append({"team_name": "ERROR", "CC": "XX", "odds": 1.0 / (1.0 + odd.getAvg())})
				fetched = True
			elif request.form["source"] in ["spi", "elo", "fifa", "value"]:
				tournament = session.query(Tournament).filter_by(id=request.form["tournament_id"]).first()
				if tournament:
					# get all finals results
					for bracket_team_result in session.query(BracketTeamResult).filter_by(tournament_id=tournament.id,bof_round=1,game_in_round=1).order_by(BracketTeamResult.wins.desc()):
						team = session.query(Team).filter_by(id=bracket_team_result.team_id).first()
						results.append({"team_name": team.name, "CC": team.country_code, "odds": bracket_team_result.wins / float(tournament.run_count)})
				fetched = True
		elif "save" in request.form:
			source = source=request.form["source"]
			if source in ["bets", "spi", "elo", "fifa", "value"]:
				# check date
				date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
				
				# we need data for all the teams
				all_odds_data = []
				for team in session.query(Team):
					odds = 0.0
					if team.country_code in request.form:
						odds = request.form[team.country_code]
					else:
						zero_point_teams.append(team.name)
					all_odds_data.append(OddsData(team, odds, date, source))
				# now remove all old info for this date
				old_odds = session.query(OddsData).filter_by(date=date, source=source).all()
				for old in old_odds:
					session.delete(old)
				# and add the new ones
				for odd in all_odds_data:
					session.add(odd)
				session.commit()
				result_entered = True
			
		cleanupSession()
		return self.render("admin_enter_odds.html", results=results, fetched=fetched, result_entered=result_entered, date=date, zero_point_teams=zero_point_teams)
	
	def is_accessible(self):
		return LoginView.is_logged_in()
		
def init(app, new_cache):
	global admin
	global cache
	session = getSession()
	cache = new_cache
	admin = Admin(app, index_view=LoginView(name='Login/Logout'))
	admin.add_view(EnterOddsView(name="Enter Odds"))
	
	admin.add_view(AuthModelView(RuleType, session))
	admin.add_view(AuthModelView(ScoreType, session))
	admin.add_view(AuthModelView(TournamentType, session))
	admin.add_view(AuthModelView(Team, session))
	admin.add_view(AuthModelView(TournamentExecutionError, session))
	cleanupSession()