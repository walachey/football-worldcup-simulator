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
	Value = None # value in euro
	Age = None # avg. age
	HA = 0.0 # home advantage
	
	def __init__(self, name, country_code, group, ELO, FIFA, Value, Age, homeadvantage=0.0):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO
		self.FIFA = FIFA
		self.Value = Value
		self.HA = homeadvantage
		self.Age = Age

all_teams = [
	# group A
	CompactTeamData("Brazil", "BR", "A", 2110, 1125, 440500000 / 19.0, 27.60, homeadvantage=1.0),
	CompactTeamData("Croatia", "HR", "A", 1779, 966, 193200000 / 22.0, 27.60),
	CompactTeamData("Mexico", "MX", "A", 1784, 887, 39250000 / 18.0, 27.80),
	CompactTeamData("Cameroon", "CM", "A", 1593, 626, 114300000 / 23.0, 26.80),
	# group B
	CompactTeamData("Spain", "ES", "B", 2082, 1506, 577000000 / 21.0, 28.0),
	CompactTeamData("Netherlands", "NL", "B", 1979, 1122, 197000000 / 24.0, 26.10),
	CompactTeamData("Chile", "CL", "B", 1896, 1038, 142850000 / 24.0, 28.20),
	CompactTeamData("Australia", "AU", "B", 1711, 576, 25550000 / 23.0, 26.40),
	# group C
	CompactTeamData("Colombia", "CO", "C", 1912, 1211, 194550000 / 26.0, 27.70),
	CompactTeamData("Greece", "GR", "C", 1813, 1084, 80400000 / 22.0, 28.70),
	CompactTeamData("Ivory Coast", "CI", "C", 1786, 841, 142900000 / 26.0, 27.30),
	CompactTeamData("Japan", "JP", "C", 1747, 601, 91700000 / 22.0, 26.90),
	# group D
	CompactTeamData("Uruguay", "UY", "D", 1898, 1157, 154925000 / 21.0, 28.30),
	CompactTeamData("Costa Rica", "CR", "D", 1700, 734, 30200000 / 22.0, 26.70),
	CompactTeamData("England", "EN", "D", 1906, 1032, 387500000 / 30.0, 26.60),
	CompactTeamData("Italy", "IT", "D", 1887, 1135, 339000000 / 26.0, 27.90),
	# group E
	CompactTeamData("Switzerland", "CH", "E", 1822, 1159, 171000000 / 21.0, 26.10),
	CompactTeamData("Ecuador", "EC", "E", 1816, 831, 54550000 / 20.0, 27.90),
	CompactTeamData("France", "FR", "E", 1855, 917, 447500000 / 25.0, 26.60),
	CompactTeamData("Honduras", "HN", "E", 1664, 716, 18400000 / 23.0, 27.50),
	# group F
	CompactTeamData("Argentina", "AR", "F", 1994, 1255, 423500000 / 22.0, 27.50, homeadvantage=0.5),
	CompactTeamData("Bosnia and Herzegovina", "BA", "F", 1758, 919, 112000000 / 22.0, 26.80),
	CompactTeamData("Iran", "IR", "F", 1719, 729, 30700000 / 34.0, 27.70),
	CompactTeamData("Nigeria", "NG", "F", 1718, 616, 88650000 / 23.0, 24.80),
	# group G
	CompactTeamData("Germany", "DE", "G", 2060, 1314, 400000000 / 19.0, 26.80),
	CompactTeamData("Portugal", "PT", "G", 1905, 1219, 258250000 / 22.0, 27.80),
	CompactTeamData("Ghana", "GH", "G", 1700, 733, 97200000 / 21.0, 25.50),
	CompactTeamData("USA", "US", "G", 1841, 1044, 28750000 / 23.0, 28.00),
	# group H
	CompactTeamData("Belgium", "BE", "H", 1807, 1117, 341450000 / 22.0, 26.50),
	CompactTeamData("Algeria", "DZ", "H", 1582, 819, 54000000 / 28.0, 27.10),
	CompactTeamData("Russia", "RU", "H", 1819, 862, 193600000 / 25.0, 27.60),
	CompactTeamData("Korea Republic", "KR", "H", 1683, 556, 52500000 / 22.0, 25.50)
	]

