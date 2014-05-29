// we need the IE to not cache AJAX responses..
$.ajaxSetup({ cache: false });

$(document).ready(
	function() 
    { 	
		$("#run_count_par").change(function() { onRunCountParChange(); });
    } 
);

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
window.tournament_max_run_count = 0;
function getMaxTournamentRunCount() { return window.tournament_max_run_count; }
function setMaxTournamentRunCount(to) { window.tournament_max_run_count = to; }

function setSectionState(id, to_state)
{
	if (to_state == "active" || to_state == "ok")
	{
		$(id).toggleClass("selbox-info selbox-ok", 500);
		$(id).parent().toggleClass("selbox-con-info selbox-con-ok", 500);
		
		if (to_state == "ok")
			$(id + " .headpart").hide("blind");
		else
			$(id + " .headpart").show("blind");
	}
	
	if (to_state == "visible")
	{
		$(id).parent().show("blind");
	}
	else
	if (to_state == "hidden")
	{
		$(id).parent().hide("blind");
	}
}

function onRunCountParChange()
{
	var run_count_par = $("#run_count_par");
	var value = parseInt(run_count_par.val());
	var valid = true;
	
	if (!value || isNaN(value) || value > getMaxTournamentRunCount() || value <= 0)
	{
		valid = false;
		
		if (value < 1)
			value = 1;
		else if (value > getMaxTournamentRunCount() || isNaN(value))
			value = getMaxTournamentRunCount();
		$("#finish_setup .error").show("fade");
		run_count_par.val(value);
	}
	
	if (valid)
		run_count_par.removeClass("error");
	else
		run_count_par.addClass("error");
}

// validates the rule input and (may) put the selected rules into an array passed as the /rule_ids/ argument. The remaining rule data will be put into the /rule_data/ object
function validateRuleSelection(rule_ids, rule_data)
{
	// no rules? nope nope nope
	if ($("#rules tr.rule_row").length <= 1)
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
							if (!input_field.val() || !regexp.test(input_field.val()))
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
	setSectionState("#finish_setup", "ok");
	
	var progress_bar = $("#starting_progressbar");
	var progress_bar_value = progress_bar.find(".ui-progressbar-value");
	progress_bar.progressbar({value:false});
	progress_bar.show("fade");
	
	// generate JSON object with all the necessary information for the server
	var json_object = {};
	json_object.tournament_type = getSelectedTournamentTypeID();
	json_object.rules = [];
	
	// figure out active rules and respective weights
	$("#rules > tbody > tr.rule_row").each(
		function (index, item)
		{
			var input_box = $(item).find("input");
			if (input_box == null) return;
			
			var rule_object = {};
			rule_object.id = input_box.attr("name");
			rule_object.weight = parseFloat(input_box.val());
			if (rule_object.weight > 0) // obviously also checked on the server.
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
			team_object.ratings = {};
			// now also get all user-defined rating
			$(item).find("input.custom").each(
				function (index, item)
				{
					var value = parseFloat($(item).val());
					var score_type = $(item).data("score_type");
					team_object.ratings[score_type] = value;
				}
			);
			
			// add!
			json_object.teams.push(team_object);
		}
	);
	
	json_object.rule_parameters = {};
	$("input.rule_parameter").each(
		function (index, item)
		{
			var type_id = $(item).data("type_id");
			var value = parseFloat($(item).val());
			
			if ($(item).is(':checkbox') && !$(item).is(':checked'))
				value = 0.0;
			json_object.rule_parameters[type_id.toString()] = value;
		}
	);
	
	failfunc = function(message) 
		{
			progress_bar.hide("fade");
			setSectionState("#finish_setup", "active");
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
		timeout: 30000,
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
					$("#goto_tournament").show("blind");
					$("#finish_setup").css("pointer-events", "auto");
					
					redirectTo(data.tournament_id, general_tournament_page_link);
				}
			},
		error: function() { return failfunc("An error occured. Try again."); }
	}
	);
}

function redirectTo(tournament_id, tournament_link)
{
	var html = '<div id="loading_dialog" style="margin-left:auto;margin-right:auto;text-align:center;">Please wait while ' + parseInt($("#run_count_par").val()).toString() + ' simulations are running..<br><img src="static/img/loader.gif"><small style="display:none;"><br><hr>If you are not redirected automatically, visit the <strong><a href="/tournaments">My Tournaments</a></strong> page.</small></div>';
	$("#main_container").append(html);
	$("#loading_dialog").dialog(
		{
			resizable: false,
			height: 'auto',
			width: 'auto',
			modal: true,
			closeText: '',
			bgiframe: true,
			closeOnEscape: false,
			open: function(event, ui) { $(".ui-dialog-titlebar-close", this.parentNode).hide(); }
		});
	
	setTimeout(function(){ redirectionTimer(tournament_id, tournament_link, 1); }, 1000);
}

function redirectionTimer(tournament_id, tournament_link, seconds_passed)
{
	if (seconds_passed == 10)
	{
		$("#loading_dialog small").show("fade");
	}
	
	function fail()
	{
		alert("There was an error with your tournament. Sorry :(");
		$("#loading_dialog").dialog('close');
		window.location = tournament_link;
	}

	$.ajax(
	{
		type: "GET",
		url:"json/state/tournament:" + tournament_id,
		dataType: "json",
		data: { get_param: 'value' },
		timeout: 10000,
		success: function(data) 
			{
				if (data.state == "error")
				{
					fail();
					return;
				}
				
				if (data.state == "finished")
				{
					// this is a fix for certain browsers which show the active dialogs on history.back
					$("#loading_dialog").dialog('close');
					
					window.location = tournament_link;
					return;
				}
				
				// try again
				setTimeout(function(){ redirectionTimer(tournament_id, tournament_link, seconds_passed + 1); }, 1000);
			},
		error: function() { fail(); }
	}
	);
}