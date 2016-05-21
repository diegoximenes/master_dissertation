<!doctype html>

<html>
<head>
<title>Set Change Points</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body 
{
  font: 10px sans-serif;
}

.axis path,
.axis line 
{
	fill: none;
	stroke: #000;
	shape-rendering: crispEdges;
}

.tick line
{
	opacity: 0.06;
}

.dot 
{
	stroke: #000;
}

.overlay 
{
	fill: none;
	pointer-events: all;
}

.button {
	background-color: #008CBA;
	border: none;
	color: white;
	text-align: center;
	text-decoration: none;
	display: inline-block;
	border-radius: 4px;
	border: 2px solid #008CBA;
	cursor: pointer;
	font-size: 13px;
	-webkit-transition-duration: 0.4s; /* Safari */
    transition-duration: 0.4s;
}
.button:hover
{
	color: #008CBA;
	background-color: white;
	border: 2px solid #008CBA;
}

</style>
</head>
<body>
<form method="get" action="plot_ts.php">
<?php

$db = pg_connect("host=localhost dbname=from_unsupervised_to_supervised user=postgres password=admin");
if(!$db) die("Error : Unable to connect to database.\n");

$sql = "SELECT id, mac, server FROM time_series";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
echo "<select name='ts_id'>";
while($row = pg_fetch_assoc($ret))
{
	if(isset($_GET["ts_id"]) && $_GET["ts_id"] == $row["id"]) $selected = "selected";
	else $selected = "";
	echo "<option value='".$row["id"]."' $selected>".$row["server"]."_".$row["mac"]."</option>";
}
echo "</select>";

$selected_linear = $selected_linear2 = $selected_polypoint = $selected_log = $selected_band = $selected_pallete = "";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "linear") $selected_linear = "selected";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "linear2") $selected_linear2 = "selected";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "polypoint") $selected_polypoint = "selected";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "log") $selected_log = "selected";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "band") $selected_band = "selected";
if(isset($_GET["plot_type"]) && $_GET["plot_type"] == "jet") $selected_jet = "selected";
?>

<select name="plot_type">
<option value="linear" <?php echo $selected_linear; ?>>linear</option>
<option value="linear2" <?php echo $selected_linear2; ?>>linear2</option>
<option value="polypoint" <?php echo $selected_polypoint; ?>>polypoint</option>
<option value="log" <?php echo $selected_log; ?>>log</option>
<option value="band" <?php echo $selected_band; ?>>band</option>
<!--<option value="jet" <?php echo $selected_jet; ?>>jet</option>-->
</select>

<input type="submit" class="button" value="Plot"></input>
</form>

<div>
<div id="div_plot1" align="left" style="float: left"></div>
<div id="div_plot2" align="left" style="float: left"></div>
</div>

<?php

if(!isset($_GET["ts_id"]) || !isset($_GET["plot_type"])) exit;

$sql = "SELECT date_start, date_end, csv_path FROM time_series WHERE id='".$_GET["ts_id"]."'";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
$row = pg_fetch_assoc($ret);
$date_start = $row["date_start"];
$date_end = $row["date_end"];
$csv_path = $row["csv_path"];

//parse csv file
$dt_array = array();
$loss_array = array();
$csv_file = file($csv_path);
for($i=1; $i<count($csv_file); ++$i)
{
	$row = str_getcsv($csv_file[$i], ",");
	array_push($dt_array, $row[1]);
	array_push($loss_array, $row[2]);
}
$js_dt_array = json_encode($dt_array);
$js_loss_array = json_encode($loss_array);
?>

<script src="./libs/d3.min.js"></script>
<script src="./libs/jquery-1.12.3.min.js"></script>

<script>

Date.prototype.addDays = function(days) {
    var dat = new Date(this.valueOf())
    dat.setDate(dat.getDate() + days);
    return dat;
}
function getDates(startDate, stopDate) {
    var dateArray = new Array();
    var currentDate = startDate;
    while (currentDate <= stopDate) {
        dateArray.push( new Date (currentDate) )
        currentDate = currentDate.addDays(1);
    }
    return dateArray;
}

function get_band(loss)
{
	if(loss <= 0.02) return 0;
	if(loss <= 0.05) return 1;
	if(loss <= 0.1) return 2;
	return 3;
}

var plot_type = "<?php echo $_GET["plot_type"]; ?>";
var date_start = new Date("<?php echo "$date_start"; ?>");
var date_end = new Date("<?php echo "$date_end"; ?>").addDays(1);
var date_array = getDates(date_start, date_end);
/*
console.log("date_start=" + date_start);
console.log("date_end=" + date_end);
console.log(date_array);
*/

