#pragma once
#include "Tournament.h"

namespace sim
{

// aggregates the score for one team
class EUROStyleTournamentQualificationResult
{
public:
	EUROStyleTournamentQualificationResult() : score(0), goals(0), goalDifference(0) {}
	EUROStyleTournamentQualificationResult(Team *team, int group) : EUROStyleTournamentQualificationResult()
	{
		this->forTeam = team;
		this->group = group;
	}
	int score;
	int goals;
	int goalDifference;
	Team *forTeam;

	bool operator<(EUROStyleTournamentQualificationResult &other);

	// It's important to know later which group this result came from.
	int group;
};

class EUROStyleTournament : public Tournament
{
public:
	EUROStyleTournament(Simulation *sim, int runs) : Tournament(sim, runs) {}
	virtual ~EUROStyleTournament() {}
	virtual void doSanityChecks();
	virtual std::vector<RankData> getRankDataAssignment() const override;
private:
	virtual void execRun();
	// both functions will return the winner for the current stage
	std::vector<Team*> runKnockout(int matches);
	std::vector<Team*> runQualification();
	// generates a name for clustering and result transmission
	std::string getMatchClusterName(int knockoutStage, int matchNumber);
};

} // namespace sim