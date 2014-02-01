from database_models import db
from database_models import Team
from database_models import *

db.drop_all()
db.create_all()

# the contents of this class will be split into different database tables
class CompactTeamData:
	name = None
	country_code = None
	ELO = None
	group = None
	
	def __init__(self, name, country_code, group, ELO):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO

all_teams = [
	# group A
	CompactTeamData("Brazil", "BR", "A", 2110),
	CompactTeamData("Croatia", "HR", "A", 1779),
	CompactTeamData("Mexico", "MX", "A", 1784),
	CompactTeamData("Cameroon", "CM", "A", 1593),
	# group B
	CompactTeamData("Spain", "ES", "B", 2082),
	CompactTeamData("Netherlands", "NL", "B", 1979),
	CompactTeamData("Chile", "CL", "B", 1896),
	CompactTeamData("Australia", "AU", "B", 1711),
	# group C
	CompactTeamData("Colombia", "CO", "C", 1912),
	CompactTeamData("Greece", "GR", "C", 1813),
	CompactTeamData("Ivory Coast", "CI", "C", 1786),
	CompactTeamData("Japan", "JP", "C", 1747),
	# group D
	CompactTeamData("Uruguay", "UY", "D", 1898),
	CompactTeamData("Costa Rica", "CR", "D", 1700),
	CompactTeamData("England", "EN", "D", 1906),
	CompactTeamData("Italy", "IT", "D", 1887),
	# group E
	CompactTeamData("Switzerland", "CH", "E", 1822),
	CompactTeamData("Ecuador", "EC", "E", 1816),
	CompactTeamData("France", "FR", "E", 1855),
	CompactTeamData("Honduras", "HN", "E", 1664),
	# group F
	CompactTeamData("Argentina", "AR", "F", 1994),
	CompactTeamData("Bosnia and Herzegovina", "BA", "F", 1758),
	CompactTeamData("Iran", "IR", "F", 1719),
	CompactTeamData("Nigeria", "NG", "F", 1718),
	# group G
	CompactTeamData("Germany", "DE", "G", 2060),
	CompactTeamData("Portugal", "PT", "G", 1905),
	CompactTeamData("Ghana", "GH", "G", 1700),
	CompactTeamData("USA", "US", "G", 1841),
	# group H
	CompactTeamData("Belgium", "BE", "H", 1807),
	CompactTeamData("Algeria", "DZ", "H", 1582),
	CompactTeamData("Russia", "RU", "H", 1819),
	CompactTeamData("Korea Republic", "KR", "H", 1683)
	]

# first step: insert teams into DB to get the IDs
for team_data in all_teams:
	team = Team(team_data.name, team_data.country_code)
	db.session.add(team)
# add new ELO rating score
db.session.add(ScoreType("ELO", "The ELO score known from chess."))
# add default ELO calculation rule
db.session.add(RuleType("ELO", "Calculation using the ELO score."))
# add default tournament types
db.session.add(TournamentType("1 vs 1", "A simple 1 vs 1 test tournament.", 2, "TwoHandsIcon.png"))
db.session.add(TournamentType("World Cup", "The standard FIFA World Cup.", 32, "StdLeagueIcon.png"))
# only after comitting will the objects have valid IDs assigned!
db.session.commit()

# get the objects we just added (now with correct ID)
elo = ScoreType.query.filter_by(name="ELO").first()
assert elo != None

# and finish the team setup
for team_data in all_teams:
	team = Team.query.filter_by(country_code=team_data.country_code).first()
	assert team != None
	
	db.session.add(Score(elo.id, team.id, team_data.ELO))

db.session.commit()
print "..done"