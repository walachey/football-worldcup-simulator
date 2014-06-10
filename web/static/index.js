function createProcessGraphs(json_data)
{
	var graphs = ["bets", "elo", "spi", "fifa", "value"];
	var max_day = 32;
	var labels = [];
	for (var i = 0; i < max_day + 1; ++i)
	{
		var day = (12 + i - 1) % 30 + 1;
		var mon = Math.floor((12 + i - 1) / 30) + 6;
		if (i == 0 || day == 1 || i == max_day)
			mon = mon.toString() + ".";
		else
		{
			mon = "";
		}
		labels.push(day.toString() + "." + mon);
	}
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
			var clr = ((colorstep * team_index + 120) % 360).toString();
			var l = 100;
			if (team_index % 2 == 0) l = 50;
			data.datasets.push({
				data: series,
				strokeColor : "hsla(" + clr + ",100%," + (l)/100 + "%,0.5)",
				pointColor : "hsla(" + clr + ",75%," + (75*l)/100 + "%,0.5)",
				pointStrokeColor : "hsla(" + clr + ",100%," + (75*l)/100 + "%,0.5)",
				title: team.name
				});
		}
		
		$("#" + graphs[i]).replaceWith('<canvas id="' + graphs[i] + '" width="600" height="100"></canvas>');
		$("#" + graphs[i]).attr("width", $("#graph_" + graphs[i]).width());
		var ctx = document.getElementById(graphs[i]).getContext("2d");
		var chart = new Chart(ctx).Line(data, {datasetFill : false});
		
		if (!legend)
		{
			legend = true;
			var legend_div = $("#graph_legend");
			legend_div.empty();
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
