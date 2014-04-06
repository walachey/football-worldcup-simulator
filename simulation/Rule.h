#ifndef _RULE_H
#define _RULE_H

#include "json.h"
#include "Team.h"

#include <vector>
#include <string>

namespace sim
{

class Rule
{
public:
	Rule(json_spirit::Object &data);
	~Rule();
	void setupNeededScores(json_spirit::Array &data);
	void setupParameters(json_spirit::Object &data);
	union {
		double customNormalizationConstant; // shortcut for the calc_custom_binary rule
	};
	std::map<std::string, double> ruleParameters;
	std::vector<std::string> neededScores;
	double weight;
	bool isBackrefRule; // whether the rule needs the win expectancy of other rules as its input

	// returns unweighted results
	double getRawResults(Team &left, Team &right, double *weight, double *currentWinExpectancy);


	void setCalculationFunction(std::string functionName);

private:
	double (Rule::*calculationFunction) (Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_elo_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_fifa_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_value_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_age_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_homeadvantage_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_custom_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy);
	double calc_luck_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy) { return 0.5; };
	double calc_dummy(Team &left, Team &right, double *weight, double *currentWinExpectancy) { return 0.5; };
};

}
#endif