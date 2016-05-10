#include "stdafx.h"
#include "TournamentFIFA.h"

#include "Simulation.h"
#include "Match.h"

namespace sim
{

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
	assert(simulation->teams.size() % 4 == 0);
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
				MatchResult result(Match::execute(16, matchCluster, simulation, teamOne, teamTwo, false));
				result.gameInRound = bracketNumber;
				addMatchResult(result);

				for (int resultIndex = 0; resultIndex < 2; ++resultIndex)
				{
					Team &team = (resultIndex == 0) ? teamOne : teamTwo;
					Team &opposingTeam = (resultIndex == 0) ? teamTwo : teamOne;

					if (!results.count(team.id))
						results[team.id] = FIFAStyleTournamentQualificationResult(&team);
					FIFAStyleTournamentQualificationResult &qualiResult = results[team.id];

					qualiResult.goals += result.goals[resultIndex];
					qualiResult.goalDifference += result.goals[resultIndex] - result.goals[1 - resultIndex];

					if (result.isWinner(resultIndex))
						qualiResult.score += 3;
					else if (result.isLoser(resultIndex))
						qualiResult.score += 0;
					else qualiResult.score += 1;
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
		assert(teamCounter == 2);
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
	assert(winners.size() == 16);

	// the winners are now sorted like A1, A2, B1, B2, C1, C2, etc..
	// but for the FIFA tournament we need to re-sort them so that teams from the same group will meet only very late in the tournament.
	int fifaTeamIndexLayout[] = { 0, 3, 4, 7, 8, 11, 12, 15, 2, 1, 6, 5, 10, 9, 14, 13 };
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
	assert(competingTeams.size() % 2 == 0);
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
		MatchResult result(Match::execute(matches, matchCluster, simulation, teamOne, teamTwo, true));
		result.gameInRound = matchCount;
		addMatchResult(result);

		if (result.isWinner(0))
		{
			winners.push_back(&teamOne);
			if (isSemiFinal) semiFinalists.push_back(&teamTwo);
		}
		else
		{
			assert(result.isWinner(1)); // no draws!
			winners.push_back(&teamTwo);
			if (isSemiFinal) semiFinalists.push_back(&teamOne);
		}
	}
	assert(winners.size() == matches);

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
		MatchResult result(Match::execute(1, matchCluster, simulation, teamOne, teamTwo, true));
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


void FIFAStyleTournament::doSanityChecks()
{
	if (simulation->teams.size() != 32)
	{
		std::ostringstream os;
		os << "Tournament has " << simulation->teams.size() << " teams. 32 are expected.\nThe simulation will be stopped.";
		throw os.str();
	}
}

std::vector<RankData> FIFAStyleTournament::getRankDataAssignment() const
{
	return
	{
		RankData("first place", 1, 1),
		RankData("second place", 2, 2),
		RankData("third place", 3, 3),
		RankData("fourth place", 4, 4),
		RankData("rest", 5, 100)
	};
}

} // namespace sim