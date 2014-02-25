#ifndef _MATCH_H
#define _MATCH_H

namespace sim
{
class Simulation;
class Team;

class MatchResult
{
public:
	MatchResult(std::string cluster, int teams[], int goals[], int places[], bool hadOvertime) : cluster(cluster), hadOvertime(hadOvertime)
	{
		for (size_t i = 0; i < 2; ++i)
		{
			this->teams[i] = teams[i];
			this->goals[i] = goals[i];
		}
		for (size_t i = 0; i < 3; ++i) // winner, loser, draw
			this->places[i] = places[i];
	}
	~MatchResult() {};

	// for statistics pooling, one cluster could f.e. be one match in a tournament ladder
	std::string cluster;

	// for FIFA style tournaments, where the score depends on f.e. whether the match had an overtime
	bool hadOvertime;

	int teams[2];
	int goals[2];
	int places[3]; // winner, loser, draw

	bool isWinner(int index) { return goals[index] > goals[1 - index]; }
	bool isLoser(int index) { return goals[index] < goals[1 - index]; }
	bool isDraw() { return goals[0] == goals[1]; }

	int getPlaceForTeamIndex(int index)
	{
		if (isWinner(index)) return places[0];
		if (isLoser(index)) return places[1];
		return places[2];
	}
};

class Match
{
public:
	Match();
	~Match();

	static MatchResult execute(std::string cluster, Simulation *simulation, Team &left, Team &right, bool forceWinner = false);
};

}
#endif