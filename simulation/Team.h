#ifndef _TEAM_H
#define _TEAM_H

#include "json.h"

#include <vector>
#include <map>
#include <string>
#include <tuple>

namespace sim
{

class RankData
{
public:
	RankData(std::string name, int placeBegin, int placeEnd);
	std::string name;
	int placeBegin, placeEnd;

	json_spirit::Object toJSONObject();
};


class TeamResult
{
public:
	TeamResult();
	~TeamResult();

	void merge(TeamResult &other);
	json_spirit::Object toJSONObject();
	json_spirit::Array rankDataToJSONArray(std::vector<RankData> &rankData);

	double getAvgGoals()
	{
		if (statisticalData[StatisticalDataKeys::TotalMatches] == 0) return 0.0;
		return (double)statisticalData[StatisticalDataKeys::TotalOwnGoals] / (double)statisticalData[StatisticalDataKeys::TotalMatches];
	}

	void addWin()
	{
		incMatchCount();
		statisticalData[StatisticalDataKeys::TotalWins] += 1;
	}

	void addLoss()
	{
		incMatchCount();
		statisticalData[StatisticalDataKeys::TotalLosses] += 1;
	}

	void addDraw()
	{
		incMatchCount();
		statisticalData[StatisticalDataKeys::TotalDraws] += 1;
	}

	void addGoals(int ownGoals, int receivedGoals)
	{
		statisticalData[StatisticalDataKeys::TotalOwnGoals] += ownGoals;
		statisticalData[StatisticalDataKeys::TotalReceivedGoals] += receivedGoals;
	}

	void addPlace(int place)
	{
		assert (place > 0 && place < MAXPLACES);
		placeHistogram[place] += 1;
	}

private:
	void incMatchCount() { ++statisticalData[StatisticalDataKeys::TotalMatches]; }

	enum StatisticalDataKeys
	{
		TotalMatches = 0,
		TotalWins,
		TotalLosses,
		TotalDraws,
		TotalOwnGoals,
		TotalReceivedGoals,
		_LastKey
	};
	int statisticalData[StatisticalDataKeys::_LastKey];

	static const size_t MAXPLACES = 256;
	int placeHistogram[MAXPLACES];
};

class Team
{
public:
	Team(json_spirit::Object &data);
	~Team();
	void setupScores(json_spirit::Object &scoreData);

	int id;
	std::map<std::string, double> scores;
};


}
#endif