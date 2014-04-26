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
	~Tournament();

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
	// starts the tournament. Called asynchronously
	void start();

	// returns a new tournament of the specified type using the additional arguments as arguments for the constructor
	static Tournament* newOfType(std::string type, Simulation *sim, int runs);
	// after all matches have been played, extract team results
	void calculateTeamResults();
	// different tournament types can require different setups
	// to catch possible errors with the data transmission, the setup can be checked and the simulation can be aborted here
	virtual void doSanityChecks(){};
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

// aggregates the score for one team
class FIFAStyleTournamentQualificationResult
{
public:
	FIFAStyleTournamentQualificationResult() : score(0), goals(0), goalDifference(0) {}
	FIFAStyleTournamentQualificationResult(Team *team) : FIFAStyleTournamentQualificationResult()
	{
		this->forTeam = team;
	}
	int score;
	int goals;
	int goalDifference;
	Team *forTeam;

	bool operator<(FIFAStyleTournamentQualificationResult &other);
};

class FIFAStyleTournament : public Tournament
{
public:
	FIFAStyleTournament(Simulation *sim, int runs) : Tournament(sim, runs) {}
	virtual void doSanityChecks();
private:
	virtual void execRun();
	// both functions will return the winner for the current stage
	std::vector<Team*> runKnockout(int matches);
	std::vector<Team*> runQualification();
	// generates a name for clustering and result transmission
	std::string getMatchClusterName(int knockoutStage, int matchNumber);
};

}
#endif