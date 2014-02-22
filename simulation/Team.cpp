#include "stdafx.h"
#include "Team.h"

namespace sim
{

TeamResult::TeamResult()
{
	for (size_t i = 0; i < StatisticalDataKeys::_LastKey; ++i)
		statisticalData[i] = 0;
	for (size_t i = 0; i < MAXPLACES; ++i)
		placeHistogram[i] = 0;
}

TeamResult::~TeamResult()
{

}

void TeamResult::merge(TeamResult &other)
{
	for (size_t i = 0; i < StatisticalDataKeys::_LastKey; ++i)
		statisticalData[i] += other.statisticalData[i];
	for (size_t i = 0; i < MAXPLACES; ++i)
		placeHistogram[i] += other.placeHistogram[i];
}

json_spirit::Object TeamResult::toJSONObject()
{
	json_spirit::Object object;
	object.push_back(json_spirit::Pair("wins", statisticalData[StatisticalDataKeys::TotalWins]));
	object.push_back(json_spirit::Pair("losses", statisticalData[StatisticalDataKeys::TotalLosses]));
	object.push_back(json_spirit::Pair("draws", statisticalData[StatisticalDataKeys::TotalDraws]));
	return object;
}

json_spirit::Array TeamResult::rankDataToJSONArray(std::vector<RankData> &rankData)
{
	json_spirit::Array ranks;
	// match all ranks
	for (RankData &rank : rankData)
	{
		json_spirit::Object object;
		int count = 0;
		for (int i = rank.placeBegin; i <= rank.placeEnd; ++i)
			count += placeHistogram[i];
		// safety
		float value = 0.0f;
		if (statisticalData[StatisticalDataKeys::TotalMatches] != 0)
			value = (float)count / (float) statisticalData[StatisticalDataKeys::TotalMatches];
		object.push_back(json_spirit::Pair("percentage", value));
		ranks.push_back(object);
	}
	return ranks;
}

Team::Team(json_spirit::Object &data)
{
	for (json_spirit::Pair &pair : data)
	{
		std::string key = pair.name_;
		if (key == "id") id = pair.value_.get_int();
		else if (key == "scores") setupScores(pair.value_.get_obj());
		else
			std::cerr << "sim::Team: invalid property \"" << key << "\"" << std::endl;
	}
}

void Team::setupScores(json_spirit::Object &scoreData)
{
	for (json_spirit::Pair &pair : scoreData)
	{
		scores[pair.name_] = pair.value_.get_real();
	}
}


Team::~Team()
{
}

RankData::RankData(std::string name, int placeBegin, int placeEnd)
{
	this->name = name;
	this->placeBegin = placeBegin;
	this->placeEnd = placeEnd;
}

json_spirit::Object RankData::toJSONObject()
{
	json_spirit::Object object;
	object.push_back(json_spirit::Pair("name", name));
	return object;
}


} // namespace sim