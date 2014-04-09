$(document).ready(
	function() 
    {  
		$("#nav_tournaments").toggleClass("active");
		correctRuleInfo();
		correctTimestamps();
    } 
);

function correctRuleInfo()
{
	$(".rule_info").each(
		function (index, item)
		{
			var rule_info = JSON.parse($(item).html());
			var rules = [];
			for (rule in rule_info)
			{
				var weight = rule_info[rule];
				var rule_object = {name: rule, weight: weight};
				console.log(rule + ": " + weight.toString());
				var rule_length = rules.length;
				for (var i = 0; i < rule_length; ++i)
				{
					if (rules[i].weight > weight) continue;
					rules.splice(i, 0, rule_object);
					break;
				}
				if (i == rule_length)
					rules.push(rule_object);
			}
			
			var text = "";
			var rule_count = rules.length;
			for (var i = 0; i < rule_count; ++i)
			{
				text = text + "<span class='ruleweight'>" + rules[i].name + ": " + rules[i].weight.toString() + "</span> ";
			}
			$(item).html(text);
		}
	);
}

function correctTimestamps()
{
	$(".timestamp").each(
		function (index, item)
		{
			var twodigits = function(x) {if (x >= 10) return x; return "0" + x;}
			var date = new Date(parseInt($(item).html()) * 1000);
			$(item).html(twodigits(date.getDate()) + "." + twodigits(date.getMonth()) + ". " + twodigits(date.getHours()) + ":" + twodigits(date.getMinutes()));
		}
	);
}