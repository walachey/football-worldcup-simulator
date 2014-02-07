#include "stdafx.h"
#include "Rule.h"

namespace sim
{

Rule::Rule(json_spirit::Object &data)
{
	weight = 0.0;

	for (auto iter = data.begin(); iter != data.end(); ++iter)
	{
		std::string &key = iter->name_;
		if (key == "scores") setupNeededScores(iter->value_.get_array());
		else if (key == "weight") weight = iter->value_.get_real();
		else
			std::cerr << "sim::Rule: invalid property \"" << key << "\"" << std::endl;
	}
}


Rule::~Rule()
{
}

void Rule::setupNeededScores(json_spirit::Array &data)
{
	for (auto iter = data.begin(); iter != data.end(); ++iter)
	{
		json_spirit::Value &val = *iter;
		neededScores.push_back(val.get_str());
	}
}

} // namespace sim