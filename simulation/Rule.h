#ifndef _RULE_H
#define _RULE_H

#include "json.h"
#include <vector>
#include <string>

namespace sim
{

class Rule
{
public:
	Rule(json_spirit::Object &data);
	~Rule();
	void setupNeededScores(json_spirit::Array &data);

	std::vector<std::string> neededScores;
	double weight;
};

}
#endif