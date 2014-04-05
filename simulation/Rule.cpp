#include "stdafx.h"
#include "Rule.h"

namespace sim
{

Rule::Rule(json_spirit::Object &data)
{
	weight = 0.0;

	for (json_spirit::Pair &pair : data)
	{
		std::string &key = pair.name_;
		if (key == "scores") setupNeededScores(pair.value_.get_array());
		else if (key == "parameters") setupParameters(pair.value_.get_obj());
		else if (key == "weight") weight = pair.value_.get_real();
		else if (key == "function") setCalculationFunction(pair.value_.get_str());
		else if (key == "backref") isBackrefRule = pair.value_.get_bool();
		else
			std::cerr << "sim::Rule: invalid property \"" << key << "\"" << std::endl;
	}

	if (calculationFunction == &Rule::calc_dummy || calculationFunction == nullptr)
		std::cerr << "Rule without calculation function." << std::endl;

	if (calculationFunction == &Rule::calc_custom_binary)
	{
		if (ruleParameters.count("normalization_constant"))
		{
			customNormalizationConstant = ruleParameters["normalization_constant"];

			if (!std::isnormal(customNormalizationConstant))
			{
				std::cerr << "The normalization constant of the custom rating rule must be a non-zero number!" << std::endl;
				throw "The Simulation was stopped because of invalid rule parameters.";
			}
		}
		else
		{
			std::cerr << "Custom Rating rule needs a normalization constant!" << std::endl;
			throw "The simulation was stopped because of missing rule parameters.";
		}
	}
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

void Rule::setupParameters(json_spirit::Object &data)
{
	for (json_spirit::Pair &pair : data)
	{
		std::string &key = pair.name_;
		ruleParameters[key] = pair.value_.get_real();
	}
}

double Rule::getRawResults(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	assert((isBackrefRule && currentWinExpectancy != nullptr) || (!isBackrefRule && currentWinExpectancy == nullptr));
	*weight = 1.0;
	return (this->*calculationFunction)(left, right, weight, currentWinExpectancy);
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
		calculationFunction = &Rule::calc_luck_binary;
	else if (functionName == "custom_binary")
		calculationFunction = &Rule::calc_custom_binary;
	else
	{
		std::cerr << "Unknown calculation function: \"" << functionName << "\"" << std::endl;
		calculationFunction = &Rule::calc_dummy;
	}
}

double Rule::calc_elo_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	return 1.0 / (1.0 + std::pow(10.0, (right.scores["ELO"] - left.scores["ELO"]) / 400.0));
}

double Rule::calc_fifa_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &leftScore = left.scores["FIFA"];
	const double &rightScore = right.scores["FIFA"];
	const double logScore = std::log(leftScore / rightScore);
	const double result = 1.0 / (1.0 + std::exp(-logScore / 0.23725));
	//std::cerr << "left: " << leftScore << "\tright: " << rightScore << "\tlog: " << logScore << "\tresult: " << result << std::endl;
	return result;
}

double Rule::calc_value_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &leftScore = left.scores["Value"];
	const double &rightScore = right.scores["Value"];
	return std::log(1 + (leftScore / (leftScore + rightScore)));
}

double Rule::calc_homeadvantage_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &homeLeft = left.scores["HA"];
	const double &homeRight = right.scores["HA"];
	// this rule is only effective if at least one of the teams has a home-advantage assigned
	*weight = homeLeft / (homeLeft + homeRight);
	assert(((homeLeft + homeRight) == 0.0) || (*weight >= 0.0 && *weight <= 1.0));
	// if not, the weight will be 0 anyway..
	if (homeLeft == 0.0) return *currentWinExpectancy;

	return 2.0 / 
		(1.0 + std::exp(-4.0 * (*currentWinExpectancy))) - 1.0;
}

double Rule::calc_custom_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	return 1.0 / (1.0 + std::exp((right.scores["Custom"] - left.scores["Custom"]) / customNormalizationConstant));
}

} // namespace sim