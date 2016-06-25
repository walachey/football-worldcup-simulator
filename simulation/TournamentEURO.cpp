#include "stdafx.h"
#include "TournamentEURO.h"

#include "Simulation.h"
#include "Match.h"

namespace sim
{

// Used to sort the third places where no between-team-information is available.
bool EUROStyleTournamentQualificationResult::operator<(EUROStyleTournamentQualificationResult &other)
{
	// std::cerr << "score " << this->score << "vs" << other.score << "\tgoaldif " << this->goalDifference << "vs" << other.goalDifference << "\tgoal " << this->goals << "vs" << other.goals << std::endl;
	if (this->score < other.score) return true;
	if (this->score > other.score) return false;

	if (this->goalDifference < other.goalDifference) return true;
	if (this->goalDifference > other.goalDifference) return false;

	if (this->goals < other.goals) return true;
	return false;
}

void EUROStyleTournament::execRun()
{
	assert(simulation->teams.size() == 24);
	// recursive, start with the finals
	runKnockout(1);
}

std::string EUROStyleTournament::getMatchClusterName(int knockoutStage, int matchNumber)
{
	std::ostringstream os;
	if (knockoutStage > 0)
		os << "game_" << knockoutStage << "_" << matchNumber;
	else os << "QUALI_" << (char)('A' + matchNumber - 1);
	return os.str();
}

std::vector<Team*> EUROStyleTournament::runQualification()
{
	assert(simulation->teams.size() % 4 == 0);
	std::vector<Team*> winners;
	std::list<EUROStyleTournamentQualificationResult> thirdPlaces;

	// round robin for every 4 teams
	int bracketNumber = 0; // for generating cluster names
	int matchCounter = 0; // for plausibility
	for (size_t i = 0; i < simulation->teams.size(); i += 4)
	{
		// fresh results for every group
		std::map<int, EUROStyleTournamentQualificationResult> results;
		// Need a team, team -> result map, too, to solve stalemates on points.
		std::map<int, std::map<int, EUROStyleTournamentQualificationResult>> opponentBasedResults;

		++bracketNumber;
		assert(bracketNumber <= 6);
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
						results[team.id] = EUROStyleTournamentQualificationResult(&team, bracketNumber);
					EUROStyleTournamentQualificationResult &qualiResult = results[team.id];

					const int goals = result.goals[resultIndex];
					const int goalDifference = result.goals[resultIndex] - result.goals[1 - resultIndex];
					qualiResult.goals += goals;
					qualiResult.goalDifference += goalDifference;

					opponentBasedResults[team.id][opposingTeam.id] = EUROStyleTournamentQualificationResult(&team, bracketNumber);
					EUROStyleTournamentQualificationResult &qualiResultOpponentBased = opponentBasedResults[team.id][opposingTeam.id];

					if (result.isWinner(resultIndex))
					{
						qualiResult.score += 3;
						qualiResultOpponentBased.score += 3;
					}
					else if (result.isLoser(resultIndex))
					{
						qualiResult.score += 0;
						qualiResultOpponentBased.score += 0;
					}
					else
					{
						qualiResult.score += 1;
						qualiResultOpponentBased.score += 1;
					}
				}
			}
		}

		// play-offs for this group are through, now get the winner
		std::vector<EUROStyleTournamentQualificationResult> sortedResults;
		sortedResults.reserve(results.size());
		for (auto &mapping : results)
			sortedResults.push_back(mapping.second);
		// First, sort by points (descending).
		std::sort(sortedResults.begin(), sortedResults.end(), [](const EUROStyleTournamentQualificationResult & a, const EUROStyleTournamentQualificationResult & b) -> bool { return a.score > b.score; });
		// Then for every draw, resort the subentries in question for the secondary criteria.
		{ // Scope.
			auto resortSubscope = [&](const std::vector<EUROStyleTournamentQualificationResult>::iterator &begin, const std::vector<EUROStyleTournamentQualificationResult>::iterator &end)
			{
				std::sort(begin, end, [&opponentBasedResults](const EUROStyleTournamentQualificationResult & a, const EUROStyleTournamentQualificationResult & b) -> bool
				{
					const Team &teamLeft = *a.forTeam;
					const Team &teamRight = *b.forTeam;
					// Sort by score between the teams in question first (note: this here only looks at two teams at a time. That's a todo.).
					const int teamLeftScore = opponentBasedResults[teamLeft.id][teamRight.id].score;
					const int teamRightScore = opponentBasedResults[teamRight.id][teamLeft.id].score;
					if (teamLeftScore > teamRightScore) return true;
					if (teamLeftScore < teamRightScore) return false;

					// Draw, look at total goal difference next.
					if (a.goalDifference > b.goalDifference) return true;
					if (a.goalDifference < b.goalDifference) return false;

					// Total goals next.
					if (a.goals > b.goals) return true;
					if (a.goals < b.goals) return false;

					// Fair play conduct? Meh.
					return false;
				});
			};
			auto stalemateBegin = sortedResults.begin();
			auto current = std::next(stalemateBegin);

			do
			{
				if (current->score == stalemateBegin->score)
				{
					++current;
					if (current == sortedResults.end())
					{
						resortSubscope(stalemateBegin, current);
						break;
					}
					continue;
				}
				assert(current->score < stalemateBegin->score);
				// Difference in score, need to resort?
				if (std::distance(stalemateBegin, current) == 1)
				{
					stalemateBegin = current;
					++current;
					continue;
				}

				resortSubscope(stalemateBegin, current);
				stalemateBegin = current;
				++current;
			} while (current != sortedResults.end());
		}

		// the top two teams advance into the next stage
		int teamCounter = 0;
		for (auto winningTeam = sortedResults.begin(); teamCounter < 3 && winningTeam != sortedResults.end(); ++teamCounter, ++winningTeam)
		{
			// The top two teams are treated differently.
			if (teamCounter < 2)
				winners.push_back(winningTeam->forTeam);
			else if (teamCounter == 2)
				thirdPlaces.push_back(*winningTeam);
			else
				assert(false);

		}
		assert(teamCounter == 3);
	}

	assert(matchCounter == 3 * 2 * 6);

	// The four best third places are also treated as winners!
	assert(thirdPlaces.size() == 6);
	thirdPlaces.sort();
	thirdPlaces.reverse();
	thirdPlaces.resize(4);
	/*
		This here uses a clever encoding to transfer the match setup table from the UEFA regulations
		(p.15, article 17.03) to a direct mapping.
		We have from before (bracketNumber)
		A = 1, B = 2, C = 3, D = 4, E = 5, F = 6
		We need an (integer) mapping that encodes a combination of those.
		So use i0..4 SUM (1 << Ti - 1) to uniquely encode the combination.
	*/
	unsigned int bestFourTeams = 0;
	for (auto const & team : thirdPlaces)
		bestFourTeams += 1 << (team.group - 1);
	// Now map the setup to a match order.
	enum { A = 0, B = 1, C = 2, D = 3, E = 4, F = 5};
	enum { A_ = 1 << A, B_ = 1 << B, C_ = 1 << C, D_ = 1 << D, E_ = 1 << E, F_ = 1 << F};
	std::vector<int> setup;
	setup.reserve(4);
	switch (bestFourTeams)
	{
	case A_ + B_ + C_ + D_: setup = { C, D, A, B }; break;
	case A_ + B_ + C_ + E_: setup = { C, A, B, E }; break;
	case A_ + B_ + C_ + F_: setup = { C, A, B, F }; break;
	case A_ + B_ + D_ + E_: setup = { D, A, B, E }; break;
	case A_ + B_ + D_ + F_: setup = { D, A, B, F }; break;
	case A_ + B_ + E_ + F_: setup = { E, A, B, F }; break;
	case A_ + C_ + D_ + E_: setup = { C, D, A, E }; break;
	case A_ + C_ + D_ + F_: setup = { C, D, A, F }; break;
	case A_ + C_ + E_ + F_: setup = { C, A, F, E }; break;
	case A_ + D_ + E_ + F_: setup = { D, A, F, E }; break;
	case B_ + C_ + D_ + E_: setup = { C, D, B, E }; break;
	case B_ + C_ + D_ + F_: setup = { C, D, B, F }; break;
	case B_ + C_ + E_ + F_: setup = { E, C, B, F }; break;
	case B_ + D_ + E_ + F_: setup = { E, D, B, F }; break;
	case C_ + D_ + E_ + F_: setup = { C, D, F, E }; break;
	default:
		assert(false);
	}

	// And add the thirds in the correct order to the winners.
	for (size_t i = 0; i < 4; ++i)
	{
		bool found = false;
		for (auto const & team : thirdPlaces)
		{
			if (team.group != setup[i] + 1) continue;
			winners.push_back(team.forTeam);
			found = true;
			break;
		}
		assert(found);
	}

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

	assert(teamPlaceCounter == 8);
	assert(winners.size() == 16);

	// The winners are now sorted like A1, A2, B1, B2, C1, C2, ..., 3C/D/E, 3A/C/D, 3A/B/F, 3B/E/F:
	/*
		idx Winner  Runner-Up
		0   A       A
		2   B       B
		4   C       C
		6   D       D
		8   E       E
		10  F       F
		12  3C/D/E  3A/C/D
		14  3A/B/F  3B/E/F
	*/
	// but for the Euros we need to re-sort them so that teams from the same group will meet only very late in the tournament.
	/*
		Match 1: rA vs rC      1   5
		Match 2: wD vs 3B/E/F  6   15
		Match 3: wB vs 3A/C/D  2   13
		Match 4: wF vs rE      10  9
		Match 5: wC vs 3A/B/F  4   14
		Match 6: wE vs rD      8   7
		Match 7: wA vs 3C/D/E  0   12
		Match 8: rB vs rF      3   11
	*/
	int euroTeamIndexLayout[] = { 1, 5, 6, 15, 2, 13, 10, 9, 4, 14, 8, 7, 0, 12, 3, 11};
	std::vector<Team*> scrambledWinners;
	scrambledWinners.reserve(winners.size());
	for (size_t i = 0; i < winners.size(); ++i)
	{
		const int resortIdx = euroTeamIndexLayout[i];
		Team * const selectedWinner = winners[resortIdx];
		assert(std::find(scrambledWinners.begin(), scrambledWinners.end(), selectedWinner) == scrambledWinners.end());
		scrambledWinners.push_back(selectedWinner);
	}
	assert(scrambledWinners.size() == winners.size());
	return scrambledWinners;
}

std::vector<Team*> EUROStyleTournament::runKnockout(int matches)
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

	// in the semi finals, we will assign both the place '3', because there will not be a deciding match.
	if (isSemiFinal)
	{
		assert(semiFinalists.size() == 2);
		for (Team *team : semiFinalists)
		{
			addTeamPlace(team->id, 3);
			teamPlaceCounter += 1;
		}
	}

	assert(!isFinal || teamPlaceCounter == 2);
	assert(!isSemiFinal || teamPlaceCounter == 2);
	assert((isFinal || isSemiFinal) || (teamPlaceCounter == competingTeams.size() - winners.size()));
	return winners;
}


void EUROStyleTournament::doSanityChecks()
{
	if (simulation->teams.size() != 24)
	{
		std::ostringstream os;
		os << "Tournament has " << simulation->teams.size() << " teams. 24 are expected.\nThe simulation will be stopped.";
		throw os.str();
	}
}

std::vector<RankData> EUROStyleTournament::getRankDataAssignment() const
{
	return
	{
		RankData("first place", 1, 1),
		RankData("second place", 2, 2),
		RankData("third and fourth", 3, 3),
		RankData("rest", 5, 100)
	};
}

} // namespace sim