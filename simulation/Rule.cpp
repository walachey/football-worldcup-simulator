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

double Rule::getRawResults(Team &left, Team &right)
{
	return (this->*calculationFunction)(left, right);
}

void Rule::setCalculationFunction(std::string functionName)
{
	if (functionName == "elo_binary")
		calculationFunction = &Rule::calc_elo_binary;
	else
	{
		std::cerr << "Unknown calculation function: \"" << functionName << "\"" << std::endl;
		calculationFunction = &Rule::calc_dummy;
	}
}

double Rule::calc_elo_binary(Team &left, Team &right)
{
	return 1.0 / (1.0 + std::pow(10.0, (right.scores["ELO"] - left.scores["ELO"]) / 400.0));
}

} // namespace sim