#include "stdafx.h"
#include "Rule.h"

namespace sim
{

Rule::Rule(json_spirit::Object &data)
{
	weight = 0.0;

	for (auto iter = data.begin(); iter != data.end(); ++iter)
	for (json_spirit::Pair &pair : data)
	{
		std::string &key = pair.name_;
		if (key == "scores") setupNeededScores(pair.value_.get_array());
		else if (key == "weight") weight = pair.value_.get_real();
		else if (key == "function") setCalculationFunction(pair.value_.get_str());
		else
			std::cerr << "sim::Rule: invalid property \"" << key << "\"" << std::endl;
	}

	if (calculationFunction == nullptr)
		std::cerr << "Rule without calculation function." << std::endl;
}


Rule::~Rule()
{
}

void Rule::setupNeededScores(json_spirit::Array &data)
{
	for (json_spirit::Value &val : data)
	{
		neededScores.push_back(val.get_str());
	}
}

double Rule::getRawResults(Team &left, Team &right, double *weight)
{
	*weight = 1.0;
	return (this->*calculationFunction)(left, right, weight);
}

void Rule::setCalculationFunction(std::string functionName)
{
	if (functionName == "elo_binary")
		calculationFunction = &Rule::calc_elo_binary;
	else if (functionName == "fifa_binary")
		calculationFunction = &Rule::calc_fifa_binary;
	else if (functionName == "value_binary")
		calculationFunction = &Rule::calc_value_binary;
	else if (functionName == "homeadvantage_binary")
		calculationFunction = &Rule::calc_homeadvantage_binary;
	else if (functionName == "luck_binary")
		calculationFunction = &Rule::calc_luck;
	else
	{
		std::cerr << "Unknown calculation function: \"" << functionName << "\"" << std::endl;
		calculationFunction = &Rule::calc_dummy;
	}
}

double Rule::calc_elo_binary(Team &left, Team &right, double *weight)
{
	return 1.0 / (1.0 + std::pow(10.0, (right.scores["ELO"] - left.scores["ELO"]) / 400.0));
}

double Rule::calc_fifa_binary(Team &left, Team &right, double *weight)
{
	const double &leftScore = left.scores["FIFA"];
	const double &rightScore = right.scores["FIFA"];
	const double logScore = std::log(leftScore / rightScore);
	const double result = 1.0 / (1.0 + std::exp(-logScore / 0.23725));
	//std::cerr << "left: " << leftScore << "\tright: " << rightScore << "\tlog: " << logScore << "\tresult: " << result << std::endl;
	return result;
}

double Rule::calc_value_binary(Team &left, Team &right, double *weight)
{
	const double &leftScore = left.scores["Value"];
	const double &rightScore = right.scores["Value"];
	return std::log(1 + (leftScore / (leftScore + rightScore)));
}

double Rule::calc_homeadvantage_binary(Team &left, Team &right, double *weight)
{
	const double &homeLeft = left.scores["HA"];
	const double &homeRight = right.scores["HA"];
	// this rule is only effective if at least one of the teams has a home-advantage assigned
	*weight = std::min(1.0, homeLeft + homeRight) / 1.0;
	assert(*weight >= 0.0 && *weight <= 1.0);
	// if not, the weight will be 0 anyway..
	if (homeLeft == 0.0 && homeRight == 0.0) return 0.5;
	return homeLeft / (homeLeft + homeRight);
}

} // namespace sim