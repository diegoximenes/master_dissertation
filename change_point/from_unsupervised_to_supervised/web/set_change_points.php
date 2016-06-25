<?php
/*
ALERT: database store change point datetime in UTC. CSV and javascript handle in local time
*/
?>

<!doctype html>
<html>
<head>
<title>Set Change Points</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">

<script src="./libs/d3.min.js"></script>
<script src="./libs/jquery-1.12.3.min.js"></script>
<script src="./libs/bootstrap.min.js"></script>
<link rel="stylesheet" href="./libs/bootstrap.min.css">

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
	opacity: 0.1;
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

ul li 
{
	padding-top: 10px;
}

</style>
</head>

<?php
$number_of_users_per_time_series = 10;

session_start();

$db = pg_connect("host=localhost dbname=from_unsupervised_to_supervised user=postgres password=admin");
if(!$db) die("Error : Unable to connect to database.\n");

if(isset($_POST["email"]))
{
	$email = $_POST["email"];

	//set user identification
	$sql = "SELECT id FROM users WHERE email='$email'";
	$ret = pg_query($db, $sql);
	if(!$ret) { echo pg_last_error($db); exit; }

	//add new user
	if(!pg_num_rows($ret)) 
	{
		$sql = "INSERT INTO users (email, insertion_time) VALUES ('$email', CURRENT_TIMESTAMP) RETURNING id";
		$ret = pg_query($db, $sql);
		if(!$ret)
		{
			echo pg_last_error($db);
			exit;
		}
	}
	$row = pg_fetch_assoc($ret);
	$_SESSION["id_user"] = $row["id"];
}
else if(!isset($_SESSION["id_user"]))
{
	header("Location: ./index.html");
	exit;
}

//prioritizes time series that have almost the necessary number of classifications
$sql = "
SELECT possible_time_series_table.id_time_series, date_start, date_end, csv_path, COUNT(id_user) AS count_id_user 
FROM (SELECT time_series.id as id_time_series, date_start, date_end, csv_path FROM time_series WHERE time_series.id NOT IN (SELECT change_points.id_time_series FROM change_points WHERE change_points.id_user = '".$_SESSION['id_user']."')) AS possible_time_series_table 
LEFT JOIN change_points 
ON possible_time_series_table.id_time_series = change_points.id_time_series 
GROUP BY possible_time_series_table.id_time_series, date_start, date_end, csv_path 
ORDER BY COUNT(id_user) ASC, possible_time_series_table.id_time_series ASC
";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
if(pg_num_rows($ret) == 0)
{
	echo "<center><h1>Thank you, you have classified all available time series.</h1></center>";
	exit;
}
//echo "id_user=".$_SESSION['id_user']."<br>";
$selected_time_series = false;
while($row = pg_fetch_assoc($ret))
{
	if(($selected_time_series == false) || ($row["count_id_user"] < $number_of_users_per_time_series))
	{
		//echo $row['id_time_series'].",".$row['count_id_user']."<br>";
		$selected_time_series = true;
		$_SESSION["id_time_series"] = $row["id_time_series"];
		$date_start = $row["date_start"];
		$date_end = $row["date_end"];
		$csv_path = $row["csv_path"]; 
	}
	if($row["count_id_user"] >= $number_of_users_per_time_series) break;
}

//get number of time series
$sql = "SELECT COUNT(*) AS cnt_time_series FROM time_series";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
$row = pg_fetch_assoc($ret);
$cnt_time_series = $row["cnt_time_series"];

//get number classfied time series by current user
$sql = "SELECT COUNT(id_time_series) AS cnt_classified_time_series FROM change_points WHERE change_points.id_user='".$_SESSION['id_user']."'";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
$row = pg_fetch_assoc($ret);
$cnt_classified_time_series = $row["cnt_classified_time_series"];

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

<body onload="set_start_time();">

<div id="div_plot" align="left" style="float: left">
<div id="div_plot_linear"></div>
<div id="div_plot_polypoint"></div>
<div id="div_plot_log"></div>
</div>

<script>

var compress_time_series = true;
var min_loss_log = 0.004; 

$("#div_plot_polypoint").hide();
$("#div_plot_log").hide();

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

var start_time_epoch;
function set_start_time()
{
	var d =  new Date();
	start_time_epoch = d.getTime()/1000;
}