function get_colour(v, vmin, vmax)
{
	var r = 1.0, g = 1.0, b = 1.0;
	var dv;
	
	if(v < vmin) v = vmin;
	if(v > vmax) v = vmax;
	dv = 1.0*(vmax - vmin);
	
	console.log("dv=" + dv);
		
	if (v < (vmin + 0.25 * dv)) 
	{
		r = 0;
		g = 4.0 * (v - vmin) / dv;
	} 
	else if(v < (vmin + 0.5 * dv))
	{
		r = 0;
		b = 1 + 4.0 * (vmin + 0.25 * dv - v) / dv;
	}
	else if(v < (vmin + 0.75 * dv)) 
	{
		r = 4.0 * (v - vmin - 0.5 * dv) / dv;
		b = 0;
	} 
	else 
	{
		g = 1 + 4.0 * (vmin + 0.75 * dv - v) / dv;
		b = 0;
	}

	r = Math.round(r*255);
	g = Math.round(g*255);
	b = Math.round(b*255);

	return [r, g, b];
}

if(plot_type == "jet")
{

	var page_width = $(window).width(), page_height = $(window).height(),
		margin = {top: 20, right: 20, bottom: 60, left: 55},
		width = page_width - margin.left - margin.right - 230,
		height = page_height - margin.top - margin.bottom - 12;
	
	var x = d3.scale.ordinal()
		.rangeRoundBands([0, width], .1);

	var y = d3.scale.linear()
		.rangeRound([height, 0]);

	var svg = d3.select("body").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	
	for(i=0; i<=100; ++i)
	{
	var rgb = get_colour(i*0.01, 0.0, 1.0);
	console.log("rgb=" + rgb);
	svg.append("rect")
		.attr("width", x.rangeBand())
		.attr("y", i)
		.attr("height", 4)
		.style("fill", "rgb(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + ")");
	}
}	
else if(plot_type == "linear2")
{
	var max_y_plot2 = 0.1;

	var page_width = $(window).width(), page_height = $(window).height(),
		margin = {top: 20, right: 20, bottom: 60, left: 55},
		width = page_width - margin.left - margin.right - 230,
		height1 = page_height/2.0 - margin.top - margin.bottom - 12,
		height2 = page_height/2.0 - margin.top - margin.bottom - 12;

	var x1 = d3.time.scale()
		.range([0, width]);
	var x2 = d3.time.scale()
		.range([0, width]);
	var y1 = d3.scale.linear()
		.range([height1, 0]);
	var y2 = d3.scale.linear()
		.range([height2, 0]);

	var xAxis1 = d3.svg.axis()
		.scale(x1)
		.orient("bottom")
		.tickSize(-height1, 0, 0)
		.tickFormat(d3.time.format("%d/%m"))
		.tickValues(date_array);
	var xAxis2 = d3.svg.axis()
		.scale(x2)
		.orient("bottom")
		.tickSize(-height2, 0, 0)
		.tickFormat(d3.time.format("%d/%m"))
		.tickValues(date_array);
	
	var yAxis1 = d3.svg.axis()
		.scale(y1)
		.orient("left")
		.tickSize(-width, 0, 0)
		.tickFormat(d3.format(",.2f"))
		.tickValues([0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]);
	var yAxis2 = d3.svg.axis()
		.scale(y2)
		.orient("left")
		.tickSize(-width, 0, 0)
		.tickValues([0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10])
		.tickFormat(function(d, i)
		{
			if(d < max_y_plot2) return d;
			else return "[" + max_y_plot2 + ", 1.00]";
		});

	var svg1 = d3.select("#div_plot1").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height1 + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	var svg2 = d3.select("#div_plot2").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height2 + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	x1.domain([date_array[0], date_array[date_array.length - 1]]);
	x2.domain([date_array[0], date_array[date_array.length - 1]]);
	
	y1.domain([-0.02, 1.02]);
	var delta = 0.002
	y2.domain([0.0 - delta, max_y_plot2 + delta]);
		
	svg1.append("g")
		.attr("class", "y axis")
		.call(yAxis1)
	svg2.append("g")
		.attr("class", "y axis")
		.call(yAxis2)

	svg1.append("g")
		.attr("class", "x axis")	
		.attr("transform", "translate(0," + height1 + ")")
		.call(xAxis1)
		.selectAll("text")
			.attr("dx", "-2.1em")
			.attr("transform", "rotate(-65)");

	svg2.append("g")
		.attr("class", "x axis")	
		.attr("transform", "translate(0," + height2 + ")")
		.call(xAxis2)
		.selectAll("text")
			.attr("dx", "-2.1em")
			.attr("transform", "rotate(-65)");


	//add points
	var dt_array = <?php echo $js_dt_array; ?>;
	var loss_array = <?php echo $js_loss_array; ?>;
	for(i=0; i<dt_array.length; ++i)
	{
		var format = d3.time.format("%Y-%m-%d %H:%M:%S");
		dt_array[i] = format.parse(dt_array[i].slice(0,19));
		
		//ignore point outside date range
		if((dt_array[i].getTime() < date_start.getTime()) || (dt_array[i].getTime() >= date_end.getTime())) continue;
		
		var cx1 = x1(dt_array[i]);
		var cx2 = x2(dt_array[i]);
		var cy1 = y1(loss_array[i]);
		var cy2 = y2(Math.min(max_y_plot2, loss_array[i]));
			
		svg1.append("circle")
			.attr("class", "dot")
			.attr("r", 1.1)
			.attr("cx", cx1)
			.attr("cy", cy1);

		svg2.append("circle")
			.attr("class", "dot")
			.attr("r", 1.1)
			.attr("cx", cx2)
			.attr("cy", cy2);
	}

}
else
{
	var page_width = $(window).width(), page_height = $(window).height();
		margin = {top: 20, right: 20, bottom: 60, left: 55},
		width = page_width - margin.left - margin.right - 230,
		height = page_height - margin.top - margin.bottom - 12;
	width = Math.max(width, 900);
	height = Math.max(height, 400);

	var min_loss_log = 0.004;

	var x = d3.time.scale()
		.range([0, width]);
	var y = d3.scale.linear();
	if(plot_type == "polypoint") y.range([height, height/2.0, 0.0]);
	else y.range([height, 0]);

	if(plot_type == "linear") y.domain([-0.02, 1.02])
	else if(plot_type == "polypoint") y.domain([-0.002, 0.1, 1.02])
	else if(plot_type == "band") y.domain([-0.5, 3.5])
	else if(plot_type == "log")
	{
		y = d3.scale.log()
			.domain([0.003, 1.01])
			.range([height, 0])
	}

	var xAxis = d3.svg.axis()
		.scale(x)
		.orient("bottom")
		.tickSize(-height, 0, 0)
		.tickFormat(d3.time.format("%d/%m"))
		.tickValues(date_array);
	var yAxis = d3.svg.axis()
		.scale(y)
		.orient("left")
		.tickSize(-width, 0, 0)
		.tickFormat(d3.format(",.2f"))
	if(plot_type == "linear" || plot_type == "polypoint") yAxis.tickValues([0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]);	
	else if(plot_type == "band")
	{
		yAxis.tickValues([0, 1, 2, 3]);
		yAxis.tickFormat(function(d, i)
		{
			if(d == 0) return "[0.00, 0.02]";
			else if(d == 1) return "(0.02, 0.05]";
			else if(d == 2) return "(0.05, 0.10]";
			else if(d == 3) return "(0.10, 1.00]";
		});
	}
	else if(plot_type == "log")
	{
		yAxis.tickValues([min_loss_log, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]);	
		yAxis.tickFormat(function(d, i)
		{
			if(d == min_loss_log) return "0.00";
			else return d;
		});
	}

	var svg = d3.select("#div_plot1").append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	x.domain([date_array[0], date_array[date_array.length - 1]]);

	svg.append("text")
		.style("font-size", "13px")
		.attr("class", "y label")
		.attr("text-anchor", "end")
		.attr("dx", "-24em")
		.attr("dy", "-2.3em")
		.attr("transform", "rotate(-90)")

	svg.append("g")
		.attr("class", "x axis")	
		.attr("transform", "translate(0," + height + ")")
		.call(xAxis)
		.selectAll("text")
			.attr("dx", "-2.1em")
			.attr("transform", "rotate(-65)");
	svg.append("g")
		.attr("class", "y axis")
		.call(yAxis)

	//add points
	var dt_array = <?php echo $js_dt_array; ?>;
	var loss_array = <?php echo $js_loss_array; ?>;
	for(i=0; i<dt_array.length; ++i)
	{
		var format = d3.time.format("%Y-%m-%d %H:%M:%S");
		dt_array[i] = format.parse(dt_array[i].slice(0,19));
		
		//ignore point outside date range
		if((dt_array[i].getTime() < date_start.getTime()) || (dt_array[i].getTime() >= date_end.getTime())) continue;
		
		var cx = x(dt_array[i]);
		var cy;
		if(plot_type == "band") cy = y(get_band(loss_array[i]));
		else if(plot_type == "log") cy = y(Math.max(min_loss_log, parseFloat(loss_array[i])));
		else cy = y(loss_array[i]);
			
		svg.append("circle")
			.attr("class", "dot")
			.attr("r", 1.1)
			.attr("cx", cx)
			.attr("cy", cy);
	}
}
</script>
<body>
</html>
