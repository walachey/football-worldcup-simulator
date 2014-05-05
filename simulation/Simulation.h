#ifndef _SIMULATION_H
#define _SIMULATION_H

#include "json.h"

#include "Team.h"
#include "Rule.h"
#include "Tournament.h"


namespace sim
{

class Simulation
{
public:
	static Simulation *singleton;

	Simulation(json_spirit::Value &jsonData);
	~Simulation();
	void reset();
	void setupTeams(json_spirit::Array &teamData);
	void setupRules(json_spirit::Array &teamData);

	int numberOfRuns;
	int numberOfThreads;
	int tournamentID;
	std::string tournamentType;

	std::vector<Team> teams;
	std::vector<Rule> rules;
	std::vector<Tournament*> tournaments;
	std::vector<RankData> ranks;
	// will only be filled after the simulation has finished
	std::map<std::string, std::map<int, TeamResult>> clusterTeamResults;
	std::map<std::string, MatchResultStatisticsList> clusterMatchResultStatisticsLists;

	void execute();

	json_spirit::Object getJSONResults();
	void fillRankResults(json_spirit::Array &ranks);
	void fillTeamResults(json_spirit::Array &teams, std::string cluster);
	void fillMatchResults(json_spirit::Array &results, std::string cluster);

	unsigned int randomSeed;
};

}
#endif