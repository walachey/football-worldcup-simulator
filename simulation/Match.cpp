#include "stdafx.h"
#include "Match.h"
#include "Simulation.h"

#include <random>

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


MatchResult Match::execute(int bofRound, std::string cluster, Simulation *simulation, Team &left, Team &right, bool forceWinner)
{
	// firstly, check whether the match already exists in the known match database
	if (simulation->knownMatchResults.count(bofRound))
	{
		for (auto &knownResult : simulation->knownMatchResults[bofRound])
		{
			if ((knownResult.teams[0] == left.id && knownResult.teams[1] == right.id)
				|| (knownResult.teams[0] == right.id && knownResult.teams[1] == left.id))
			{
				int teams[2] = { knownResult.teams[0], knownResult.teams[1] };
				int goals[2] = { knownResult.goals[0], knownResult.goals[1] };
				// make sure to keep the exact order as the normal simulation would, though
				if (teams[0] != left.id)
				{
					std::swap(teams[0], teams[1]);
					std::swap(goals[0], goals[1]);
				}
				return MatchResult(knownResult.bofRound, cluster, teams, goals, knownResult.hadOvertime);
			}
		}
	}

	// if not in the known matches, we will have to simulate the match:

	// use two chances for scoring - some rules are not necessarily symmetrical and should still work as good as possible
	double chanceLeftVsRight(0.0), chanceRightVsLeft(0.0);
	// the maximum weight of the normal rules. Used to scale backreferencing rules correctly
	double maxRuleWeight = 0.0;
	// apply all normal rules to figure out the correct odds
	for (int i = 0; i < 2; ++i)
	{
		double weightedChanceSum = 0.0;
		double weightTotalSum = 0.0;

		for (auto &rule : simulation->rules)
		{
			// remember for backref rules later. Not only the weight of non-backref rules!
			maxRuleWeight = std::max(maxRuleWeight, rule.weight);

			if (rule.isBackrefRule) continue;
			// rules can scale down their weight for one calculation if they cannot make good predictions anyway
			double customWeight(1.0);
			// apply!
			double ruleChance = rule.getRawResults(i == 0 ? left : right, i == 0 ? right : left, &customWeight, nullptr);
			weightedChanceSum += customWeight * rule.weight * ruleChance;
			weightTotalSum += customWeight * rule.weight;
		}

		double chance = 0.0;
		if (weightTotalSum > 0.0)
		{
			chance = weightedChanceSum / weightTotalSum;
		}

		if (i == 0)
			chanceLeftVsRight = chance;
		else
			chanceRightVsLeft = chance;
	}

	// this can happen if a rule reduces its custom weight to 0
	if ((chanceLeftVsRight == 0.0 && chanceRightVsLeft == 0.0) || !std::isfinite(chanceLeftVsRight) || !std::isfinite(chanceRightVsLeft))
	{
		chanceLeftVsRight = chanceRightVsLeft = 0.5;
	}

	// now apply all backreference rules
	assert(maxRuleWeight != 0.0);

	for (int i = 0; i < 2; ++i)
	{
		double *currentWinExpectancy = (i == 0) ? &chanceLeftVsRight : &chanceRightVsLeft;

		for (auto &rule : simulation->rules)
		{
			if (!rule.isBackrefRule) continue;
			double customWeight(1.0);
			double adjustedWinExpectancy = rule.getRawResults(i == 0 ? left : right, i == 0 ? right : left, &customWeight, currentWinExpectancy);
			// now scale the rule correctly, according to the user input
			double ruleFactor = std::min(1.0, rule.weight * customWeight / maxRuleWeight);
			*currentWinExpectancy = ruleFactor * adjustedWinExpectancy + (1.0 - ruleFactor) * (*currentWinExpectancy);
		}
	}

	assert(!(chanceLeftVsRight == 0.0 && chanceRightVsLeft == 0.0));

	// currently some rules might be assymetric (because they include draws f.e.)
	// to make sure that we do a fair roll later, normalize the chances..
	// Note that in case chanceLeftVsRight + chanceRightvsLeft == 1.0, this does nothing
	double normalizedChanceLeftVsRight = chanceLeftVsRight / (chanceLeftVsRight + chanceRightVsLeft);
	// std::cerr << "norm: " << normalizedChanceLeftVsRight << "\tleft: " << chanceLeftVsRight << "\tright: " << chanceRightVsLeft << std::endl;

	int teams[] = {left.id, right.id};
	int goals[] = {0, 0};
	int winnerIndex = -1;

	std::random_device seeder;
	auto leftSideGoalRoller = std::bind(std::poisson_distribution<>(1.8 * (normalizedChanceLeftVsRight) + 0.27), std::mt19937(simulation->randomSeed + seeder()));
	auto rightSideGoalRoller = std::bind(std::poisson_distribution<>(1.8 * (1.0 - normalizedChanceLeftVsRight) + 0.27), std::mt19937(simulation->randomSeed + seeder()));
	auto uniformRoller = std::bind(std::uniform_real_distribution<double>(0.0, 1.0), std::mt19937(simulation->randomSeed + seeder()));

	bool hadOvertime = false;

	// roll for draws first
	// 0.33 * exp(-(x - 0.5) ^ 2 / (2 * 0.28 ^ 2))
	double chanceForDraw = (1.0 / 3.0) * std::exp(-std::pow((normalizedChanceLeftVsRight - 0.5), 2.0) / (2.0 * std::pow(0.28, 2.0)));

	/*
	// This can be used to get raw prediction probabilities from matches.
	// I used it to get them when controlling the simulator from python.
	// This is borderline hacky - the 'best' way would be to just integrate that into the normal interface.
	std::cerr << left.id << "\t" << right.id << "\t" << normalizedChanceLeftVsRight << "\t" << chanceForDraw << "\t" << (1.0 - normalizedChanceLeftVsRight) << std::endl;
	*/

	bool isDraw = false;
	if (uniformRoller() < chanceForDraw)
	{
		if (forceWinner)
			hadOvertime = true;
		else
			isDraw = true;
	}

	if (!isDraw)
	{
		const double winnerSide = uniformRoller();
		if (winnerSide < normalizedChanceLeftVsRight)
			winnerIndex = 0;
		else
			winnerIndex = 1;

		// roll goals until someone wins
		do
		{
			goals[0] = leftSideGoalRoller();
			goals[1] = rightSideGoalRoller();
		} while (goals[winnerIndex] <= goals[1 - winnerIndex]);
	}
	else
	{
		// roll goals until draw
#ifndef NDEBUG
		int safetyCounter = 10000;
#endif
		do
		{
			goals[0] = leftSideGoalRoller();
			goals[1] = rightSideGoalRoller();
#ifndef NDEBUG
			if (--safetyCounter <= 0) break;
#endif
		} while (goals[0] != goals[1]);
		
#ifndef NDEBUG
		if (safetyCounter <= 0)
		{
			std::cerr << "Goal rolling did not terminate!" << std::endl;
			std::cerr << "Chance: " << chanceLeftVsRight << ", C4D: " << chanceForDraw << ", chance: " << (2.0 * (normalizedChanceLeftVsRight)+(1.0 / 3.0)) << std::endl;
			std::cerr << "Current sample: " << goals[0] << ":" << goals[1] << ", winner: " << winnerIndex << std::endl;
			exit(1);
		}
#endif
	}

	assert(!forceWinner || goals[0] != goals[1]);
	return MatchResult(bofRound, cluster, teams, goals, hadOvertime);
}

}; // namespace sim