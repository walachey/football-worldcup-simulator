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
	// prepare result objects
	for (auto team : simulation->teams)
		teamResults.emplace(std::make_pair(team.id, TeamResult()));
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
		return new OneVersusOneTournament(sim, runs);
	std::cerr << "Unknown tournament type: \"" << type << "\"" << std::endl;
	return 0;
}

void Tournament::calculateTeamResults()
{
	// for every match, extract team-based results
	for (auto &match : matchResults)
	{
		for (int teamIndex = 0; teamIndex < 2; ++teamIndex)
		{
			const int &teamID = match.teams[teamIndex];
			TeamResult &result = teamResults[teamID];

			if (match.isWinner(teamIndex))
				result.addWin();
			else if (match.isLoser(teamIndex))
				result.addLoss();
			else result.addDraw();

			// for goal count statistics
			result.addGoals(match.goals[teamIndex], match.goals[1 - teamIndex]);
			// for the general overview
			result.addPlace(match.getPlaceForTeamIndex(teamIndex));
		}
	}
}

void OneVersusOneTournament::execRun()
{
	// get (first) two teams from simulation
	assert(simulation->teams.size() >= 2);
	Team &teamOne = simulation->teams.at(0);
	Team &teamTwo = simulation->teams.at(1);

	MatchResult result(Match::execute(simulation, teamOne, teamTwo));
	addMatchResult(result);
}

}; // namespace sim