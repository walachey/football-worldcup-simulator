function createProcessGraphs(json_data)
{
	var graphs = ["bets", "elo", "spi", "fifa"];
	var max_day = 32;
	var labels = [];
	for (var i = 0; i < max_day + 1; ++i)
		labels.push("" + (i+1).toString());

	var colorstep = 360 / json_data.length;
	var legend = false;
	
	for (var i = 0; i < graphs.length; ++i)
	{
		var data = {
			labels : labels,
			datasets : []
		};

		for (var team_index = 0; team_index < json_data.length; ++team_index)
		{
			var team = json_data[team_index];
			var series = team[graphs[i]];
			if (!series)
				series = []
			
			//while (series.length < max_day)
			//	series.push(null);
			
			var clr = (colorstep * team_index).toString();
			data.datasets.push({
				data: series,
				strokeColor : "hsla(" + clr + ",75%,75%,0.5)",
				pointColor : "hsla(" + clr + ",50%,50%,0.5)",
				pointStrokeColor : "hsla(" + clr + ",75%,50%,0.5)",
				title: team.name
				});
		}
		
		$("#" + graphs[i]).attr("width", $("#graph_" + graphs[i]).width());
		var ctx = document.getElementById(graphs[i]).getContext("2d");
		var chart = new Chart(ctx).Line(data, {datasetFill : false});
		
		if (!legend)
		{
			legend = true;
			var legend_div = $("#graph_legend");
			for (var t = 0; t < data.datasets.length; ++t)
			{
				var info = data.datasets[t];
				legend_div.append(
				'<li style="border:2px solid ' + info.pointStrokeColor + ';'
				+ 'background: ' + info.pointColor + ';'
				+ '"+">' 
				+ info.title + '</li>'
				); 
			}
		}
	}
}
