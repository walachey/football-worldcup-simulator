$(document).ready(
	function() 
    { 
       // $("#teamstable").tablesorter(); 
		$("#nav_create_simple").toggleClass("active");

		$("#rules > tbody > tr.rule_row input").each(
			function (index, item)
			{
				$(item).change(function() { updateRuleSpiderChart(); });
			}
		);
		
		$("#custom_rule_constant").change(function() { updateCustomRuleChart(); });		
		updateRuleSpiderChart();
		updateCustomRuleChart();
    } 
);

function updateRuleSpiderChart()
{
	
	var labels = [];
	var dataset = {
		fillColor: "rgba(50, 50, 150, 0.5)",
		strokeColor: "rgba(0, 0, 50, 1.0)",
		data: []
	};
	var maxValue = 1.0;
	$("#rules > tbody > tr.rule_row").each(
		function (index, item)
		{
			var input_box = $(item).find("input");
			if (input_box == null) return;
			
			labels.push(input_box.attr("title"));
			var value = parseFloat(input_box.val());
			if (value > maxValue)
				maxValue = value;
			dataset.data.push(value);
		}
	);
	
	// replacing the canvas element seems necessary for certain mobile browsers..
	$('#rulecanvas').replaceWith('<canvas id="rulecanvas" width="300" height="300"></canvas>');
	
	var canvas = document.getElementById("rulecanvas");
	var ctx = canvas.getContext("2d");
	var options = {
		scaleOverride: true,
		scaleStartValue: 0.0,
		scaleSteps: 3.0,
		scaleStepWidth: maxValue / 3.0,
		pointDot : false,
	};
	new Chart(ctx).Radar({labels: labels, datasets: [dataset]}, options);
}

function showCustomRule(id)
{
	
	$("#rule_row_" + id.toString()).show("fade");
	$("#custom_show_" + id.toString()).hide();
	showCustomTeamRatingsDialog(id)
}

function updateCustomRuleChart()
{
	var value = parseFloat($("#custom_rule_constant").val());
	var fun = function(x) { return 1.0 / (1.0  + Math.exp(-x/value)); }
	var labels = [];
	var data = [];
	for (var i = -100; i <= 100; i += 20)
	{
		labels.push(i);
		data.push(fun(i));
	}
	var data = {
		labels : labels,
		datasets : [
			{
				fillColor : "rgba(220,220,255,0.5)",
				strokeColor : "rgba(150,150,255,1)",
				pointColor : "rgba(100,100,200,1)",
				pointStrokeColor : "#fff",
				data : data
			}
		]
	};
	$('#customfunctioncanvas').replaceWith('<canvas id="customfunctioncanvas" width="300" height="300" style="float:left;"></canvas>');
	var canvas = document.getElementById("customfunctioncanvas");
	var ctx = canvas.getContext("2d");
	var options = {
		scaleOverride : true,
		scaleSteps : 10,
		scaleStepWidth : 0.1,
		scaleStartValue : 0.0,
		bezierCurve : false,
	};
	new Chart(ctx).Line(data, options);
}

function showCustomTeamRatingsDialog(id)
{
	$("#choose_teams_con").dialog(
	{
		//autoOpen: false,
		height: "auto",
		width: "auto",
		modal: true,
		title: "Set the custom ratings",
		buttons: 
			{
				 OK: function() { $( this ).dialog( "close" ); }
			}
	});
	var width = Math.min($(window).width() * 0.9, $("#choose_teams_con").width());
	$("#choose_teams_con").dialog('option', 'height', $(window).height() * 0.8);
	$("#choose_teams_con").dialog('option', 'width', width);
}

function showPlayedMatches()
{
	// just fade out?
	if ($("#show_matches").is(":visible"))
	{
		$("#show_matches").hide("clip");
		return;
	}
	$("#show_matches").show("clip");
	
	// get matches via AJAX
	if ($("#show_matches table td").length == 0)
	{
		$.ajax(
		{
			url:"matchtable",
			dataType: "html",
			data: { get_param: 'value' }, 
			success: function(data) { populatePlayedMatches(data); },
			error: function() { populatePlayedMatchesFail(); }
		}
		);
	}
}

function scroll(element, parent){
     $(parent).animate({ scrollTop: $(parent).scrollTop() + $(element).offset().top - $(parent).offset().top }, { duration: 'slow', easing: 'swing'});
     $('html,body').animate({ scrollTop: $(parent).offset().top - $(window).height() + $(element).height() }, { duration: 1000, easing: 'swing'});
}

function populatePlayedMatchesFail()
{
	$("#show_matches .spacer").append("<h3><small>Could not load matches!</small></h3>");
}
function populatePlayedMatches(html)
{
	$("#show_matches .spacer").hide();
	$("#show_matches table").replaceWith(html);
	
	var elem = "#show_matches table tr:nth-child(12)";
	var parent = "#show_matches table tbody";
	if (!$(elem).length)
	{
		elem = "#show_matches table";
		parent = "#show_matches";
	}
	scroll(elem, parent);
	setTimeout(function(){ $("#show_matches table").effect("highlight"); }, 1000);
}