/*
	Some global variables and getter/setters are used to pass information over dialogs/ajax requests and the like.
*/
// the tournament type ID is unique for the page and later forms need it for their JSON requests
window.selected_tournament_type_id = null;
function getSelectedTournamentTypeID() { return window.selected_tournament_type_id; }
function setSelectedTournamentTypeID(to) { window.selected_tournament_type_id = to; }
// comes from a template file
window.general_tournament_page_link = null;
function getGeneralTournamentPageLink() { return window.general_tournament_page_link; }
function setGeneralTournamentPageLink(to) { window.general_tournament_page_link = to; }

// validates the rule input and (may) put the selected rules into an array passed as the /rule_ids/ argument. The remaining rule data will be put into the /rule_data/ object
function validateRuleSelection(rule_ids, rule_data)
{
	// no rules? nope nope nope
	if ($("#rules tr").length <= 1)
	{
		$("#rules").effect("shake");
		return false;
	}
	// do validation of all inputs and get the selected rules' IDs at the same time
	if (rule_ids == null)
		rule_ids = [];
	if (rule_data == null)
		rule_data = {}; // to fetch the name&description right now (will be needed for the team-view)
	var regexp = new RegExp("^[0-9]*\\.?[0-9]*$");
	var valid = true;
	$(".rule_row").each(
						function (index, item)
						{
							var input_field = $(item).find("input");
							// remember rule ID for later
							rule_ids.push(parseInt(input_field.attr("name"), 10));
							rule_data[input_field.attr("name")] = {name: $(item).children("td").eq(1).text(), desc: $(item).children("td").eq(2).text()};
							// validation of input
							if (!regexp.test(input_field.val()))
							{
								valid = false;
								$(input_field).effect("shake");
							}
						}
					);
	if (!valid) return false;
	return true;
}

function startTournament()
{
	$("#finish_setup").toggleClass("selectionbox-info selectionbox-ok", 500);
	$("#finish_setup > .headpart").hide("blind");
	
	var progress_bar = $("#starting_progressbar");
	var progress_bar_value = progress_bar.find(".ui-progressbar-value");
	progress_bar.progressbar({value:false});
	progress_bar.show("fade");
	
	// generate JSON object with all the necessary information for the server
	var json_object = {};
	json_object.tournament_type = getSelectedTournamentTypeID();
	json_object.rules = [];
	
	// figure out active rules and respective weights
	$("#rules > tbody > tr").each(
		function (index, item)
		{
			var input_box = $(item).find("input");
			if (input_box == null) return;
			
			var rule_object = {};
			rule_object.id = input_box.attr("name");
			rule_object.weight = input_box.val();
			json_object.rules.push(rule_object);
			// console.log("rule " + rule_object.id + " with weight " + rule_object.weight);
		}
	);
	
	json_object.teams = [];
	// figure out active teams and put into list
	$("#teams > tbody > tr").each(
		function (index, item)
		{
			var team_object = {};
			team_object.id = $(item).find(".teamid").html();
			json_object.teams.push(team_object);
		}
	);
	
	failfunc = function(message) 
		{
			// progress_bar.hide("fade");
			$("#finish_setup > .headpart").show("blind");
			$("#finish_setup").toggleClass("selectionbox-info selectionbox-ok", 500);
			alert (message);
			return;
		}
	
	// AJAX is go
	$.ajax(
	{
		type: "POST",
		url:"json/register_tournament",
		dataType: "json",
		data: { get_param: 'value', info: JSON.stringify(json_object) },
		timeout: 10000,
		success: function(data) 
			{
				if (data.status == "FAIL")
				{
					return failfunc(data.message);
				}
				else if (data.status == "OK")
				{
					progress_bar.hide("blind");
					$("#goto_tournament > .info").text(data.message);
					// alert(data.message);
					var general_tournament_page_link = getGeneralTournamentPageLink();
					general_tournament_page_link = general_tournament_page_link.slice(0, -1) + data.tournament_id;
					$("#goto_tournament > a").attr("href", general_tournament_page_link);
					$("#goto_tournament").show("blind");
					$("#finish_setup").css("pointer-events", "auto");
					
					setTimeout(function() { window.location = general_tournament_page_link; }, 1000);
				}
			},
		error: function() { return failfunc("An error occured. Try again."); }
	}
	);
}