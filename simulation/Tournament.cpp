#include "stdafx.h"
#include "Tournament.h"

#include "Simulation.h"
#include "Match.h"

namespace sim
{


Tournament::~Tournament()
{
}

void Tournament::init()
{
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
	if (type == "worldcup") // TODO
		return new FIFAStyleTournament(sim, runs);
	std::cerr << "Unknown tournament type: \"" << type << "\"" << std::endl;
	return 0;
}

void Tournament::calculateTeamResults()
{
	// now calculate team results for the clusters -> local results
	for (auto &cluster : clusterMatchResults)
	{
		std::map<int, TeamResult> &clusterResult = clusterTeamResults[cluster.first];
		
		for (auto &team : simulation->teams)
			clusterResult.emplace(std::make_pair(team.id, TeamResult(cluster.second, team.id)));
	}
}

void OneVersusOneTournament::execRun()
{
	// get (first) two teams from simulation
	assert(simulation->teams.size() >= 2);
	Team &teamOne = simulation->teams.at(0);
	Team &teamTwo = simulation->teams.at(1);

	MatchResult result(Match::execute("all", simulation, teamOne, teamTwo));
	addMatchResult(result);
}

void FIFAStyleTournament::execRun()
{
	assert(simulation->teams.size() == 32);
	// recursive, start with the finals
	runKnockout(1);
}

std::string FIFAStyleTournament::getMatchClusterName(int knockoutStage, int matchNumber)
{
	std::ostringstream os;
	if (knockoutStage > 0)
		os << "BOF" << knockoutStage << "_";
	else os << "QUALI_";
	char matchID = 'A' + matchNumber - 1;
	os << matchID;
	return os.str();
}

std::vector<Team*> FIFAStyleTournament::runQualification()
{
	assert (simulation->teams.size() % 4 == 0);
	std::map<int, FIFAStyleTournamentQualificationResult> results;
	std::vector<Team*> winners;

	// round robin for every 4 teams
	int bracketNumber = 0; // for generating cluster names
	for (size_t i = 0; i < simulation->teams.size(); i += 4)
	{
		++bracketNumber;
		for (size_t t = 0; t < 4; ++t)
		{
			for (size_t opponent = t + 1; opponent < 4; ++opponent)
			{
				Team &teamOne = simulation->teams.at(i + t);
				Team &teamTwo = simulation->teams.at(i + opponent);

				std::string matchCluster = getMatchClusterName(0, bracketNumber);
				MatchResult result(Match::execute(matchCluster, simulation, teamOne, teamTwo, false));
				addMatchResult(result);

				for (size_t resultIndex = 0; resultIndex < 2; ++resultIndex)
				{
					Team &team = (resultIndex == 0) ? teamOne : teamTwo;
					Team &opposingTeam = (resultIndex == 1) ? teamOne : teamTwo;

					if (!results.count(team.id))
						results[team.id] = FIFAStyleTournamentQualificationResult(&team);
					FIFAStyleTournamentQualificationResult &qualiResult = results[team.id];

					qualiResult.goals += result.goals[resultIndex];
					qualiResult.goalDifference += result.goals[resultIndex] - result.goals[1 - resultIndex];
					
					if (result.isWinner(resultIndex))
						qualiResult.score = 3;
					else if (result.isLoser(resultIndex))
						qualiResult.score = 0;
					else qualiResult.score = 1;
				}
			}
		}

		// play-offs for this group are through, now get the winner
		std::list<FIFAStyleTournamentQualificationResult> sortedResults;
		for (auto &mapping : results)
			sortedResults.push_back(mapping.second);
		sortedResults.sort();

		// the top two teams advance into the next stage
		int teamCounter = 0;
		for (auto winningTeam = sortedResults.begin(); teamCounter < 2 && winningTeam != sortedResults.end(); ++i, ++winningTeam)
			winners.push_back(winningTeam->forTeam);
		assert (teamCounter == 2);
	}

	assert (winners.size() == 16);
	return winners;
}

std::vector<Team*> FIFAStyleTournament::runKnockout(int matches)
{
	std::vector<Team*> competingTeams;

	// special treatment for round-of-16
	if (matches == 8)
	{
		// get winners from qualification stage
		competingTeams = runQualification();
	}
	else
	{
		// get winners from last stage
		competingTeams = runKnockout(matches * 2);
	}

	// need an even amount of teams!
	assert (competingTeams.size() % 2 == 0);
	// for every two teams, run another match
	std::vector<Team*> winners;
	// only for generating a match ID
	int matchCount = 0;
	for (size_t i = 0; i < competingTeams.size(); i += 2)
	{
		Team &teamOne = *competingTeams.at(i);
		Team &teamTwo = *competingTeams.at(i + 1);

		std::string matchCluster = getMatchClusterName(matches, ++matchCount);
		MatchResult result(Match::execute(matchCluster, simulation, teamOne, teamTwo, true));
		addMatchResult(result);

		if (result.isWinner(0))
			winners.push_back(&teamOne);
		else
		{
			assert (result.isWinner(1)); // no draws!
			winners.push_back(&teamTwo);
		}
	}
	assert (winners.size() == matches);
	return winners;
}

}; // namespace sim