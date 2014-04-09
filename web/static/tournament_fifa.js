
$(document).ready(
	function() 
    {  
	
		fillBrackets({{ matches|safe }}, {{ team_lookup|safe }});		
    } 
);

function fillBrackets(json_data, team_lookup)
{
	// a fresh start!
	$(".all_games tbody").replaceWith("<tbody></tbody>");
	var table_body = $(".all_games tbody").first();
	
	var rounds = [16, 8, 4, 2, 1, 2, 4, 8, 16];
	var games_in_rounds = [
			[1, 3, 5, 7],
			[1, 2, 3, 4],
			[1, 2],
			[1],
			[1],
			[2],
			[3, 4],
			[5, 6, 7, 8],
			[2, 4, 6, 8]
		];
	var round_count = rounds.length;
	for (var round_index = 0; round_index < round_count; ++round_index)
	{
		var round = rounds[round_index];
		var games_count = games_in_rounds[round_index].length;
		var round_name = "round_" + round.toString();
		table_body.append(
			"<td id='column_" + round_index.toString() + "' style='z-index:100'><table class='round' name='" + round_name + "' id='round_index_" + round_index + "' style='z-index:" + (100-round) + "'>" +
			"</table></td>");
		var round_table = table_body.find("#round_index_" + round_index).first();
		for (var game_index = 0; game_index < games_count; ++game_index)
		{
			var game = games_in_rounds[round_index][game_index];
			var name = "game_" + round.toString() + "_" + game.toString();
			round_table.append(
				"<table class='game' id='" + name + "'>" +
				"</table>");
			var game_table = round_table.find("#" + name).first();
			//console.log("Game: " + name);
			// the group get assigned their letter, because they are not in the expected order for better overview..
			if (round == 16)
			{
				game_table.append("<tr><td>&nbsp;</td><td class='table_header'>Group " + String.fromCharCode(64 + game) + "</td><td align='right'><small>pts</small></td></tr>");
			}
			var match_data = json_data[name];
			var team_count = match_data.length;
			for (var team_index = 0; team_index < team_count; ++team_index)
			{
				var team = match_data[team_index];
				//if (team.chance == 0.0) continue;
				var team_data = team_lookup[team.team];
				var class_name = "team_" + team_data.country_code;
				var score_string = "";
				// special treatment for round-robin games where the number is not the win ratio but the score
				if (round == 16)
					score_string = (Math.floor(10 * team.chance) / 10).toString();
				else
					score_string = Math.floor(100 * team.chance + 0.5).toString() + "%"
				game_table.append(
					"<tr class='" + class_name + "' onmouseover='hl(\"" + class_name + "\");'>" +
					"<td><img class='flag' src='/static/img/flags/" + team_data.country_code + ".png'></img></td>" +
					"<td>" + team_data.name + "</td>" +
					"<td class='chance'>" + score_string + "</td>" +
					"</tr>");
			}
		}
	}
	
/*	for (var match_name in json_data)
	{
		if (!json_data.hasOwnProperty(match_name)) continue;
		var data = json_data[match_name];
		var element_name = '#' + match_name;
		var element = $(element_name);
		if (!element) continue;
		element.find("th.head.left").html(team_lookup[data.teams[0]]);
		element.find("th.head.right").html(team_lookup[data.teams[1]]);
		
		element.find("td.left").html(data.goals[0].toFixed(2));
		element.find("td.right").html(data.goals[1].toFixed(2));
	}*/
}

// highlights a team
window.last_highlighted_team = null;
function hl(class_name)
{
	class_name = "." + class_name;
	if (window.last_highlighted_team != null)
	{
		$(window.last_highlighted_team).toggleClass("highlighted");
	}
	$(class_name).toggleClass("highlighted");
	window.last_highlighted_team  = class_name;
}