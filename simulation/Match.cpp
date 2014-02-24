#include "stdafx.h"
#include "Match.h"
#include "Simulation.h"

#include <random>
#include <chrono>

namespace sim
{

Match::Match()
{
}


Match::~Match()
{
}


MatchResult Match::execute(Simulation *simulation, Team &left, Team &right)
{
	static unsigned SEED = std::chrono::system_clock::now().time_since_epoch().count();
	++SEED;
	// apply all rules to figure out the correct odds
	double weightedChanceSum = 0.0;
	double weightTotalSum = 0.0;

	for (auto &rule : simulation->rules)
	{
		weightedChanceSum += rule.weight * rule.getRawResults(left, right);
		weightTotalSum += rule.weight;
	}
	
	double chanceLeftVsRight = weightedChanceSum / weightTotalSum;
	// for now, make up results..
	int teams[] = {left.id, right.id};
	int goals[] = {0, 0};
	int places[] = {1, 2, 100};

	int possibleGoals = 6;
	auto goalRoller = std::bind(std::uniform_int_distribution<int>(0,1), std::mt19937(SEED));
	auto sideRoller = std::bind(std::uniform_real_distribution<double>(0.0,1.0), std::mt19937(SEED));
	while (--possibleGoals)
	{
		if (goalRoller() == 0) continue;
		
		if (sideRoller() < chanceLeftVsRight)
			goals[0]++;
		else goals[1]++;
	}

	return MatchResult(teams, goals, places);
}

}; // namespace sim