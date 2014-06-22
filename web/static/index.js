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
			var series_data = team[graphs[i]];
			if (!series_data) series_data = [];
			
			var first_null_index = 0, len = series_data.length;
			for (;first_null_index < len; ++first_null_index)
				if (series_data[first_null_index] == 0) break;
			var series = series_data.slice(0, first_null_index);
			var clr = ((colorstep * team_index + 120) % 360).toString();
			var l = 100;
			if (team_index % 2 == 0) l = 50;
			data.datasets.push({
				data: series,
				strokeColor : "hsl(" + clr + ",100%," + (50*l)/100 + "%)",
				pointColor : "hsl(" + clr + ",75%," + (20*l)/100 + "%)",
				pointStrokeColor : "hsl(" + clr + ",100%," + (75*l)/100 + "%)",
				title: team.name
				});
		}
		
		$("#" + graphs[i]).replaceWith('<canvas id="' + graphs[i] + '" width="600" height="100"></canvas>');
		$("#" + graphs[i]).attr("width", $("#graph_" + graphs[i]).width());
		var ctx = document.getElementById(graphs[i]).getContext("2d");
		var chart = new Chart(ctx).Line(data, {datasetFill: false, datasetStrokeWidth: 2, pointDotRadius: 1.5});
		
		if (!legend)
		{
			legend = true;
			var legend_div = $("#graph_legend");
			legend_div.empty();
			for (var t = 0; t < data.datasets.length; ++t)
			{
				var info = data.datasets[t];
				legend_div.append(
				'<li style="border:2px solid ' + info.strokeColor + ';'
				+ 'background: ' + info.pointStrokeColor + ';'
				+ '"+">' 
				+ info.title + '</li>'
				); 
			}
		}
	}
}
