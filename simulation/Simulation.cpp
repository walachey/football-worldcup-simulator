#include "stdafx.h"
#include "Simulation.h"

#include <thread>
#include <chrono>

namespace sim
{

Simulation *Simulation::singleton = nullptr;

void Simulation::reset()
{
	assert(Simulation::singleton == nullptr);
	Simulation::singleton = this;

	numberOfThreads = 1;
	tournamentID = 0;
	randomSeed = (unsigned int)std::chrono::system_clock::now().time_since_epoch().count();
}

Simulation::Simulation(json_spirit::Value &jsonData)
{
	reset();

	json_spirit::Object jsonObject = jsonData.get_obj();
	
	// It is crucial that the teams are setup before the rules.
	// To achieve that, we just delay rule initialization.
	json_spirit::Array ruleData;

	for (json_spirit::Pair &pair : jsonObject)
	{
		std::string &key = pair.name_;

		if (key == "thread_count") numberOfThreads = pair.value_.get_int();
		else if (key == "run_count") numberOfRuns = pair.value_.get_int();
		else if (key == "tournament_id") tournamentID = pair.value_.get_int();
		else if (key == "tournament_type") tournamentType = pair.value_.get_str();
		else if (key == "teams") setupTeams(pair.value_.get_array());
		else if (key == "rules") ruleData = pair.value_.get_array();
		else if (key == "match_database") setupKnownMatches(pair.value_.get_array());
		else
			std::cerr << "sim::Simulation: invalid property \"" << key << "\"" << std::endl;
	}

	// Finally (after the teams are setup) init the rules.
	if (!ruleData.empty())
		setupRules(ruleData);
}


Simulation::~Simulation()
{
	for (auto &tournament : tournaments)
		delete tournament;
}

void Simulation::setupTeams(json_spirit::Array &teamData)
{
	int teamIndex = 0;
	for (json_spirit::Value &val : teamData)
	{
		teams.push_back(Team(val.get_obj(), teamIndex++));
	}
}

void Simulation::setupRules(json_spirit::Array &ruleData)
{
	for (json_spirit::Value &val : ruleData)
	{
		rules.push_back(Rule(val.get_obj()));
	}
}

void Simulation::setupKnownMatches(json_spirit::Array &matches)
{
	for (json_spirit::Value &val : matches)
	{
		json_spirit::Object &data = val.get_obj();
		int teams[2] = { -1, -1 };
		int goals[2] = { -1, -1 };
		bool hadOvertime = false;
		std::string cluster = "all";
		int bofRound = -1;

		for (json_spirit::Pair &pair : data)
		{
			std::string &key = pair.name_;
			
			if (key == "teams")
			{
				for (int i = 0; i < 2; ++i)
					teams[i] = pair.value_.get_array().at(i).get_int();
			}
			else if (key == "goals")
			{
				for (int i = 0; i < 2; ++i)
					goals[i] = pair.value_.get_array().at(i).get_int();
			}
			else if (key == "bof_round")
			{
				bofRound = pair.value_.get_int();
			}
		}

		assert(bofRound != -1);
		assert(teams[0] != -1);
		assert(goals[0] != -1);
		if (!knownMatchResults.count(bofRound))
			knownMatchResults[bofRound] = std::vector<KnownMatchResult>();
		knownMatchResults[bofRound].push_back(KnownMatchResult(bofRound, cluster, teams, goals, hadOvertime));
	}
}

void Simulation::execute()
{
	// some safety & sanity checks
	if (teams.empty())
	{
		throw "No teams are active. Aborting the tournament.";
	}
	if (rules.empty())
	{
		throw "No rules are active. Aborting the tournament.";
	}

	// 16 threads for one tournament sound impractical
	int realThreadCount = std::min(numberOfThreads, numberOfRuns);

	std::vector<std::thread> threads;
	threads.resize(realThreadCount);
	tournaments.resize(realThreadCount);

	int remainingRuns = numberOfRuns;
	int runsPerThread = numberOfRuns / realThreadCount;

	for (int i = 0; i < realThreadCount; ++i, remainingRuns -= runsPerThread)
	{
		int runsForTournament = std::min(remainingRuns, runsPerThread);
		// make sure that there are no remaining runs that don't get distributed
		// example: 20 runs and 8 threads, runs per thread = 2, only 2*8=16 tournaments would be started
		if (i == realThreadCount - 1)
			runsForTournament = remainingRuns;

		tournaments[i] = Tournament::newOfType(tournamentType, this, runsForTournament);
		tournaments[i]->doSanityChecks(); // allow the tournament some checking prior to the launch
		threads[i] = std::thread(&Tournament::start, tournaments[i]);
	}
	
	// wait for the simulation to finish
	for (auto &thread : threads)
	{
		thread.join();
	}

	// setup rank data
	{ // scope
		std::unique_ptr<Tournament> tournament(Tournament::newOfType(tournamentType, this, 0));
		for (RankData const & rank : tournament->getRankDataAssignment())
			ranks.push_back(rank);
	}

	// and then join the results
	for (Tournament* &tournament : tournaments)
	{
		// first the team data
		for (auto &clusterToMerge : tournament->clusterTeamResults)
		{
			std::map<int, TeamResult> &cluster = clusterTeamResults[clusterToMerge.first];

			for (auto &team : teams)
			{
				if (!cluster.count(team.id))
					cluster.emplace(std::make_pair(team.id, TeamResult(clusterToMerge.second[team.id])));
				else
					cluster[team.id].merge(clusterToMerge.second[team.id]);
			}
		}

		// and then the match cluster statistics
		for (auto &clusterToMerge : tournament->clusterMatchResultStatisticsLists)
		{
			clusterMatchResultStatisticsLists[clusterToMerge.first].merge(clusterToMerge.second);
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

	root.push_back(json_spirit::Pair("matches", json_spirit::Object()));
	json_spirit::Object &matches= root.back().value_.get_obj();
	for (auto &cluster : clusterTeamResults)
	{
		matches.push_back(json_spirit::Pair(cluster.first, json_spirit::Object()));
		json_spirit::Object &match = matches.back().value_.get_obj();

		match.push_back(json_spirit::Pair("teams", json_spirit::Array()));
		json_spirit::Array &teams = match.back().value_.get_array();
		fillTeamResults(teams, cluster.first);

		match.push_back(json_spirit::Pair("results", json_spirit::Array()));
		json_spirit::Array &results = match.back().value_.get_array();
		fillMatchResults(results, cluster.first);

		if (cluster.first != "all")
		{
			match.push_back(json_spirit::Pair("bof_round", clusterMatchResultStatisticsLists[cluster.first].bofRound));
			match.push_back(json_spirit::Pair("game_in_round", clusterMatchResultStatisticsLists[cluster.first].gameInRound));
		}
		else
		{
			match.push_back(json_spirit::Pair("bof_round", 0));
			match.push_back(json_spirit::Pair("game_in_round", 0));
		}
	}

	return root;
}

void Simulation::fillRankResults(json_spirit::Array &ranks)
{
	for (RankData &rankData : this->ranks)
		ranks.push_back(rankData.toJSONObject());
}

void Simulation::fillMatchResults(json_spirit::Array &results, std::string cluster)
{
	results = clusterMatchResultStatisticsLists[cluster].toJSONArray();
}

void Simulation::fillTeamResults(json_spirit::Array &teamList, std::string cluster)
{
	for (auto &team : teams)
	{
		json_spirit::Object teamData;
		teamData.push_back(json_spirit::Pair("id", team.id));
		if (cluster == "all")
		{
			teamData.push_back(json_spirit::Pair("ranks", clusterTeamResults[cluster][team.id].rankDataToJSONArray(ranks)));
			teamData.push_back(json_spirit::Pair("avg_place", clusterTeamResults[cluster][team.id].getAvgPlace()));
		}
		teamData.push_back(json_spirit::Pair("match_data", clusterTeamResults[cluster][team.id].toJSONObject()));
		teamData.push_back(json_spirit::Pair("avg_goals", clusterTeamResults[cluster][team.id].getAvgGoals()));
		
		
		teamList.push_back(teamData);
	}
}

} // namespace sim