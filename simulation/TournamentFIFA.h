#pragma once
#include "Tournament.h"

namespace sim
{

// aggregates the score for one team
class FIFAStyleTournamentQualificationResult
{
public:
	FIFAStyleTournamentQualificationResult() : score(0), goals(0), goalDifference(0) {}
	FIFAStyleTournamentQualificationResult(Team *team) : FIFAStyleTournamentQualificationResult()
	{
		this->forTeam = team;
	}
	int score;
	int goals;
	int goalDifference;
	Team *forTeam;

	bool operator<(FIFAStyleTournamentQualificationResult &other);
};

class FIFAStyleTournament : public Tournament
{
public:
	FIFAStyleTournament(Simulation *sim, int runs) : Tournament(sim, runs) {}
	virtual ~FIFAStyleTournament() {}
	virtual void doSanityChecks();
private:
	virtual void execRun();
	// both functions will return the winner for the current stage
	std::vector<Team*> runKnockout(int matches);
	std::vector<Team*> runQualification();
	// generates a name for clustering and result transmission
	std::string getMatchClusterName(int knockoutStage, int matchNumber);
};

} // namespace sim