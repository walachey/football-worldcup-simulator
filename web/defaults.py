from database_models import db
from database_models import Team
from database_models import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--update", help="only update existing scores", action="store_true")
args = parser.parse_args()

if args.update:
    print "...only doing an update"
else:
	print "...clearing and re-filling DB" 
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
	
	def __init__(self, name, country_code, group, ELO, FIFA, Value_in_mio, Age, spi, homeadvantage=0.0):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO
		self.FIFA = FIFA
		self.Value = Value_in_mio * 1000000
		self.HA = homeadvantage
		self.Age = Age
		self.spi = spi

all_teams = [
	# group A
	CompactTeamData("Brazil", "BR", "A", 2113, 1242, 467.50 / 23.0, 28.40, SPI(91.7, 3.4, 0.5), homeadvantage=1.0),
	CompactTeamData("Croatia", "HR", "A", 1787, 903, 193.25 / 23.0, 27.20, SPI(75.1, 1.7, 0.9)),
	CompactTeamData("Mexico", "MX", "A", 1820, 882, 96.55 / 23.0, 27.30, SPI(76.7, 1.6, 0.7)),
	CompactTeamData("Cameroon", "CM", "A", 1602, 558, 118.45 / 23.0, 26.90, SPI(71.0, 1.5, 1.0)),
	# group B
	CompactTeamData("Spain", "ES", "B", 2086, 1485, 622.0 / 23.0, 28.3, SPI(89.4, 2.8, 0.5)),
	CompactTeamData("Netherlands", "NL", "B", 1959, 981, 207.5 / 23.0, 26.5, SPI(82.3, 2.4, 0.9)),
	CompactTeamData("Chile", "CL", "B", 1895, 1026, 139.30 / 23.0, 28.00, SPI(87.3, 2.8, 0.7), homeadvantage=0.0),
	CompactTeamData("Australia", "AU", "B", 1699, 526, 21.35 / 23.0, 26.40, SPI(70.1, 1.7, 1.3)),
	# group C
	CompactTeamData("Colombia", "CO", "C", 1897, 1137, 190.20 / 23.0, 27.90, SPI(86.2, 2.2, 0.4), homeadvantage=0.0),
	CompactTeamData("Greece", "GR", "C", 1796, 1064, 79.90 / 23.0, 28.50, SPI(76.0, 1.4, 0.6)),
	CompactTeamData("Ivory Coast", "CI", "C", 1778, 809, 121.70 / 23.0, 27.80, SPI(79.2, 2.3, 1.0)),
	CompactTeamData("Japan", "JP", "C", 1753, 626, 98.0 / 23.0, 27.20, SPI(72.7, 1.9, 1.2)),
	# group D
	CompactTeamData("Uruguay", "UY", "D", 1895, 1147, 217.63 / 23.0, 28.50, SPI(84.1, 2.4, 0.7), homeadvantage=0.0),
	CompactTeamData("Costa Rica", "CR", "D", 1707, 762, 29.63 / 23.0, 27.50, SPI(76.8, 1.4, 0.6)),
	CompactTeamData("England", "EN", "D", 1914, 1090, 334.0 / 23.0, 26.60, SPI(83.1, 2.2, 0.7)),
	CompactTeamData("Italy", "IT", "D", 1879, 1104, 323.0 / 23.0, 27.90, SPI(81.0, 2.1, 0.8)),
	# group E
	CompactTeamData("Switzerland", "CH", "E", 1820, 1149, 178.0 / 23.0, 26.10, SPI(77.3, 2.0, 1.0)),
	CompactTeamData("Ecuador", "EC", "E", 1813, 791, 62.85 / 23.0, 27.80, SPI(82.1, 2.0, 0.7), homeadvantage=0.0),
	CompactTeamData("France", "FR", "E", 1869, 913, 441.75 / 23.0, 27.1, SPI(85.2, 2.4, 0.6)),
	CompactTeamData("Honduras", "HN", "E", 1642, 731, 21.15 / 23.0, 28.50, SPI(73.4, 1.7, 1.0)),
	# group F
	CompactTeamData("Argentina", "AR", "F", 1989, 1175, 391.50 / 23.0, 28.90, SPI(90.3, 2.9, 0.4), homeadvantage=0.5),
	CompactTeamData("Bosnia and Herzegovina", "BA", "F", 1751, 873, 114.95 / 23.0, 27.10, SPI(79.5, 2.3, 1.0)),
	CompactTeamData("Iran", "IR", "F", 1695, 641, 24.10 / 23.0, 28.10, SPI(70.7, 1.4, 1.0)),
	CompactTeamData("Nigeria", "NG", "F", 1719, 640, 86.85 / 23.0, 25.80, SPI(75.9, 1.7, 0.9)),
	# group G
	CompactTeamData("Germany", "DE", "G", 2046, 1300, 562.0 / 23.0, 26.30, SPI(88.7, 3.1, 0.7)),
	CompactTeamData("Portugal", "PT", "G", 1902, 1189, 297.25 / 23.0, 28.50, SPI(79.6, 2.1, 0.9)),
	CompactTeamData("Ghana", "GH", "G", 1687, 704, 96.35 / 23.0, 25.40, SPI(76.1, 1.9, 1.0)),
	CompactTeamData("USA", "US", "G", 1832, 1035, 57.80 / 23.0, 27.80, SPI(77.7, 2.1, 1.0)),
	# group H
	CompactTeamData("Belgium", "BE", "H", 1824, 1074, 348.00 / 23.0, 26.0, SPI(80.8, 2.1, 0.8)),
	CompactTeamData("Algeria", "DZ", "H", 1609, 858, 57.20 / 23.0, 26.60, SPI(62.9, 1.1, 1.2)),
	CompactTeamData("Russia", "RU", "H", 1821, 893, 183.80 / 23.0, 28.0, SPI(78.9, 1.7, 0.7)),
	CompactTeamData("Korea Republic", "KR", "H", 1673, 547, 51.93 / 23.0, 26.0, SPI(73.5, 1.7, 1.0))
	]

