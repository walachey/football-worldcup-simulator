#include "stdafx.h"
#include "Tournament.h"
#include "TournamentFIFA.h"
#include "TournamentEURO.h"

#include "Simulation.h"
#include "Match.h"

namespace sim
{

int Tournament::NoPlace = 100;

Tournament::~Tournament()
{
}

void Tournament::init()
{
	//  prepare team results in cluster "all", that way a check when adding a place later can be omitted
	auto &cluster = clusterTeamResults["all"];
	for (auto &team : simulation->teams)
	{
		cluster.emplace(std::make_pair(team.id, TeamResult()));
	}
}

void Tournament::addTeamPlace(int teamID, int place)
{
	clusterTeamResults["all"][teamID].addPlace(place);
}

void Tournament::addMatchResult(MatchResult &result)
{
	// cluster the matches and calculate results based on that, again
	clusterMatchResults[result.cluster].push_back(result);
	if (result.cluster != "all")
		clusterMatchResults["all"].push_back(result);
}

void Tournament::start()
{
#define EXCEPTIONDEBUG
#ifdef EXCEPTIONDEBUG
	try
#endif
	{
		for (int i = 0; i < remainingRuns; ++i)
			execRun();
		calculateTeamResults();
	}
#ifdef EXCEPTIONDEBUG
	catch(const std::runtime_error& re)
	{
		std::cerr << "Runtime error: " << re.what() << std::endl;
		assert (false);
		exit(1);
	}
	catch(const std::exception& ex)
	{
		std::cerr << "Error occurred: " << ex.what() << std::endl;
		assert (false);
		exit(1);
	}
	catch(...)
	{
		std::cerr << "An unexpected error occurred." << std::endl;
		assert (false);
		exit(1);
	}
#endif
#undef EXCEPTIONDEBUG
}

Tournament* Tournament::newOfType(std::string type, Simulation *sim, int runs)
{
	if (type == "1v1")
		return new OneVersusOneTournament(sim, runs);
	if (type == "worldcup")
		return new FIFAStyleTournament(sim, runs);
	if (type == "eurocup")
		return new EUROStyleTournament(sim, runs);
	std::cerr << "Unknown tournament type: \"" << type << "\"" << std::endl;
	return 0;
}

void Tournament::calculateTeamResults()
{
	// quick check over places - for plausibility only
	int totalPlaceCount = 0;
	for (auto &pair : clusterTeamResults["all"])
	{
		totalPlaceCount += pair.second.getTotalPlaceCount();
	}
	assert(totalPlaceCount == remainingRuns * simulation->teams.size());

	// now calculate team results for the clusters -> local results
	for (auto &cluster : clusterMatchResults)
	{
		// first the team results
		std::map<int, TeamResult> &clusterTeamResult = clusterTeamResults[cluster.first];
		
		for (auto &team : simulation->teams)
		{
			// aggregate results from matches
			TeamResult results(cluster.second, team.id);
			// .. and merge into existing team data, which probably already has stuff like places etc. set
			if (clusterTeamResult.count(team.id))
				clusterTeamResult[team.id].merge(results);
			else clusterTeamResult[team.id] = results;
		}

		// and then the single match results
		MatchResultStatisticsList &list = clusterMatchResultStatisticsLists[cluster.first];
		for (auto &match : cluster.second)
			list.addMatch(match);
	}
}

void OneVersusOneTournament::execRun()
{
	// get (first) two teams from simulation
	assert(simulation->teams.size() >= 2);
	Team &teamOne = simulation->teams.at(0);
	Team &teamTwo = simulation->teams.at(1);

	MatchResult result(Match::execute(1, "all", simulation, teamOne, teamTwo, false));
	result.gameInRound = 1;
	addMatchResult(result);

	int places[] = { 1, 2 };
	
	if (result.isLoser(0))
	{
		places[0] = 2;
		places[1] = 1;
	}
	else if (result.isDraw())
	{
		places[0] = 100;
		places[1] = 100;
	}
	addTeamPlace(teamOne.id, places[0]);
	addTeamPlace(teamTwo.id, places[1]);
}

std::vector<RankData> OneVersusOneTournament::getRankDataAssignment() const
{
	return
	{
		RankData("winner", 1, 1),
		RankData("loser", 2, 2),
		RankData("draw", 5, 100)
	};
}


}; // namespace sim