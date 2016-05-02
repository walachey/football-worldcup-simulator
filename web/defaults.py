import pandas
import numpy as np

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
	HA = 0.0 # home advantage
	spi = None
	
	def __init__(self, name, country_code, group, ELO, FIFA, Value_in_mio, spi, homeadvantage=0.0):
		self.name = name
		self.country_code = country_code
		self.group = group
		self.ELO = ELO
		self.FIFA = FIFA
		self.Value = Value_in_mio * 1000000
		self.HA = homeadvantage
		self.spi = spi

# Read data from table into the team data class.
# This is just a helper to allow easy editing (compared to editing the constructors below).
# This would also be extremely easy to extend to allow a custom data source.
# (Which could even be an URL, thanks to pandas.)
teamdata_df = pandas.read_excel("TeamData.xlsx")
all_teams = []

for row in teamdata_df.iterrows():
	row = row[1]
	team = CompactTeamData(
		name = row["Team"],
		country_code = row["CC"],
		group = row["Group"],
		ELO = row["ELO"],
		FIFA = row["FIFA"],
		Value_in_mio = row["Value"],
		spi = SPI(
				rating = row["SPI_power"], 
				off_rating = row["SPI_off"], 
				def_rating = row["SPI_def"]
				),
		homeadvantage = row["HA"]
		)
	all_teams.append(team)

if not args.update:
	# first step: insert teams into DB to get the IDs
	for team_data in all_teams:
		team = Team(team_data.name, team_data.country_code)
		session.add(team)
	# add new rating score types
	session.add(ScoreType("ELO", "The ELO rating known from chess.", long_name="Elo rating"))
	session.add(ScoreType("FIFA", "FIFA ranking points", long_name="FIFA rating"))
	session.add(ScoreType("Value", "Average value of the players in Euro", long_name="&#216; value in &euro;"))
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
ha = session.query(ScoreType).filter_by(name="HA").first()
custom = session.query(ScoreType).filter_by(name="Custom").first()
spi_off = session.query(ScoreType).filter_by(name="SPI Off").first()
spi_def = session.query(ScoreType).filter_by(name="SPI Def").first()
assert elo != None
assert fifa != None
assert value != None
assert ha != None
assert custom != None
assert spi_off != None
assert spi_def != None

if not args.update:
	elo_rule.addScoreType(elo, session)
	fifa_rule.addScoreType(fifa, session)
	value_rule.addScoreType(value, session)
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
		if np.isnan(score):
			score = 0.0
		session.add(Score(type.id, team.id, score))
	def update(type, score):
		if np.isnan(score):
			score = 0.0
		session.query(Score).filter_by(type_id=type.id,tournament_id=None,team_id=team.id).first().value = score
	if not args.update:
		fun = add
	else:
		fun = update
		
	fun(elo, team_data.ELO)
	fun(fifa, team_data.FIFA)
	fun(value, team_data.Value)
	fun(ha, team_data.HA)
	fun(spi_off, team_data.spi.off_rating)
	fun(spi_def, team_data.spi.def_rating)
	
	
session.commit()
print "..done"
cleanupSession()
