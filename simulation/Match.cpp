#include "stdafx.h"
#include "Match.h"
#include "Simulation.h"

#include <random>
#include <chrono>

namespace sim
{

void MatchResultStatisticsList::addMatch(const MatchResult &match)
{
	int teamIDOne = std::min(match.teams[0], match.teams[1]);
	int teamIDTwo = std::max(match.teams[0], match.teams[1]);

	std::pair<int, int> teamPair = std::make_pair(teamIDOne, teamIDTwo);
	if (!results.count(teamPair))
	{
		results.emplace(teamPair, MatchResultStatistics(teamIDOne, teamIDTwo));
		assert(match.bofRound > 0);
		this->bofRound = match.bofRound;
		this->gameInRound = match.gameInRound;
	}
	MatchResultStatistics &clusterResult = results[teamPair];
	clusterResult.addMatch(match);
}

void MatchResultStatisticsList::merge(MatchResultStatisticsList &other)
{
	for (auto &result : other.results)
	{
		const std::pair<int, int> &teamPair = result.first;
		if (!results.count(teamPair))
			results.emplace(teamPair, MatchResultStatistics(result.second));
		else
			results[teamPair].merge(result.second);
	}
	this->bofRound = other.bofRound;
	this->gameInRound = other.gameInRound;
}

json_spirit::Array MatchResultStatisticsList::toJSONArray()
{
	json_spirit::Array data;

	// sort our results by count
	std::list<MatchResultStatistics> sorted;
	for (auto &result : results)
		sorted.push_back(result.second);
	sorted.sort();
	sorted.reverse();

	// ..and add to data
	for (MatchResultStatistics &stats : sorted)
		data.push_back(stats.toJSONObject());

	return data;
}

json_spirit::Object MatchResultStatistics::toJSONObject()
{
	json_spirit::Object object;
	object.push_back(json_spirit::Pair("teams", json_spirit::Array({ teams[0], teams[1] })));
	object.push_back(json_spirit::Pair("goals", json_spirit::Array({ goals[0], goals[1] })));
	object.push_back(json_spirit::Pair("count", count));
	return object;
}

void MatchResultStatistics::addMatch(const MatchResult &result)
{
	int first = 0, second = 1;
	// team IDs will always be sorted ascending
	if (result.teams[0] > result.teams[1])
	{
		first = 1;
		second = 0;
	}
	this->goals[0] += result.goals[first];
	this->goals[1] += result.goals[second];
	count += 1;
}

void MatchResultStatistics::merge(const MatchResultStatistics &other)
{
	assert(this->teams[0] == other.teams[0] && this->teams[1] == other.teams[1]);
	for (int i = 0; i < 2; ++i)
	{
		this->goals[i] += other.goals[i];
	}
	this->count += other.count;
}

Match::Match()
{
}


Match::~Match()
{
}


MatchResult Match::execute(std::string cluster, Simulation *simulation, Team &left, Team &right, bool forceWinner)
{
	static unsigned int SEED = (unsigned int)std::chrono::system_clock::now().time_since_epoch().count();
	++SEED;
	// use two chances for scoring - some rules are not necessarily symmetrical and should still work as good as possible
	double chanceLeftVsRight(0.0), chanceRightVsLeft(0.0);
	// apply all rules to figure out the correct odds
	for (int i = 0; i < 2; ++i)
	{
		double weightedChanceSum = 0.0;
		double weightTotalSum = 0.0;

		for (auto &rule : simulation->rules)
		{
			weightedChanceSum += rule.weight * rule.getRawResults(i == 0 ? left : right, i == 0 ? right : left);
			weightTotalSum += rule.weight;
		}

		if (i == 0)
			chanceLeftVsRight = weightedChanceSum / weightTotalSum;
		else
			chanceRightVsLeft = weightedChanceSum / weightTotalSum;
	}

	assert(!(chanceLeftVsRight == 0.0 && chanceRightVsLeft == 0.0));

	// for now, make up results..
	int teams[] = {left.id, right.id};
	int goals[] = {0, 0};

	int possibleGoals = 4;
	auto goalRoller = std::bind(std::uniform_int_distribution<int>(0,1), std::mt19937(SEED));
	auto sideRoller = std::bind(std::uniform_real_distribution<double>(0.0,1.0), std::mt19937(SEED));
	bool hadOvertime = false;

	for (;possibleGoals >= 0; --possibleGoals)
	{
		if (goalRoller() == 1)
		{
			if (sideRoller() < chanceLeftVsRight)
				goals[0]++;
			if (sideRoller() < chanceRightVsLeft)
				goals[1]++;
		}

		if ((possibleGoals == 0) && forceWinner && (goals[0] == goals[1]))
		{
			possibleGoals = 2;
			hadOvertime = true;
		}
	}

	assert(!forceWinner || goals[0] != goals[1]);
	return MatchResult(cluster, teams, goals, hadOvertime);
}

}; // namespace sim