var date_start = new Date("<?php echo "$date_start"; ?>");
var date_end = new Date("<?php echo "$date_end"; ?>").addDays(1);
var date_array = getDates(date_start, date_end);

//get data
var dt_array = <?php echo $js_dt_array; ?>;
var loss_array = <?php echo $js_loss_array; ?>;
var pt_array = new Array();
for(i=0; i<dt_array.length; ++i)
{
	var format = d3.time.format("%Y-%m-%d %H:%M:%S");
	dt_array[i] = format.parse(dt_array[i].slice(0,19));
	
	//ignore point outside date range
	if((dt_array[i].getTime() < date_start.getTime()) || (dt_array[i].getTime() >= date_end.getTime())) continue;

	pt_array.push({dt: dt_array[i], loss: loss_array[i]});
}
pt_array.sort(function cmp(pt1, pt2) { return (pt1.dt.getTime() - pt2.dt.getTime()); });

var button_width = 220;
var page_width = $(window).width(), page_height = $(window).height(),
	margin = {top: 20, right: 20, bottom: 40, left: 45},
	width = page_width - margin.left - margin.right - button_width,
	height = page_height - margin.top - margin.bottom - 10;

function plot(id_div_plot, plot_type)
{
	//define scales
	var x;
	if(compress_time_series) x = d3.scale.linear().range([0, width]);
	else x = d3.time.scale().range([0, width]);
	
	var y = d3.scale.linear();
	if(plot_type == "polypoint") y.range([height, height/2.0, 0.0]);
	else y.range([height, 0]);
	
	if(!compress_time_series) x.domain([date_array[0], date_array[date_array.length - 1]]);
	else x.domain([0, pt_array.length - 1]);

	if(plot_type == "linear") y.domain([-0.02, 1.02])
	else if(plot_type == "polypoint") y.domain([-0.004, 0.1, 1.02])
	else if(plot_type == "band") y.domain([-0.5, 3.5])
	else if(plot_type == "log")
	{
		y = d3.scale.log()
			.domain([0.0036, 1.01])
			.range([height, 0])
	}
	
	//define axis
	var xAxis = d3.svg.axis()
		.scale(x)
		.orient("bottom")
		.tickSize(-height, 0, 0)
	if(!compress_time_series)
	{
		xAxis
		.tickFormat(d3.time.format("%d/%m"))
		.tickValues(date_array);
	}
	else
	{ 
		var tick_values = [];
		for(i=0; i<pt_array.length; i+=20) tick_values.push(i);
		xAxis.tickValues(tick_values);
	}

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

	//add svg	
	var svg = d3.select("#" + id_div_plot).append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
			.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	//add axis label
	svg.append("text")
		.style("font-size", "13px")
		.style("font-weight", "normal")
		.attr("class", "y label")
		.attr("text-anchor", "end")
		.attr("dy", "-2.3em")
		.attr("transform", "rotate(-90)")
		.text("loss fraction");
	
	//add axis label
	if(compress_time_series)
	{
		svg.append("text")
		.style("font-size", "13px")
		.style("font-weight", "normal")
		.attr("class", "y label")
		.attr("transform", "translate(" + width + "," + (margin.top + height) + ")")
		.attr("dx", "-2.3em")
		.attr("dy", "0.8em")
		.text("time");
	}
	
	//add axis
	svg.append("g")
		.attr("class", "x axis")	
		.attr("transform", "translate(0," + height + ")")
		.call(xAxis)
		.selectAll("text")
			.attr("dy", "1.0em");
			//.attr("transform", "rotate(-65)");
	svg.append("g")
		.attr("class", "y axis")
		.call(yAxis);
	
	//add points
	for(i=0; i<pt_array.length; ++i)
	{
		var dt = pt_array[i].dt;
		var loss = pt_array[i].loss;
			
		var cx;
		if(!compress_time_series) cx = x(dt);
		else cx = x(i);
	
		var cy;
		if(plot_type == "band") cy = y(get_band(loss));
		else if(plot_type == "log") cy = y(Math.max(min_loss_log, parseFloat(loss)));
		else cy = y(loss);
		
		svg.append("circle")
			.attr("class", "dot")
			.attr("r", 1.3)
			.attr("cx", cx)
			.attr("cy", cy);
	}
	
	var y1 = y(y.domain()[0]), y2 = y(y.domain()[1]);
	if(plot_type == "polypoint") y2 = y(y.domain()[2]);
	var mouse_line = svg.append("g")
						.datum({x: null, visible: false});
	mouse_line.append("line")
		.attr("x1", 0)
		.attr("y1", y1)
		.attr("x2", 0)
		.attr("y2", y2)
		.style("stroke-width", 2)
		.style("stroke", "#009999")
		.style("fill", "none");
	mouse_line.update = function()
	{
		this.attr("transform", function(d)
		{
			if(d.visible == true) return "translate(" + d.x + ", 0)";
		})
		.style("opacity", function(d) { return d.visible ? 1 : 0});
	}
	mouse_line.update();

	//add rect to handle mouse events
	svg.append("rect")
		.attr("id", "rect_mouse_events")
		.attr("class", "overlay")
		.attr("width", width)
		.attr("height", height)
		.on("mousedown", add_change_point)
		.on("mousemove", handle_mouse_move)
		.on("mouseover", handle_mouse_move)
		.on("mouseout", handle_mouse_out);
	
	return [x, y, svg, mouse_line];
}

