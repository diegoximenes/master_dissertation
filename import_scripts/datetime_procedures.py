import sys, os, calendar, pytz
from datetime import datetime

def get_date_dir(date):
	return str(date[0]).zfill(2) + "_" + str(date[1])

def from_utc_to_sp(dt):
	dt_utc = pytz.utc.localize(dt)
	dt_sp = dt_utc.astimezone(pytz.timezone("America/Sao_Paulo"))
	return dt_sp
def from_sp_to_utc(dt):
	dt_sp = pytz.timezone("America/Sao_Paulo").localize(dt)
	dt_utc = dt_sp.astimezone(pytz.utc)
	return dt_sp

def get_month_days(year, month):
	l = []
	cal = calendar.Calendar()
	for p in cal.itermonthdays2(year, month):
		day = p[0]
		#ignore days of previous month
		if day != 0: l.append(day)
	return l          

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

def get_rounded_strDatetime(str_datetime):
	datetime = from_strDatetime_to_datetime(str_datetime)
	year = datetime.year
	month = datetime.month
	day = datetime.day
	hour = datetime.hour
	minute = datetime.minute
	week_day = calendar.weekday(year, month, day)

	if minute <= 29: half_hour = 0
	else: half_hour = 30
	
	str_datetime2 = str(year) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2) + " " + str(hour).zfill(2) + ":" + str(half_hour).zfill(2) + ":00"
	return str_datetime2

def generate_hourly_bins_month(date):
	datetime_bin = {}
	month, year = date[0], date[1]
	
	cnt_bins = 0
	cal = calendar.Calendar()
	for p in cal.itermonthdays2(year, month):
		day = p[0]
		#ignore days of previous month
		if day == 0: continue
		
		for hour in range(24):
			str_datetime = str(year) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2) + " " + str(hour).zfill(2) + ":00:00"
			datetime_bin[str_datetime] = cnt_bins
			cnt_bins += 1
	return datetime_bin	


"""
return dic with rounded_strDatetime to bin in month mapping
"""
def generate_bins_month(date):
	datetime_bin = {}
	month, year = date[0], date[1]
	
	cnt_bins = 0
	cal = calendar.Calendar()
	for p in cal.itermonthdays2(year, month):
		day = p[0]
		#ignore days of previous month
		if day == 0: continue
		
		for hour in range(24):
			for minute in ["00", "30"]:
				str_datetime = str(year) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2) + " " + str(hour).zfill(2) + ":" + str(minute).zfill(2) + ":00"
				datetime_bin[str_datetime] = cnt_bins
				cnt_bins += 1
	return datetime_bin	

def get_xticks_bins_month(date, datetime_bin):
	xticks, xticks_labels = [], []
	cal = calendar.Calendar()
	month, year = date[0], date[1]
	for p in cal.itermonthdays2(year, month):
		day = p[0]
		#ignore days of previous month
		if day == 0: continue
	
		str_datetime = str(year) + "-" + str(month).zfill(2) + "-" + str(day).zfill(2) + " " + "00:00:00"

		xticks.append(datetime_bin[str_datetime])
		xticks_labels.append(str(day).zfill(2) + "/" + str(month).zfill(2))
	return xticks, xticks_labels

