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

	std::vector<std::string> neededScores;
	double weight;

	// returns unweighted results
	double getRawResults(Team &left, Team &right);


	void setCalculationFunction(std::string functionName);

private:
	double (Rule::*calculationFunction) (Team &left, Team &right);
	double calc_elo_binary(Team &left, Team &right);
	double calc_fifa_binary(Team &left, Team &right);
	double calc_value_binary(Team &left, Team &right);
	double calc_homeadvantage_binary(Team &left, Team &right);
	double calc_dummy(Team &left, Team &right) { return 0.5; };
};

}
#endif