if not args.update:
	# first step: insert teams into DB to get the IDs
	for team_data in all_teams:
		team = Team(team_data.name, team_data.country_code)
		session.add(team)
	# add new rating score types
	session.add(ScoreType("ELO", "The ELO rating known from chess.", long_name="Elo rating"))
	session.add(ScoreType("FIFA", "FIFA ranking points", long_name="FIFA rating"))
	session.add(ScoreType("Value", "Average value of the players in Euro", long_name="&#216; value in &euro;"))
	session.add(ScoreType("Age", "Average age of the team", long_name="&#216; age"))
	session.add(ScoreType("HA", "Home advantage of the team", long_name="Home advantage"))
	session.add(ScoreType("Custom", "User-defined custom rating", long_name="Custom rating", hidden=True))
	session.add(ScoreType("SPI Off", "ESPN SPI Offensive Rating", long_name="SPI Offensive Rating"))
	session.add(ScoreType("SPI Def", "ESPN SPI Defensive Rating", long_name="SPI Defensive Rating"))

	# add certain custom parameters
	custom_rule_parameter = RuleParameterType("normalization_constant", 10.0)
	session.add(custom_rule_parameter)

	session.add(RuleParameterType("simulation_run_count", 1))
	session.add(RuleParameterType("use_match_database", 1))

	# add default ELO calculation rule
	elo_rule = RuleType("ELO", "Calculation using the Elo rating", "elo_binary", long_name="Elo")
	elo_rule.makeDefaultRule(1.0)
	session.add(elo_rule)

	spi_rule = RuleType("SPI", "Calculation based on ESPN's Soccer Power Index", "spi_binary")
	spi_rule.makeDefaultRule(1.0)
	session.add(spi_rule)

	fifa_rule = RuleType("FIFA", "Calculation using the FIFA ranking", "fifa_binary")
	fifa_rule.makeDefaultRule(0.5)
	session.add(fifa_rule)

	value_rule = RuleType("Value", "Calculation based on average player market value", "value_binary")
	value_rule.makeDefaultRule(0.25)
	session.add(value_rule)

	ha_rule = RuleType("HA", "Adjust the win expectancy based on the home advantage", "homeadvantage_binary", long_name="Home advantage", is_backref_rule=True)
	ha_rule.makeDefaultRule(1.0)
	session.add(ha_rule)

	age_rule = RuleType("Age", "Calculation based on average age", "age_binary")
	age_rule.makeDefaultRule(0.0)
	session.add(age_rule)

	luck_rule = RuleType("Luck", "Each team has the same probability of winning", "luck_binary")
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

if not args.update:
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
	
	fun = None
	def add(type, score):
			session.add(Score(type.id, team.id, score))
	def update(type, score):
			session.query(Score).filter_by(type_id=type.id,tournament_id=None,team_id=team.id).first().value = score
	if not args.update:
		fun = add
	else:
		fun = update
		
	fun(elo, team_data.ELO)
	fun(fifa, team_data.FIFA)
	fun(value, team_data.Value)
	fun(age, team_data.Age)
	fun(ha, team_data.HA)
	fun(spi_off, team_data.spi.off_rating)
	fun(spi_def, team_data.spi.def_rating)
	
	
session.commit()
print "..done"
cleanupSession()
