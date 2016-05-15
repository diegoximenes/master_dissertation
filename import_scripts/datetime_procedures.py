import sys, os, calendar, pytz
from datetime import datetime, timedelta

def generate_dt_list(dt_start, dt_end):
	l = []
	for day in range((dt_end - dt_start).days + 1):
		dt_day = dt_start + timedelta(days = day)
		for hour in range(24):
			dt_hour = dt_day + timedelta(hours = hour)
			l.append(dt_hour)
	return l
	
def from_utc_to_sp(dt):
	dt_utc = pytz.utc.localize(dt)
	dt_sp = dt_utc.astimezone(pytz.timezone("America/Sao_Paulo"))
	return dt_sp
def from_sp_to_utc(dt):
	dt_sp = pytz.timezone("America/Sao_Paulo").localize(dt)
	dt_utc = dt_sp.astimezone(pytz.utc)
	return dt_sp

def from_datetime_to_epoch(dt):
	return (dt - datetime(1970, 1, 1)).total_seconds()
            
def get_datetime_sp(str_datetime):
	date = str_datetime.split()[0]
	time = str_datetime.split()[1]
	year, month, day = int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2])
	hour, minute, second = int(time.split(":")[0]), int(time.split(":")[1]), int(time.split(":")[2])

	return from_utc_to_sp(datetime(year, month, day, hour, minute, second))

def from_strDatetime_to_datetime(str_datetime):
	date = str_datetime.split()[0]
	time = str_datetime.split()[1]
	year, month, day = int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2])
	hour, minute, second = int(time.split(":")[0]), int(time.split(":")[1]), int(time.split(":")[2].split("-")[0])
	return datetime(year, month, day, hour, minute, second)
