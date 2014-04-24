from database_models import db
from database_models import Team
from database_models import *

db.drop_all()
db.create_all()

session = getSession()

class SPI:
	off_rating = None
	def_rating = None
	rating = None
	
	def __init__(self, rating, off_rating, def_rating):
		self.off_rating = off_rating
		self.def_rating = def_rating
		self.rating = rating

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
	spi = None
	
	def __init__(self, name, country_code, group, ELO, FIFA, Value, Age, spi, homeadvantage=0.0):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO
		self.FIFA = FIFA
		self.Value = Value
		self.HA = homeadvantage
		self.Age = Age
		self.spi = spi

all_teams = [
	# group A
	CompactTeamData("Brazil", "BR", "A", 2110, 1125, 440500000 / 19.0, 27.60, SPI(91.7, 3.4, 0.5), homeadvantage=1.0),
	CompactTeamData("Croatia", "HR", "A", 1779, 966, 193200000 / 22.0, 27.60, SPI(75.0, 1.7, 0.9)),
	CompactTeamData("Mexico", "MX", "A", 1784, 887, 39250000 / 18.0, 27.80, SPI(76.7, 1.6, 0.7)),
	CompactTeamData("Cameroon", "CM", "A", 1593, 626, 114300000 / 23.0, 26.80, SPI(71.0, 1.5, 1.0)),
	# group B
	CompactTeamData("Spain", "ES", "B", 2082, 1506, 577000000 / 21.0, 28.0, SPI(89.3, 2.8, 0.5)),
	CompactTeamData("Netherlands", "NL", "B", 1979, 1122, 197000000 / 24.0, 26.10, SPI(82.4, 2.4, 0.9)),
	CompactTeamData("Chile", "CL", "B", 1896, 1038, 142850000 / 24.0, 28.20, SPI(87.1, 2.7, 0.7)),
	CompactTeamData("Australia", "AU", "B", 1711, 576, 25550000 / 23.0, 26.40, SPI(69.9, 1.7, 1.3)),
	# group C
	CompactTeamData("Colombia", "CO", "C", 1912, 1211, 194550000 / 26.0, 27.70, SPI(86.0, 2.2, 0.4)),
	CompactTeamData("Greece", "GR", "C", 1813, 1084, 80400000 / 22.0, 28.70, SPI(76.1, 1.4, 0.6)),
	CompactTeamData("Ivory Coast", "CI", "C", 1786, 841, 142900000 / 26.0, 27.30, SPI(79.2, 2.3, 1.0)),
	CompactTeamData("Japan", "JP", "C", 1747, 601, 91700000 / 22.0, 26.90, SPI(72.9, 1.9, 1.2)),
	# group D
	CompactTeamData("Uruguay", "UY", "D", 1898, 1157, 154925000 / 21.0, 28.30, SPI(84.0, 2.4, 0.7)),
	CompactTeamData("Costa Rica", "CR", "D", 1700, 734, 30200000 / 22.0, 26.70, SPI(76.7, 1.4, 0.6)),
	CompactTeamData("England", "EN", "D", 1906, 1032, 387500000 / 30.0, 26.60, SPI(83.1, 2.2, 0.7)),
	CompactTeamData("Italy", "IT", "D", 1887, 1135, 339000000 / 26.0, 27.90, SPI(80.9, 2.1, 0.8)),
	# group E
	CompactTeamData("Switzerland", "CH", "E", 1822, 1159, 171000000 / 21.0, 26.10, SPI(77.3, 2.0, 1.0)),
	CompactTeamData("Ecuador", "EC", "E", 1816, 831, 54550000 / 20.0, 27.90, SPI(81.7, 2.0, 0.7)),
	CompactTeamData("France", "FR", "E", 1855, 917, 447500000 / 25.0, 26.60, SPI(85.2, 2.4, 0.6)),
	CompactTeamData("Honduras", "HN", "E", 1664, 716, 18400000 / 23.0, 27.50, SPI(73.3, 1.7, 1.0)),
	# group F
	CompactTeamData("Argentina", "AR", "F", 1994, 1255, 423500000 / 22.0, 27.50, SPI(90.3, 2.9, 0.4), homeadvantage=0.5),
	CompactTeamData("Bosnia and Herzegovina", "BA", "F", 1758, 919, 112000000 / 22.0, 26.80, SPI(79.4, 2.3, 1.0)),
	CompactTeamData("Iran", "IR", "F", 1719, 729, 30700000 / 34.0, 27.70, SPI(70.7, 1.4, 1.0)),
	CompactTeamData("Nigeria", "NG", "F", 1718, 616, 88650000 / 23.0, 24.80, SPI(75.9, 1.7, 0.9)),
	# group G
	CompactTeamData("Germany", "DE", "G", 2060, 1314, 400000000 / 19.0, 26.80, SPI(88.7, 3.1, 0.7)),
	CompactTeamData("Portugal", "PT", "G", 1905, 1219, 258250000 / 22.0, 27.80, SPI(79.5, 2.1, 0.9)),
	CompactTeamData("Ghana", "GH", "G", 1700, 733, 97200000 / 21.0, 25.50, SPI(76.1, 1.9, 1.0)),
	CompactTeamData("USA", "US", "G", 1841, 1044, 28750000 / 23.0, 28.00, SPI(77.5, 2.1, 1.0)),
	# group H
	CompactTeamData("Belgium", "BE", "H", 1807, 1117, 341450000 / 22.0, 26.50, SPI(80.7, 2.1, 0.8)),
	CompactTeamData("Algeria", "DZ", "H", 1582, 819, 54000000 / 28.0, 27.10, SPI(63.1, 1.1, 1.2)),
	CompactTeamData("Russia", "RU", "H", 1819, 862, 193600000 / 25.0, 27.60, SPI(79.0, 1.7, 0.7)),
	CompactTeamData("Korea Republic", "KR", "H", 1683, 556, 52500000 / 22.0, 25.50, SPI(73.4, 1.7, 1.0))
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
session.add(ScoreType("SPI Off", "ESPN SPI Offensive Rating", long_name="SPI Offensive Rating"))
session.add(ScoreType("SPI Def", "ESPN SPI Defensive Rating", long_name="SPI Defensive Rating"))

# add certain custom parameters
custom_rule_parameter = RuleParameterType("normalization_constant", 10.0)
session.add(custom_rule_parameter)

# add default ELO calculation rule
elo_rule = RuleType("ELO", "Calculation using the ELO score.", "elo_binary")
elo_rule.makeDefaultRule(1.0)
session.add(elo_rule)

spi_rule = RuleType("SPI", "Calculation based on ESPN's Soccer-Power-Index", "spi_binary")
spi_rule.makeDefaultRule(1.0)
session.add(spi_rule)

fifa_rule = RuleType("FIFA", "Calculation using the FIFA ranking.", "fifa_binary")
fifa_rule.makeDefaultRule(0.5)
session.add(fifa_rule)

value_rule = RuleType("Value", "Calculation based on average player value.", "value_binary")
value_rule.makeDefaultRule(0.25)
session.add(value_rule)

ha_rule = RuleType("HA", "Adjust the win expectancy based on the home-advantage.", "homeadvantage_binary", long_name="Home-advantage", is_backref_rule=True)
ha_rule.makeDefaultRule(1.0)
session.add(ha_rule)

age_rule = RuleType("Age", "Calculation based on average age.", "age_binary")
age_rule.makeDefaultRule(0.0)
session.add(age_rule)

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
spi_off = session.query(ScoreType).filter_by(name="SPI Off").first()
spi_def = session.query(ScoreType).filter_by(name="SPI Def").first()
assert elo != None
assert fifa != None
assert value != None
assert age != None
assert ha != None
assert custom != None
assert spi_off != None
assert spi_def != None

elo_rule.addScoreType(elo, session)
fifa_rule.addScoreType(fifa, session)
value_rule.addScoreType(value, session)
age_rule.addScoreType(age, session)
ha_rule.addScoreType(ha, session)

custom_rule.addScoreType(custom, session)
custom_rule.addParameterType(custom_rule_parameter, session)

spi_rule.addScoreType(spi_off, session)
spi_rule.addScoreType(spi_def, session)



# and finish the team setup
for team_data in all_teams:
	team = session.query(Team).filter_by(country_code=team_data.country_code).first()
	assert team != None
	
	session.add(Score(elo.id, team.id, team_data.ELO))
	session.add(Score(fifa.id, team.id, team_data.FIFA))
	session.add(Score(value.id, team.id, team_data.Value))
	session.add(Score(age.id, team.id, team_data.Age))
	session.add(Score(ha.id, team.id, team_data.HA))
	session.add(Score(spi_off.id, team.id, team_data.spi.off_rating))
	session.add(Score(spi_def.id, team.id, team_data.spi.def_rating))

session.commit()
print "..done"
cleanupSession()
