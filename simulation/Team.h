#ifndef _TEAM_H
#define _TEAM_H

#include "json.h"

#include <vector>
#include <map>
#include <string>

namespace sim
{

class RankData
{
public:
	RankData(std::string name);
	std::string name;

	json_spirit::Object toJSONObject();
};

class Result
{
public:
	Result(double percentage);
	double percentage;

	json_spirit::Object toJSONObject();
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