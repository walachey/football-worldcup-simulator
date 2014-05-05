#ifndef _JSON_H
#define _JSON_H

#define JSON_SPIRIT_VALUE_ENABLED
#define JSON_SPIRIT_WVALUE_ENABLED
#define JSON_SPIRIT_MVALUE_ENABLED
#define JSON_SPIRIT_WMVALUE_ENABLED

#pragma warning(push, 0) // disable warnings in MSVC
#include <json_spirit/json_spirit.h>
#pragma warning(pop) 
#endif