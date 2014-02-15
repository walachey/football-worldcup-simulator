#include "stdafx.h"
#include "Simulation.h"

namespace sim
{

void Simulation::reset()
{
	numberOfThreads = 1;
	tournamentID = 0;
}

Simulation::Simulation(json_spirit::Value &jsonData)
{
	reset();

	json_spirit::Object jsonObject = jsonData.get_obj();
	
	for (auto iter = jsonObject.begin(); iter != jsonObject.end(); ++iter)
	{
		std::string &key = iter->name_;

		if (key == "thread_count") numberOfThreads = iter->value_.get_int();
		else if (key == "tournament_id") tournamentID = iter->value_.get_int();
		else if (key == "teams") setupTeams(iter->value_.get_array());
		else if (key == "rules") setupRules(iter->value_.get_array());
		else
			std::cerr << "sim::Simulation: invalid property \"" << key << "\"" << std::endl;
	}
}


Simulation::~Simulation()
{
}

void Simulation::setupTeams(json_spirit::Array &teamData)
{
	for (auto iter = teamData.begin(); iter != teamData.end(); ++iter)
	{
		json_spirit::Value &val = *iter;
		teams.push_back(Team(val.get_obj()));
	}
}

void Simulation::setupRules(json_spirit::Array &ruleData)
{
	for (auto iter = ruleData.begin(); iter != ruleData.end(); ++iter)
	{
		json_spirit::Value &val = *iter;
		rules.push_back(Rule(val.get_obj()));
	}
}

void Simulation::execute()
{

}

json_spirit::Object Simulation::getJSONResults()
{
	json_spirit::Object root;
	root.push_back(json_spirit::Pair("tournament_id", tournamentID));
	
	root.push_back(json_spirit::Pair("ranks", json_spirit::Array()));
	json_spirit::Array &ranks = root.back().value_.get_array();
	fillRankResults(ranks);

	root.push_back(json_spirit::Pair("teams", json_spirit::Array()));
	json_spirit::Array &teams = root.back().value_.get_array();
	fillTeamResults(teams);

	return root;
}

void Simulation::fillRankResults(json_spirit::Array &ranks)
{
	ranks.push_back(RankData("winner").toJSONObject());
	ranks.push_back(RankData("loser").toJSONObject());
}

void Simulation::fillTeamResults(json_spirit::Array &teamList)
{
	double testCounter = 1.0;
	for (auto iter = teams.begin(); iter != teams.end(); ++iter)
	{
		Team &team = *iter;
		json_spirit::Object teamData;
		teamData.push_back(json_spirit::Pair("id", team.id));
		teamData.push_back(json_spirit::Pair("ranks", json_spirit::Array()));
		json_spirit::Array &ranks = teamData.back().value_.get_array();
		
		testCounter *= 0.8;
		ranks.push_back(Result(testCounter).toJSONObject());
		ranks.push_back(Result(1.0 - testCounter).toJSONObject());

		teamList.push_back(teamData);
	}
}

} // namespace sim