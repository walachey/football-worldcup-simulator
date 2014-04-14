$(document).ready(
	function() 
    {  
		$("#nav_tournament").toggleClass("active");
		$("#tournamenttable").tablesorter({
			textExtraction: function(node)
				{                    
					if ($(node).attr("sorter"))
						return $(node).attr("sorter"); 
					return $(node).text();
				},
			sortInitialOrder: 'desc',
			sortList: [[1, 1]]
		}); 
    } 
);
function viewDataForSpreadsheets(tournament_id, tournament_link)
{
	$("#spreadsheet_dialog").dialog(
		{
			resizable: true,
			draggable: false,
			height: 'auto',
			width: 600,
			modal: true,
			closeText: 'Close',
			closeOnEscape: true,
			open: function(event, ui) { },
			title: "Export the data to spreadsheet software",
			buttons: { Close: function() { $( this ).dialog( "close" ); }
			}
		});

	// figure out header row first..
	var headers = [];
	var text = "";
	$("#tournamenttable > thead .bar").each(
		function (index, item)
		{
			var name = $(item).html();
			headers.push("result_" + index.toString());
			text = text + name + "\t";
		}
	);
	text = "Teams\t" + text + "Avg. Goals\tIn Finals\t\n";

	$("#tournamenttable > tbody > tr").each(
		function (index, item)
		{
			text += $(item).find("[name='name']").html() + "\t";
			var len = headers.length;
			for (var i = 0; i < len; i++)
			{
				var bar = $(item).find("[name='" + headers[i] + "'] small");
				if (bar.length == 0)
					text +="0%\t";
				else
					text += bar.html() + "\t";
			}
			text += $(item).find("[name='avg_goals']").html() + "\t";
			text += $(item).find("[name='finals_perc']").html() + "\t";
			text += "\n"
		}
	);
	$("#spreadsheet_dialog textarea").val(text);
	$("#spreadsheet_dialog textarea").select();
}