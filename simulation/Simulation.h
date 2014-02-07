
#ifndef _SIMULATION_H
#define _SIMULATION_H

#include "json.h"

#include "Team.h"
#include "Rule.h"

namespace sim
{

class Simulation
{
public:
	Simulation(json_spirit::Value &jsonData);
	~Simulation();
	void reset();
	void setupTeams(json_spirit::Array &teamData);
	void setupRules(json_spirit::Array &teamData);

	int numberOfThreads;
	int tournamentID;

	std::vector<Team> teams;
	std::vector<Rule> rules;

	void execute();

	json_spirit::Object getJSONResults();
	void fillRankResults(json_spirit::Array &ranks);
	void fillTeamResults(json_spirit::Array &teams);
};

}
#endif