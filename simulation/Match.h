#ifndef _MATCH_H
#define _MATCH_H

#include "json.h"

namespace sim
{
class Simulation;
class Team;
class MatchResultStatistics;
class Match;
class MatchResult;

class MatchResultStatisticsList
{
public:
	MatchResultStatisticsList() : bofRound(0), gameInRound(0) {}

	std::map<std::pair<int, int>, MatchResultStatistics> results;
	void addMatch(const MatchResult &match);
	void merge(MatchResultStatisticsList &other);

	int bofRound;
	int gameInRound;

	json_spirit::Array toJSONArray();
};

// the aggregated match results from one cluster - every match with the same teams gets a unique MatchClusterResult
class MatchResultStatistics
{
public:
	MatchResultStatistics() : count(0)
	{
		for (size_t i = 0; i < 2; ++i)
		{
			this->teams[i] = 0;
			this->goals[i] = 0;
		}
	}

	MatchResultStatistics(int teamIDOne, int teamIDTwo) : MatchResultStatistics()
	{
		teams[0] = std::min(teamIDOne, teamIDTwo);
		teams[1] = std::max(teamIDOne, teamIDTwo);
	}

	int teams[2];
	int goals[2];
	int count;

	void addMatch(const MatchResult &result);
	// merges two results of the same type that have the exact same teams
	void merge(const MatchResultStatistics &other);

	// for sorting
	bool operator<(MatchResultStatistics &other) { return this->count < other.count; }

	json_spirit::Object toJSONObject();
};

class MatchResult
{
public:
	MatchResult(int bofRound, std::string cluster, int teams[], int goals[], bool hadOvertime) : cluster(cluster), bofRound(bofRound), gameInRound(0), hadOvertime(hadOvertime)
	{
		for (size_t i = 0; i < 2; ++i)
		{
			this->teams[i] = teams[i];
			this->goals[i] = goals[i];
		}
	}
	~MatchResult() {};

	// for statistics pooling, one cluster could f.e. be one match in a tournament ladder
	std::string cluster;
	int bofRound;
	int gameInRound;

	// for FIFA style tournaments, where the score depends on f.e. whether the match had an overtime
	bool hadOvertime;

	int teams[2];
	int goals[2];

	bool isWinner(int index) { return goals[index] > goals[1 - index]; }
	bool isLoser(int index) { return goals[index] < goals[1 - index]; }
	bool isDraw() { return goals[0] == goals[1]; }
};

// when outcomes for certain matches are already known a-priori, those matches do not need to be simulated
class KnownMatchResult : public MatchResult
{
public:
	/*
	replace copy & pasted constructor with the following line, once VS supports constructor inheritance:
	using MatchResult::MatchResult;
	*/
	KnownMatchResult(int bofRound, std::string cluster, int teams[], int goals[], bool hadOvertime) : MatchResult(bofRound, cluster, teams, goals, hadOvertime)
	{
	}

};

class Match
{
public:
	Match();
	~Match();

	static MatchResult execute(int bofRound, std::string cluster, Simulation *simulation, Team &left, Team &right, bool forceWinner);
};

}
#endif