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