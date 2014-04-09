$(document).ready(
	function() 
    { 
        $("#teamstable").tablesorter(); 
		$("#nav_create").toggleClass("active");
    } 
);

/*
	Some global variables and getter/setters are used to pass information over dialogs/ajax requests and the like.
*/
// the tournament info contains teams and general information about the tournament and is retrieved using AJAX at some point
window.received_tournament_info = null;
function getTeamData() { return window.received_tournament_info.teams; }
// the currently pending index of the team table to be assigned
function setCurrentlyPendingTeamIndex(index) { window.received_tournament_info.pendingTeamIndex = index; }
function getCurrentlyPendingTeamIndex() { return window.received_tournament_info.pendingTeamIndex; }

function setAvailableScoreData(score_data) { window.received_tournament_info.score_data = score_data;}
function getAvailableScoreData(score_data) { return window.received_tournament_info.score_data;}

function onTypeChosen(type_id)
{
	// animate some buttons and show next selection widget
	$("#choose_type #type_" + type_id.toString()).toggleClass("btn-default btn-success");
	$("#choose_type .type-button:not(#type_" + type_id.toString() + ")").hide("blend");
	setSectionState("#choose_type", "ok");
	setSectionState("#choose_rules", "visible");
	
	// fetch rule information
	$.ajax(
		{
			url:"json/rules/tournament:" + type_id.toString(),
			dataType: "json",
			data: { get_param: 'value' }, 
			success: function(data) { populateRuleSelectionDialog(data); },
			error: function() {alert("An error occured!");}
		}
		);
	
	// this is a global variable
	setSelectedTournamentTypeID(type_id);
}

function showRuleSelectionDialog()
{
	$("#rule_selection_dialog").dialog(
	{
		//autoOpen: false,
		height: "auto",
		width: "auto",
		modal: true,
		title: "Choose the active rules",
		buttons: 
			{
				 Close: function() { $( this ).dialog( "close" ); }
			}
	});
}

function populateRuleSelectionDialog(json_results)
{
	if (json_results == null) return;
	var rule_list = $("#rule_selection_dialog > table");

	$(json_results.rules).each(
								function(index, item)
								{
									rule_list.append(
										'<tr class="btn btn-default" onclick="javascript:onRuleSelected(' + item.id + ', \'' + item.name + '\', \'' + item.desc + '\');">' +
										'<td>' + item.long_name + '</td>' + 
										'<td>' + item.desc + '</td>' +
										'</tr>'
										);
								}
							);
							
	$("#add_rule_button").toggleClass("btn-default btn-primary");
}

function onRuleSelected(id, name, description)
{
	var element_name = "rule_" + id.toString();
	// do not add rules twice
	if ($("#" + element_name).length) return;
	
	var element = '<tr id="' + element_name + '" class="rule_row">' +
					'<td><input class="' + element_name + '" value="1" name="' + id + '">' + '</input></td>' +
					'<td>' + name + '</td>' +
					'<td>' + description + '</td>' +
					'</tr>';
	$("#rules").append(element);
	// with at least one rule, allow finishing the adding process
	$("#end_rule_selection_button").toggleClass("btn-default btn-primary");
}


function endRuleSelection()
{
	var rule_ids = [];
	var rule_data = {};
	if (!validateRuleSelection(rule_ids, rule_data)) return;
	
	// some effects
	setSectionState("#choose_rules", "ok");
	setSectionState("#choose_teams", "visible");
	
	// get the teams and rule parameters
	var tournament_type = getSelectedTournamentTypeID();
	var json_object = new Object();
	json_object.tournament = tournament_type;
	json_object.rules = rule_ids;
	
	$.ajax(
	{
		type: "POST",
		url:"json/teams",
		dataType: "json",
		data: { get_param: 'value', info: JSON.stringify(json_object) }, 
		success: function(data) { populateTeamView(rule_data, data); },
		error: function() {alert("An error occured!");}
	}
	);
}

function populateTeamView(rule_data, json_data)
{
	// remember for later
	window.received_tournament_info = json_data;
	
	// populate both the team with default rows AND the team selection dialog with all teams
	
	// populate team table with X teams and scores, where X is the amount of players allowed
	// header row
	var header_row = "<thead><tr><th>Team</th>";
	// one column for every score
	var scores = [];
	for (var key in json_data.scores)
	{ 
		if (!json_data.scores.hasOwnProperty(key)) continue;
		var value = json_data.scores[key];
		scores.push({id: key, name: value.name, desc: value.desc});
		header_row += "<th>" + value.name + "</th>";
	}
	// remember for later
	setAvailableScoreData(scores);
   
	header_row += "</tr></thead><tbody>";
	$("#teams").append(header_row);
	var team_selection_dialog = $("#team_selection_dialog > table");
	team_selection_dialog.append(header_row);
	
	// and now one row for every possible team
	var team_list_length = json_data.teams.length;
	for (var team_index = 0; team_index < team_list_length; ++team_index)
	{
		var team = json_data.teams[team_index];
		var score_string = "";
		var row = "";
		for (var score_index = 0; score_index < scores.length; ++score_index)
		{
			var score = scores[score_index];
			score_string += '<td><span class="score">' + team.scores[score.id.toString()] + '</span></td>';
		}
		// append only the possible number of teams for the tournament to the main view
		if (team_index < json_data.team_count)
		{
			row = '<tr id="team_' + team_index + '">';
			row += '<td class="btn btn-default" style="width:100%" onclick="javascript:changeTeam(' + team_index + ');"><span class="teamname">' + team.name + '</span><span class="teamid" style="display:none">' + team.id + '</span></td>';
			row += score_string;
			row += "</tr>";
			$("#teams > tbody").append(row);
		}
		// but always add to full team list in the selection dialog
		row = '<tr onclick="javascript:onTeamSelected(' + team_index + ');">';
		row += '<td>' + team.name + '</td>';
		row += score_string;
		row += "</tr>";
		// but put all teams into the selection dialog
		team_selection_dialog.append(row);
	}
	$("#teams").append("</tbody>");
	team_selection_dialog.append("</tbody>");
	$(team_selection_dialog).tablesorter(); 
}

function onTeamSelected(index_to)
{
	index_from = getCurrentlyPendingTeamIndex();
	score_data = getAvailableScoreData();
	team_data = getTeamData();
	team = team_data[index_to];
	scores = team.scores;
	var row_name = "#team_" + index_from.toString();
	var pending_row = $(row_name);
	$("#team_selection_dialog").effect("transfer", {to:row_name, className:"ui-effects-transfer"});
	$("#team_selection_dialog").dialog("close");
	
	
	// set new team name in first field
	pending_row.find(".teamname").html(team_data[index_to].name);
	pending_row.find(".teamid").html(team_data[index_to].id);
	// and refresh score values, as well
	$(pending_row.find(".score")).each(
		function (index, item)
		{
			$(item).html(scores[score_data[index].id]);
		}
	);
}

function changeTeam(index)
{
	setCurrentlyPendingTeamIndex(index);
	$("#team_selection_dialog").dialog(
	{
		//autoOpen: false,
		height: 400,
		width: "auto",
		modal: true,
		title: "Select team",
		buttons: 
			{
				 Close: function() { $( this ).dialog( "close" ); }
			}
	});
}

function endTeamSelection()
{
	// some effects
	setSectionState("#choose_teams", "ok");
	setSectionState("#finish_setup", "visible");
}
