#include "stdafx.h"
#include "Rule.h"

#include "Simulation.h"

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

	if (calculationFunction == &Rule::calc_spi_binary)
	{
		generateExpectancyMatrix(&Rule::calculateSPIWinExpectancy);
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
	else if (functionName == "age_binary")
		calculationFunction = &Rule::calc_age_binary;
	else if (functionName == "homeadvantage_binary")
		calculationFunction = &Rule::calc_homeadvantage_binary;
	else if (functionName == "spi_binary")
		calculationFunction = &Rule::calc_spi_binary;
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
	const double scoreDiff = leftScore - rightScore;
	const double result = 1.0 / (1.0 + std::exp(-scoreDiff / 291.5));
	//std::cerr << "left: " << leftScore << "\tright: " << rightScore << "\tlog: " << logScore << "\tresult: " << result << std::endl;
	return result;
}

double Rule::calc_value_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &leftScore = left.scores["Value"];
	const double &rightScore = right.scores["Value"];
	const double logScore = std::log(leftScore / rightScore);
	const double result = 1.0 / (1.0 + std::exp(-logScore / 1.3026));
	return result;
}

double Rule::calc_age_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &leftScore = left.scores["Age"];
	const double &rightScore = right.scores["Age"];
	const double ageDiff = leftScore - rightScore;
	const double result = 1.0 / (1.0 + std::exp(-(32.0 * ageDiff - ageDiff * ageDiff * ageDiff) / 131.0));
	return result;
}

double Rule::calc_spi_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
#ifndef NDEBUG
	if (probabilityLookupMatrix.empty())
	{
		throw("SPI rule: probability lookup matrix not initialized. This can happen if the rule data is provided before the team data.");
	}
#endif
	return probabilityLookupMatrix[left.index][right.index];
}

double Rule::calc_homeadvantage_binary(Team &left, Team &right, double *weight, double *currentWinExpectancy)
{
	const double &homeLeft = left.scores["HA"];
	const double &homeRight = right.scores["HA"];
	// this rule is only effective if at least one of the teams has a home-advantage assigned
	*weight = homeLeft / std::max(1.0, homeLeft + homeRight);
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

void Rule::generateExpectancyMatrix(double (*fun)(Team&, Team&))
{
	assert(probabilityLookupMatrix.empty());
	size_t teamCount = Simulation::singleton->teams.size();
	assert(teamCount >= 2 && "Team data must be provided before rule data.");

	probabilityLookupMatrix.resize(teamCount);
	for (size_t i = 0; i < teamCount; ++i)
		probabilityLookupMatrix[i].resize(teamCount);
	
	for (Team &left : Simulation::singleton->teams)
	{
		for (Team &right : Simulation::singleton->teams)
		{
			assert(left.index >= 0 && left.index < Simulation::singleton->teams.size());
			assert(right.index >= 0 && right.index < Simulation::singleton->teams.size());
			double prob_left = fun(left, right);
			double prob_right = fun(right, left);
			probabilityLookupMatrix[left.index][right.index] = prob_left;
			probabilityLookupMatrix[right.index][left.index] = prob_right;
		}
	}
}

double Rule::calculateSPIWinExpectancy(Team &left, Team &right)
{
	const double &off1 = left.scores["SPI Off"];
	const double &off2 = right.scores["SPI Off"];
	const double &def1 = left.scores["SPI Def"];
	const double &def2 = right.scores["SPI Def"];

	const double combined_off = (off1 + def2) / 2.0;
	const double combined_def = (def1 + off2) / 2.0;

	std::function<int(int)> factorial =
		[&](int n)
	{
		return (n == 1 || n == 0) ? 1 : factorial(n - 1) * n;
	};
	auto poisson_probability =
		[&](double lambda, int times)
	{
		return std::exp(-lambda) * std::pow(lambda, (double)times) / (double)factorial(times);
	};

	double prob_off(0.0), prob_def(0.0);

	for (int i = 0; i < 20; ++i)
	{
		const double equal_prob_off = poisson_probability(combined_off, i);
		const double equal_prob_def = poisson_probability(combined_def, i);

		double less_prob_off(0.0), less_prob_def(0.0);
		for (int c = 0; c < i; ++c)
		{
			less_prob_off += poisson_probability(combined_off, c);
			less_prob_def += poisson_probability(combined_def, c);
		}

		prob_off += equal_prob_off * less_prob_def;
		prob_def += equal_prob_def * less_prob_off;
	}
	return (prob_off / (prob_off + prob_def));
}

} // namespace sim