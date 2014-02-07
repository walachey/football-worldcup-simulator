#include "stdafx.h"
#include "Team.h"

namespace sim
{

Team::Team(json_spirit::Object &data)
{
	for (auto iter = data.begin(); iter != data.end(); ++iter)
	{
		std::string key = iter->name_;
		if (key == "id") id = iter->value_.get_int();
		else if (key == "scores") setupScores(iter->value_.get_obj());
		else
			std::cerr << "sim::Team: invalid property \"" << key << "\"" << std::endl;
	}
}

void Team::setupScores(json_spirit::Object &scoreData)
{
	for (auto iter = scoreData.begin(); iter != scoreData.end(); ++iter)
	{
		scores[iter->name_] = iter->value_.get_real();
	}
}


Team::~Team()
{
}

RankData::RankData(std::string name)
{
	this->name = name;
}

json_spirit::Object RankData::toJSONObject()
{
	json_spirit::Object object;
	object.push_back(json_spirit::Pair("name", name));
	return object;
}

Result::Result(double percentage)
{
	this->percentage = percentage;
}

json_spirit::Object Result::toJSONObject()
{
	json_spirit::Object object;
	object.push_back(json_spirit::Pair("percentage", percentage));
	return object;
}

} // namespace sim