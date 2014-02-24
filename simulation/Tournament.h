#ifndef _TOURNAMENT_H
#define _TOURNAMENT_H

#include "stdafx.h"
#include "Team.h"
#include "Match.h"

#include <list>

namespace sim
{

class Simulation;

class Tournament
{
public:
	Tournament(Simulation *sim, int runs) : simulation(sim), remainingRuns(runs) { init(); };
	~Tournament();

	Simulation *simulation;

	int remainingRuns;
	// maps the team id against a result object that aggregates the results
	std::map<int, TeamResult> teamResults;
	// just collects all results from matches
	std::list<MatchResult> matchResults;
	void addMatchResult(MatchResult &result) { matchResults.push_back(result); }
	// starts the tournament. Called asynchronously
	void start();

	// returns a new tournament of the specified type using the additional arguments as arguments for the constructor
	static Tournament* newOfType(std::string type, Simulation *sim, int runs);
	// after all matches have been played, extract team results
	void calculateTeamResults();
private:
	// initializes certain values and prepares for the runs
	void init();
	// executes one tournament run
	virtual void execRun() = 0;
};


class OneVersusOneTournament : public Tournament
{
public:
	OneVersusOneTournament(Simulation *sim, int runs) : Tournament(sim, runs) {}
private:
	virtual void execRun();
};

}
#endif