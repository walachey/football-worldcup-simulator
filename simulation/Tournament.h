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
	static int NoPlace;

	Tournament(Simulation *sim, int runs) : simulation(sim), remainingRuns(runs) { init(); };
	virtual ~Tournament();

	Simulation *simulation;

	int remainingRuns;
	// just collects all results from matches
	std::map<std::string, std::list<MatchResult>> clusterMatchResults;
	// special cluster results for tournaments with special qualifiers etc.
	// for every cluster, this maps the team id against a result object that aggregates the results
	std::map<std::string, std::map<int, TeamResult>> clusterTeamResults;
	// aggregates the statistics for a cluster of matches
	std::map<std::string, MatchResultStatisticsList> clusterMatchResultStatisticsLists;
	// every played match should add its outcome
	void addMatchResult(MatchResult &result);
	// and once the place for a team is known, it should be added here, too
	void addTeamPlace(int teamID, int place);
	// Just for the group phase (in a EURO/WC style tournament), we need to remember the average rank for every team.
	// This is just for the interface to be able to sort it later.
	void addGroupPhaseRank(std::string cluster, int teamID, int rank);
	// starts the tournament. Called asynchronously
	void start();

	// returns a new tournament of the specified type using the additional arguments as arguments for the constructor
	static Tournament* newOfType(std::string type, Simulation *sim, int runs);
	// after all matches have been played, extract team results
	void calculateTeamResults();
	// different tournament types can require different setups
	// to catch possible errors with the data transmission, the setup can be checked and the simulation can be aborted here
	virtual void doSanityChecks(){};
	// returns a mapping between the numerical ranks and a semantic representation (e.g. 1 means 'winner' or 100 means 'rest').
	virtual std::vector<RankData> getRankDataAssignment() const = 0;

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
	virtual ~OneVersusOneTournament() {}
	virtual std::vector<RankData> getRankDataAssignment() const override;
private:
	virtual void execRun();
};

}
#endif