var ret_linear = plot("div_plot_linear", "linear");
var ret_polypoint = plot("div_plot_polypoint", "polypoint");
var ret_log = plot("div_plot_log", "log");

var x_linear = ret_linear[0], y_linear = ret_linear[1], svg_linear = ret_linear[2], mouse_line_linear = ret_linear[3];
var x_polypoint = ret_polypoint[0], y_polypoint = ret_polypoint[1], svg_polypoint = ret_polypoint[2], mouse_line_polypoint = ret_polypoint[3];
var x_log = ret_log[0], y_log = ret_log[1], svg_log = ret_log[2], mouse_line_log = ret_log[3];

function handle_mouse_out()
{
	mouse_line_linear.datum({x: null, visible: false});
	mouse_line_linear.update();
	
	mouse_line_polypoint.datum({x: null, visible: false});
	mouse_line_polypoint.update();
	
	mouse_line_log.datum({x: null, visible: false});
	mouse_line_log.update();
}

function handle_mouse_move()
{
	var px = x_linear.invert(d3.mouse(this)[0]);
	var py = y_linear.invert(d3.mouse(this)[1]);
	
	mouse_line_linear.datum({x: x_linear(px), visible: true});
	mouse_line_linear.update();
	
	mouse_line_polypoint.datum({x: x_polypoint(px), visible: true});
	mouse_line_polypoint.update();
	
	mouse_line_log.datum({x: x_log(px), visible: true});
	mouse_line_log.update();
}

var change_points_array = [], change_points_plot_type_array = [];
function add_change_point()
{
	var plot_type = document.getElementById("plot_type").value;
	
	var px = x_linear.invert(d3.mouse(this)[0]);
	var py = y_linear.invert(d3.mouse(this)[1]);

	if(compress_time_series) change_points_array.push(pt_array[Math.min(pt_array.length-1, Math.round(px))].dt);
	else change_points_array.push(px);
	change_points_plot_type_array.push(plot_type);
	//console.log(change_points_array);
	//console.log(change_points_plot_type_array);
	
	svg_linear.append("line")
		.attr("id", "change_point_" + change_points_array.length)
		.attr("x1", x_linear(px))		
		.attr("y1", y_linear(y_linear.domain()[0]))
		.attr("x2", x_linear(px))
		.attr("y2", y_linear(y_linear.domain()[1]))
		.style("stroke-width", 2)
		.style("stroke", "red")
		.style("fill", "none");
	svg_polypoint.append("line")
		.attr("id", "change_point_" + change_points_array.length)
		.attr("x1", x_polypoint(px))		
		.attr("y1", y_polypoint(y_polypoint.domain()[0]))
		.attr("x2", x_polypoint(px))
		.attr("y2", y_polypoint(y_polypoint.domain()[2]))
		.style("stroke-width", 2)
		.style("stroke", "red")
		.style("fill", "none");
	svg_log.append("line")
		.attr("id", "change_point_" + change_points_array.length)
		.attr("x1", x_log(px))		
		.attr("y1", y_log(y_log.domain()[0]))
		.attr("x2", x_log(px))
		.attr("y2", y_log(y_log.domain()[1]))
		.style("stroke-width", 2)
		.style("stroke", "red")
		.style("fill", "none");
}

