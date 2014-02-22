#include "stdafx.h"
#include "Simulation.h"

#include <thread>

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
	
	for (json_spirit::Pair &pair : jsonObject)
	{
		std::string &key = pair.name_;

		if (key == "thread_count") numberOfThreads = pair.value_.get_int();
		else if (key == "run_count") numberOfRuns = pair.value_.get_int();
		else if (key == "tournament_id") tournamentID = pair.value_.get_int();
		else if (key == "tournament_type") tournamentType = pair.value_.get_str();
		else if (key == "teams") setupTeams(pair.value_.get_array());
		else if (key == "rules") setupRules(pair.value_.get_array());
		else
			std::cerr << "sim::Simulation: invalid property \"" << key << "\"" << std::endl;
	}
}


Simulation::~Simulation()
{
	for (auto &tournament : tournaments)
		delete tournament;
}

void Simulation::setupTeams(json_spirit::Array &teamData)
{
	for (json_spirit::Value &val : teamData)
	{
		teams.push_back(Team(val.get_obj()));
	}
}

void Simulation::setupRules(json_spirit::Array &ruleData)
{
	for (json_spirit::Value &val : ruleData)
	{
		rules.push_back(Rule(val.get_obj()));
	}
}

void Simulation::execute()
{
	std::vector<std::thread> threads;
	threads.resize(numberOfThreads);
	tournaments.resize(numberOfThreads);

	int remainingRuns = numberOfRuns;
	int runsPerThread = numberOfRuns / numberOfThreads;

	for (int i = 0; i < numberOfThreads; ++i, remainingRuns -= runsPerThread)
	{
		int runsForTournament = std::min(remainingRuns, runsPerThread);
		tournaments[i] = Tournament::newOfType(tournamentType, this, runsForTournament);
		threads[i] = std::thread(&Tournament::start, tournaments[i]);
	}
	
	// wait for the simulation to finish
	for (auto &thread : threads)
	{
		thread.join();
	}

	// setup rank data
	ranks.push_back(RankData("winner", 1, 1));
	ranks.push_back(RankData("loser", 2, 2));
	ranks.push_back(RankData("rest", 3, 100));


	// and then join the results
	for (auto &tournament : tournaments)
	{
		for (auto &team : teams)
		{
			if (!teamResults.count(team.id))
				teamResults.emplace(std::make_pair(team.id, TeamResult()));
			teamResults[team.id].merge(tournament->teamResults[team.id]);
		}
	}
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
	for (RankData &rankData : this->ranks)
		ranks.push_back(rankData.toJSONObject());
}

void Simulation::fillTeamResults(json_spirit::Array &teamList)
{
	for (auto &team : teams)
	{
		json_spirit::Object teamData;
		teamData.push_back(json_spirit::Pair("id", team.id));
		teamData.push_back(json_spirit::Pair("ranks", teamResults[team.id].rankDataToJSONArray(ranks)));
		teamData.push_back(json_spirit::Pair("match_data", teamResults[team.id].toJSONObject()));
		teamData.push_back(json_spirit::Pair("avg_goals", teamResults[team.id].getAvgGoals()));
		
		teamList.push_back(teamData);
	}
}

} // namespace sim