from database_models import db
from database_models import Team
from database_models import *

db.drop_all()
db.create_all()

session = getSession()

# the contents of this class will be split into different database tables
class CompactTeamData:
	name = None
	country_code = None
	ELO = None
	group = None
	FIFA = None
	Value = None
	
	def __init__(self, name, country_code, group, ELO, FIFA, Value):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO
		self.FIFA = FIFA
		self.Value = Value

all_teams = [
	# group A
	CompactTeamData("Brazil", "BR", "A", 2110, 1125, 434500000),
	CompactTeamData("Croatia", "HR", "A", 1779, 966, 196600000),
	CompactTeamData("Mexico", "MX", "A", 1784, 887, 50250000),
	CompactTeamData("Cameroon", "CM", "A", 1593, 626, 126950000),
	# group B
	CompactTeamData("Spain", "ES", "B", 2082, 1506, 579000000),
	CompactTeamData("Netherlands", "NL", "B", 1979, 1122, 195500000),
	CompactTeamData("Chile", "CL", "B", 1896, 1038, 138700000),
	CompactTeamData("Australia", "AU", "B", 1711, 576, 25300000),
	# group C
	CompactTeamData("Colombia", "CO", "C", 1912, 1211, 191050000),
	CompactTeamData("Greece", "GR", "C", 1813, 1084, 79900000),
	CompactTeamData("Ivory Coast", "CI", "C", 1786, 841, 138700000),
	CompactTeamData("Japan", "JP", "C", 1747, 601, 91400000),
	# group D
	CompactTeamData("Uruguay", "UY", "D", 1898, 1157, 215700000),
	CompactTeamData("Costa Rica", "CR", "D", 1700, 734, 28200000),
	CompactTeamData("England", "EN", "D", 1906, 1032, 387500000),
	CompactTeamData("Italy", "IT", "D", 1887, 1135, 387000000),
	# group E
	CompactTeamData("Switzerland", "CH", "E", 1822, 1159, 161500000),
	CompactTeamData("Ecuador", "EC", "E", 1816, 831, 57050000),
	CompactTeamData("France", "FR", "E", 1855, 917, 397250000),
	CompactTeamData("Honduras", "HN", "E", 1664, 716, 16850000),
	# group F
	CompactTeamData("Argentina", "AR", "F", 1994, 1255, 424500000),
	CompactTeamData("Bosnia and Herzegovina", "BA", "F", 1758, 919, 109500000),
	CompactTeamData("Iran", "IR", "F", 1719, 729, 30650000),
	CompactTeamData("Nigeria", "NG", "F", 1718, 616, 91250000),
	# group G
	CompactTeamData("Germany", "DE", "G", 2060, 1314, 427000000),
	CompactTeamData("Portugal", "PT", "G", 1905, 1219, 262500000),
	CompactTeamData("Ghana", "GH", "G", 1700, 733, 99600000),
	CompactTeamData("USA", "US", "G", 1841, 1044, 51100000),
	# group H
	CompactTeamData("Belgium", "BE", "H", 1807, 1117, 351450000),
	CompactTeamData("Algeria", "DZ", "H", 1582, 819, 50700000),
	CompactTeamData("Russia", "RU", "H", 1819, 862, 185800000),
	CompactTeamData("Korea Republic", "KR", "H", 1683, 556, 36750000)
	]

# first step: insert teams into DB to get the IDs
for team_data in all_teams:
	team = Team(team_data.name, team_data.country_code)
	session.add(team)
# add new ELO rating score
session.add(ScoreType("ELO", "The ELO score known from chess."))
session.add(ScoreType("FIFA", "FIFA ranking points"))
session.add(ScoreType("Value", "Value of the team in Euro"))
# add default ELO calculation rule
elo_rule = RuleType("ELO", "Calculation using the ELO score.", "elo_binary")
elo_rule.makeDefaultRule(1.0)
session.add(elo_rule)
fifa_rule = RuleType("FIFA", "Calculation using the FIFA ranking.", "fifa_binary")
fifa_rule.makeDefaultRule(0.2)
session.add(fifa_rule)
value_rule = RuleType("Value", "Calculation using the monetary value.", "value_binary")
value_rule.makeDefaultRule(0.2)
session.add(value_rule)
# add default tournament types
session.add(TournamentType("1 vs 1", "A simple 1 vs 1 test tournament.", 2, "TwoHandsIcon.png", "1v1"))
session.add(TournamentType("World Cup", "The standard FIFA World Cup.", 32, "StdLeagueIcon.png", "worldcup", "worldcup_view"))
# only after comitting will the objects have valid IDs assigned!
session.commit()

# get the objects we just added (now with correct ID)
elo = session.query(ScoreType).filter_by(name="ELO").first()
fifa = session.query(ScoreType).filter_by(name="FIFA").first()
value = session.query(ScoreType).filter_by(name="Value").first()
assert elo != None
assert fifa != None
assert value != None

elo_rule.score_types.append(elo)
fifa_rule.score_types.append(fifa)
value_rule.score_types.append(value)

# and finish the team setup
for team_data in all_teams:
	team = session.query(Team).filter_by(country_code=team_data.country_code).first()
	assert team != None
	
	session.add(Score(elo.id, team.id, team_data.ELO))
	session.add(Score(fifa.id, team.id, team_data.FIFA))
	session.add(Score(value.id, team.id, team_data.Value))

session.commit()
print "..done"