# first step: insert teams into DB to get the IDs
for team_data in all_teams:
	team = Team(team_data.name, team_data.country_code)
	session.add(team)
# add new rating score types
session.add(ScoreType("ELO", "The ELO rating known from chess.", long_name="ELO rating"))
session.add(ScoreType("FIFA", "FIFA ranking points", long_name="FIFA rating"))
session.add(ScoreType("Value", "Average value of the players in Euro", long_name="&#216; value in &euro;"))
session.add(ScoreType("Age", "Average age of the team", long_name="&#216; age"))
session.add(ScoreType("HA", "Home-advantage of the team", long_name="Home-advantage"))
session.add(ScoreType("Custom", "User-defined custom rating", long_name="Custom rating", hidden=True))

# add certain custom parameters
custom_rule_parameter = RuleParameterType("normalization_constant", 10.0)
session.add(custom_rule_parameter)

# add default ELO calculation rule
elo_rule = RuleType("ELO", "Calculation using the ELO score.", "elo_binary")
elo_rule.makeDefaultRule(1.0)
session.add(elo_rule)

fifa_rule = RuleType("FIFA", "Calculation using the FIFA ranking.", "fifa_binary")
fifa_rule.makeDefaultRule(0.2)
session.add(fifa_rule)

value_rule = RuleType("Value", "Calculation based on average player value.", "value_binary")
value_rule.makeDefaultRule(0.2)
session.add(value_rule)

age_rule = RuleType("Age", "Calculation based on average age.", "age_binary")
age_rule.makeDefaultRule(0.1)
session.add(age_rule)

ha_rule = RuleType("HA", "Adjust the win expectancy based on the home-advantage.", "homeadvantage_binary", long_name="Home-advantage", is_backref_rule=True)
ha_rule.makeDefaultRule(1.0)
session.add(ha_rule)

luck_rule = RuleType("Luck", "Even the unexpected can happen!", "luck_binary")
luck_rule.makeDefaultRule(0.0)
session.add(luck_rule)

custom_rule = RuleType("Custom", "Define custom ratings and an own win expectancy function.", "custom_binary", long_name="Custom Rating", needs_custom_ratings=True)
custom_rule.makeDefaultRule(0.0)
session.add(custom_rule)
# add default tournament types
session.add(TournamentType("1 vs 1", "A simple 1 vs 1 test tournament.", 2, "TwoHandsIcon.png", "1v1"))
session.add(TournamentType("World Cup", "The standard FIFA World Cup.", 32, "StdLeagueIcon.png", "worldcup", "worldcup_view"))
# only after comitting will the objects have valid IDs assigned!
session.commit()

# get the objects we just added (now with correct ID)
elo = session.query(ScoreType).filter_by(name="ELO").first()
fifa = session.query(ScoreType).filter_by(name="FIFA").first()
value = session.query(ScoreType).filter_by(name="Value").first()
age = session.query(ScoreType).filter_by(name="Age").first()
ha = session.query(ScoreType).filter_by(name="HA").first()
custom = session.query(ScoreType).filter_by(name="Custom").first()
assert elo != None
assert fifa != None
assert value != None
assert age != None
assert ha != None
assert custom != None

elo_rule.score_types.append(elo)
fifa_rule.score_types.append(fifa)
value_rule.score_types.append(value)
age_rule.score_types.append(age)
ha_rule.score_types.append(ha)
custom_rule.score_types.append(custom)

custom_rule.parameter_types.append(custom_rule_parameter)

# and finish the team setup
for team_data in all_teams:
	team = session.query(Team).filter_by(country_code=team_data.country_code).first()
	assert team != None
	
	session.add(Score(elo.id, team.id, team_data.ELO))
	session.add(Score(fifa.id, team.id, team_data.FIFA))
	session.add(Score(value.id, team.id, team_data.Value))
	session.add(Score(age.id, team.id, team_data.Age))
	session.add(Score(ha.id, team.id, team_data.HA))

session.commit()
print "..done"