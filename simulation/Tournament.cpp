#include "stdafx.h"
#include "Tournament.h"

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
	if (type == "worldcup") // TODO
		return new FIFAStyleTournament(sim, runs);
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

	MatchResult result(Match::execute("all", simulation, teamOne, teamTwo, false));
	result.bofRound = 1;
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

bool FIFAStyleTournamentQualificationResult::operator<(FIFAStyleTournamentQualificationResult &other)
{
	// std::cerr << "score " << this->score << "vs" << other.score << "\tgoaldif " << this->goalDifference << "vs" << other.goalDifference << "\tgoal " << this->goals << "vs" << other.goals << std::endl;
	if (this->score < other.score) return true;
	if (this->score > other.score) return false;

	if (this->goalDifference < other.goalDifference) return true;
	if (this->goalDifference > other.goalDifference) return false;

	if (this->goals < other.goals) return true;
	return false;
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
		os << "game_" << knockoutStage << "_" << matchNumber;
	else os << "QUALI_" << (char)('A' + matchNumber - 1);
	return os.str();
}

std::vector<Team*> FIFAStyleTournament::runQualification()
{
	assert (simulation->teams.size() % 4 == 0);
	std::vector<Team*> winners;

	// round robin for every 4 teams
	int bracketNumber = 0; // for generating cluster names
	int matchCounter = 0; // for plausibility
	for (size_t i = 0; i < simulation->teams.size(); i += 4)
	{
		// fresh results for every group
		std::map<int, FIFAStyleTournamentQualificationResult> results;
		++bracketNumber;
		assert(bracketNumber <= 8);
		for (size_t t = 0; t < 4; ++t)
		{
			for (size_t opponent = t + 1; opponent < 4; ++opponent)
			{
				Team &teamOne = simulation->teams.at(i + t);
				Team &teamTwo = simulation->teams.at(i + opponent);
				matchCounter += 1;

				std::string matchCluster = getMatchClusterName(0, bracketNumber);
				MatchResult result(Match::execute(matchCluster, simulation, teamOne, teamTwo, false));
				result.bofRound = 16;
				result.gameInRound = bracketNumber;
				addMatchResult(result);

				for (size_t resultIndex = 0; resultIndex < 2; ++resultIndex)
				{
					Team &team = (resultIndex == 0) ? teamOne : teamTwo;
					Team &opposingTeam = (resultIndex == 0) ? teamTwo : teamOne;

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
		sortedResults.reverse();

		// the top two teams advance into the next stage
		int teamCounter = 0;
		for (auto winningTeam = sortedResults.begin(); teamCounter < 2 && winningTeam != sortedResults.end(); ++teamCounter, ++winningTeam)
			winners.push_back(winningTeam->forTeam);
		assert (teamCounter == 2);
	}

	assert(matchCounter == 3 * 2 * 8);

	// we now have all the winners and thus, the losers
	// assign places to the losers - they are OUT
	int teamPlaceCounter = 0; // for plausibility
	for (auto &team : simulation->teams)
	{
		bool isWinner = std::find(winners.begin(), winners.end(), &team) != winners.end();;

		if (!isWinner)
		{
			addTeamPlace(team.id, Tournament::NoPlace);
			teamPlaceCounter += 1;
		}
	}

	assert(teamPlaceCounter == 16);
	assert (winners.size() == 16);

	// the winners are now sorted like A1, A2, B1, B2, C1, C2, etc..
	// but for the FIFA tournament we need to re-sort them so that teams from the same group will meet only very late in the tournament.
	int fifaTeamIndexLayout[] = {0, 3, 4, 7, 8, 11, 12, 15, 2, 1, 6, 5, 10, 9, 14, 13};
	std::vector<Team*> scrambledWinners;
	scrambledWinners.reserve(winners.size());
	for (size_t i = 0; i < winners.size(); ++i)
		scrambledWinners.push_back(winners[fifaTeamIndexLayout[i]]);
	assert(scrambledWinners.size() == winners.size());
	return scrambledWinners;
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
	// for fighting out the match for the third and fourth place
	const bool isSemiFinal = matches == 2;
	std::vector<Team*> semiFinalists;

	// only for generating a match ID
	int matchCount = 0;
	for (size_t i = 0; i < competingTeams.size(); i += 2)
	{
		Team &teamOne = *competingTeams.at(i);
		Team &teamTwo = *competingTeams.at(i + 1);

		std::string matchCluster = getMatchClusterName(matches, ++matchCount);
		MatchResult result(Match::execute(matchCluster, simulation, teamOne, teamTwo, true));
		result.bofRound = matches;
		result.gameInRound = matchCount;
		addMatchResult(result);

		if (result.isWinner(0))
		{
			winners.push_back(&teamOne);
			if (isSemiFinal) semiFinalists.push_back(&teamTwo);
		}
		else
		{
			assert (result.isWinner(1)); // no draws!
			winners.push_back(&teamTwo);
			if (isSemiFinal) semiFinalists.push_back(&teamOne);
		}
	}
	assert (winners.size() == matches);

	// assign places for teams
	const bool isFinal = matches == 1;
	int teamPlaceCounter = 0; // for plausibility
	if (!isSemiFinal)
	{
		for (auto &team : competingTeams)
		{
			bool isWinner = std::find(winners.begin(), winners.end(), team) != winners.end();

			if (isFinal)
			{
				if (isWinner) addTeamPlace(team->id, 1);
				else addTeamPlace(team->id, 2);

				teamPlaceCounter += 1;
			}
			else if (!isWinner) // neither finals nor semi-finals
			{
				addTeamPlace(team->id, Tournament::NoPlace);
				teamPlaceCounter += 1;
			}
			
		}
	}

	// in the semi finals, we will have to figure out the places with a match again
	if (isSemiFinal)
	{
		assert(semiFinalists.size() == 2);
		Team &teamOne = *semiFinalists.at(0);
		Team &teamTwo = *semiFinalists.at(1);

		std::string matchCluster = getMatchClusterName(1, 2); // second match of the "finale" cluster
		MatchResult result(Match::execute(matchCluster, simulation, teamOne, teamTwo, true));
		result.bofRound = 1;
		result.gameInRound = 2;
		addMatchResult(result);

		if (result.isWinner(0))
		{
			addTeamPlace(teamOne.id, 3);
			addTeamPlace(teamTwo.id, 4);
		}
		else
		{
			assert(!result.isDraw());
			addTeamPlace(teamOne.id, 4);
			addTeamPlace(teamTwo.id, 3);
		}
		teamPlaceCounter += 2;
	}

	assert(!isFinal || teamPlaceCounter == 2);
	assert(!isSemiFinal || teamPlaceCounter == 2);
	assert((isFinal || isSemiFinal) || (teamPlaceCounter == competingTeams.size() - winners.size()));
	return winners;
}

}; // namespace sim