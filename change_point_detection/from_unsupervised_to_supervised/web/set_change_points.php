<!doctype html>

<?php
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
		$sql = "INSERT INTO users (email) VALUES ('$email') RETURNING id";
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
	header("Location: ./set_change_points.php");
	exit;
}

//prioritizes time series that no one have seen
$sql = "SELECT time_series.id, time_series.date_start, time_series.date_end, time_series.csv_path FROM time_series WHERE time_series.id NOT IN (SELECT change_points.id_time_series from change_points)";
$ret = pg_query($db, $sql);
if(!$ret) { echo pg_last_error($db); exit; }
if(pg_num_rows($ret) == 0)
{
	//select all time series that the user didn't see
	$sql = "SELECT time_series.id, time_series.date_start, time_series.date_end, time_series.csv_path FROM time_series WHERE time_series.id NOT IN (SELECT change_points.id_time_series from change_points WHERE change_points.id_user='".$_SESSION['id_user']."')";
	$ret = pg_query($db, $sql);
	if(!$ret) { echo pg_last_error($db); exit; }
}
if(pg_num_rows($ret) == 0)
{
	echo "You've seen all available time series.";
	exit;
}
$available_ts_id = array();
$available_ts_date_start = array();
$available_ts_date_end = array();
$available_ts_csv_path = array();
while($row = pg_fetch_assoc($ret))
{
	array_push($available_ts_id, $row["id"]);
	array_push($available_ts_date_start, $row["date_start"]);
	array_push($available_ts_date_end, $row["date_end"]);
	array_push($available_ts_csv_path, $row["csv_path"]);
}
//randomly select an available time series
$rand_idx = rand(0, count($available_ts_id)-1);
$_SESSION["id_time_series"] = $available_ts_id[$rand_idx];
$date_start = $available_ts_date_start[$rand_idx]; 
$date_end = $available_ts_date_end[$rand_idx]; 
$csv_path = $available_ts_csv_path[$rand_idx]; 

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

<html>
<head>
<title>Set Change Points</title>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body {
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
	padding: 6px 6px;
	width: 180px;
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

<script src="./libs/d3.min.js"></script>
<script src="./libs/jquery-1.12.3.min.js"></script>

<div>
<div id="div_plot" align="left" style="float: left">
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

var date_start = new Date("<?php echo "$date_start"; ?>");
var date_end = new Date("<?php echo "$date_end"; ?>").addDays(1);
var date_array = getDates(date_start, date_end);
/*
console.log("date_start=" + date_start);
console.log("date_end=" + date_end);
console.log(date_array);
*/

/*
var margin = {top: 20, right: 20, bottom: 60, left: 40},
	width = 960 - margin.left - margin.right,
	height = 600 - margin.top - margin.bottom;
*/

var page_width = $(window).width(), page_height = $(window).height();
	margin = {top: 20, right: 20, bottom: 60, left: 40},
	width = page_width - margin.left - margin.right - 230,
	height = page_height - margin.top - margin.bottom - 12;
width = Math.max(width, 900);
height = Math.max(height, 400);

var x = d3.time.scale()
	.range([0, width]);
var y = d3.scale.linear()
	.range([height, 0]);

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
	.tickValues([0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]);	

var svg = d3.select("#div_plot").append("svg")
	.attr("width", width + margin.left + margin.right)
	.attr("height", height + margin.top + margin.bottom)
	.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

x.domain([date_array[0], date_array[date_array.length - 1]]);
y.domain([-0.02, 1.02]);

svg.append("text")
	.style("font-size", "13px")
	.attr("class", "y label")
	.attr("text-anchor", "end")
	.attr("dx", "-24em")
	.attr("dy", "-2.3em")
	.attr("transform", "rotate(-90)")
	.text("loss fraction");

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
		
	svg.append("circle")
		.attr("class", "dot")
		.attr("r", 1.0)
		.attr("cx", x(dt_array[i]))
		.attr("cy", y(loss_array[i]))
}
//add area to handle mouse events
svg.append("rect")
	.attr("class", "overlay")
	.attr("width", width)
	.attr("height", height)
	.on("click", add_change_point);

var change_points_array = []
function add_change_point()
{
	var px = x.invert(d3.mouse(this)[0]);
	var py = y.invert(d3.mouse(this)[1]);
	
	change_points_array.push(px)
		
	svg.append("line")
		.attr("id", "change_point_" + change_points_array.length)
		.attr("x1", x(px))		
		.attr("y1", y(y.domain()[0]))
		.attr("x2", x(px))
		.attr("y2", y(y.domain()[1]))
		.style("stroke-width", 2)
		.style("stroke", "red")
		.style("fill", "none")
	
	//console.log("x=" + px);
	//window.alert("x=" + px + ", y=" + py);
}

function remove_change_point()
{
	if(change_points_array.length > 0)
	{
		svg.selectAll("#change_point_" + change_points_array.length).remove();
		change_points_array.pop()	
	}
}

function save_change_points()
{
	json_change_points_array = JSON.stringify(change_points_array);
	//window.alert(json_change_points_array);
		
	$("<form id='change_points_form' method='post' action='save_change_points.php'></form>").appendTo("body");
	$("<input type='hidden' name='json_change_points_array' value='" + json_change_points_array + "'>").appendTo("#change_points_form");
	$("#change_points_form").submit();
}

</script>
</div>
<div align="left" style="float: left">
<div style="padding-top:6px">
<button type="button" class="button" onclick="remove_change_point()">Remove last change point</button><br>
</div>
<div style="padding-top:6px">
<button type="button" class="button" onclick="save_change_points()">Save and next</button>
</div>
</div>
<body>
</html>
