<?php
session_start();

if(!isset($_SESSION["id_user"]) || !isset($_SESSION["id_time_series"]))
{
	header("Location: ./index.html");
	exit;
}

$db = pg_connect("host=localhost dbname=from_unsupervised_to_supervised user=postgres password=admin");
if(!$db) die("Error : Unable to connect to database.\n");

$change_points_array = json_decode($_POST["json_change_points_array"]);
$change_points_plot_type_array = json_decode($_POST["json_change_points_plot_type_array"]);
$classification_time_seconds = $_POST["classification_time_seconds"];
$str_change_points_array = implode(",", $change_points_array);
$str_change_points_plot_type_array = implode(",", $change_points_plot_type_array);

/*
echo "change_points_array[0]=$change_points_array[0]";
echo "id_user=".$_SESSION["id_user"]."\n";
echo "id_time_series=".$_SESSION["id_time_series"]."\n";
echo "str_change_points_array=$str_change_points_array";
*/

$sql = "INSERT INTO change_points (id_user, id_time_series, change_points, change_points_plot_type, insertion_time, classification_time_seconds) VALUES ('".$_SESSION["id_user"]."', '".$_SESSION["id_time_series"]."', '$str_change_points_array', '$str_change_points_plot_type_array', CURRENT_TIMESTAMP, '$classification_time_seconds')";
$ret = pg_query($db, $sql);
if(!$ret)
{
	echo pg_last_error($db);
	exit;
}

header("Location: ./set_change_points.php");
exit;

?>
