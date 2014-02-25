#ifndef _TEAM_H
#define _TEAM_H

#include "json.h"

#include "Match.h"

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
	template <class CONT> TeamResult(CONT matches, int teamID);
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
	int teamID;
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

// needs to be defined in the header file, due to template arguments
template <class CONT> TeamResult::TeamResult(CONT matches, int teamID)
{
	TeamResult();
	this->teamID = teamID;

	for (MatchResult &match : matches)
	{
		for (int teamIndex = 0; teamIndex < 2; ++teamIndex)
		{
			const int &teamID = match.teams[teamIndex];
			if (teamID != this->teamID) continue;

			if (match.isWinner(teamIndex))
				addWin();
			else if (match.isLoser(teamIndex))
				addLoss();
			else addDraw();

			// for goal count statistics
			addGoals(match.goals[teamIndex], match.goals[1 - teamIndex]);
			// for the general overview
			addPlace(match.getPlaceForTeamIndex(teamIndex));
		}
	}
}

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