function remove_change_point()
{
	if(change_points_array.length > 0)
	{
		svg_linear.selectAll("#change_point_" + change_points_array.length).remove();
		svg_polypoint.selectAll("#change_point_" + change_points_array.length).remove();
		svg_log.selectAll("#change_point_" + change_points_array.length).remove();
		change_points_array.pop();
		change_points_plot_type_array.pop();
	}
}

function clear_page(show_loading)
{
	svg_linear.selectAll("overlay").remove();
	svg_polypoint.selectAll("overlay").remove();
	svg_log.selectAll("overlay").remove();
	$("#div_button").empty();
	$("#div_plot").empty();
	if(show_loading) $("#div_loading").html("<h1>loading</h1>");
}

function save_change_points()
{
	clear_page(true);
	
	var d = new Date();
	var end_time_epoch = d.getTime()/1000;
	var classification_time_seconds = end_time_epoch - start_time_epoch;
		
	json_change_points_array = JSON.stringify(change_points_array);
	json_change_points_plot_type_array = JSON.stringify(change_points_plot_type_array);
	//window.alert(json_change_points_array);
		
	$("<form id='change_points_form' method='post' action='save_change_points.php'></form>").appendTo("body");
	$("<input type='hidden' name='json_change_points_array' value='" + json_change_points_array + "'>").appendTo("#change_points_form");
	$("<input type='hidden' name='json_change_points_plot_type_array' value='" + json_change_points_plot_type_array + "'>").appendTo("#change_points_form");
	$("<input type='hidden' name='classification_time_seconds' value='" + Math.round(classification_time_seconds) + "'>").appendTo("#change_points_form");
	$("#change_points_form").submit();
}

function change_plot_type()
{
	var new_plot_type = document.getElementById("plot_type").value;
	if(new_plot_type == "linear")
	{
		$("#div_plot_polypoint").hide();
		$("#div_plot_log").hide();
		$("#div_plot_linear").show();
	}
	else if(new_plot_type == "polypoint")
	{
		$("#div_plot_linear").hide();
		$("#div_plot_log").hide();
		$("#div_plot_polypoint").show();
	}
	else if(new_plot_type == "log")
	{
		$("#div_plot_linear").hide();
		$("#div_plot_polypoint").hide();
		$("#div_plot_log").show();
	}
}

$(window).on('beforeunload', function() { clear_page(false); });

</script>

<div id="div_button" align="left" style="float: left; padding-top: 10px;">

<table>
<tr>
<td>
<font size="3">Scale:</font>&emsp;
</td>
<td>
<select id="plot_type" class="form-control" onchange="change_plot_type();" style="width: 120px;">
<option value="linear">linear</option>
<option value="polypoint">polypoint</option>
<option value="log">log</option>
</select>
</td>
</tr>
</table>

<div style="padding-top:120px">
<button type="button" class="btn btn-primary" style="width: 210px;" data-toggle="modal" data-target=".bs-example-modal-lg">Show tips</button><br>
</div>

<div data-dismiss="modal" class="modal fade bs-example-modal-lg container-fluid" tabindex="-1" role="dialog">
	<div class="modal-dialog modal-lg" role="">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
				<h3 class="modal-title">Tips</h3>
			</div>
			<div class="modal-body" id="tips" style="font-size: 16px;"></div>
		</div>
	</div>
</div>
<script> 
$(function(){ $("#tips").load("tips.html"); });
</script> 

<div style="padding-top:6px">
<button type="button" class="btn btn-primary" style="width: 210px;" onclick="remove_change_point();">Remove last change point</button><br>
</div>

<div style="padding-top:6px">
<button type="button" class="btn btn-primary" style="width: 210px;" onclick="save_change_points();">Save and next</button>
</div>

<div style="padding-top:30px; width:210px">
<font size="3">
Number of classified time series: <?php echo "$cnt_classified_time_series of $cnt_time_series"; ?>
</font>
</div>

</div>

<div id="div_loading" align="center">
</div>

<body>
</html>
