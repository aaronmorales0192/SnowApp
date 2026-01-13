#run "pip install requests" in terminal to allow for requests be used. 
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

def get_forecast_summary(lat, lon):
    #"""Fetch forecast data and return a readable string summary."""
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&forecast_days=5&timezone=America%2FNew_York"

    GFS_url = f"https://ensemble-api.open-meteo.com/v1/ensemble?latitude={lat}&longitude={lon}&hourly=snowfall&models=gfs_seamless&forecast_days=5&timezone=America/New_York"
    with ThreadPoolExecutor(max_workers=2) as executor:
        forecast_future = executor.submit(fetch, url)
        gfs_future = executor.submit(fetch, GFS_url)

        data = forecast_future.result()
        GFS_MODEL_data = gfs_future.result()

    temps = data["hourly"]["temperature_2m"]
    times = data["hourly"]["time"] #Need to get the times array to call time later.
    current_time = datetime.now() #gives us the current local time of the user.
    current_hour = current_time.hour 

    summary_24hrs = []
    for i in range(1, 25):
         #this part takes care of the edge case: in case the API decreases time to 24 hours, this will prevent from getting index error.
        next_range_hour = min(current_hour + i, len(temps) - 1)
        next_hour_temp = temps[next_range_hour]

        #this fromisoformat function changes the string into a datetime object. 
        #Needed to change the string to datetime object so we could change the format of date string. 
        forecast_time = datetime.fromisoformat(times[next_range_hour])

        #since the return type of function is a tuple, need to initialize two variables at once.
        snow_chance, snow_amount = get_snowfall_chance_amount_ensemble(next_range_hour, GFS_MODEL_data["hourly"])

        #This .strftime() function allows us to change the format of the datetime object and write it to a string. 
        summary = f"⏱️ Date: {forecast_time.strftime('%Y-%m-%d %H:%M')} | ❄️ Snow chance: {snow_chance:.1f}% | 🌨️ Snow amount: {snow_amount:.2f}cm | 🌡️ Temperature: {next_hour_temp:.1f}°C"
        summary_24hrs.append(summary)
    
    # Return as a joined formatted string
    return "\n".join(summary_24hrs);

#more accurate for snowfall prediction as it accounts for snowfall amounts by ensemble member
#utilizes api from gfs seamless ensembles
def get_snowfall_chance_amount_ensemble(next_hour, data):
    nextHourSnowCount = 0
    nextHourSnowAmount = 0

    #since there are 30 members given in the currently used data, just loop 30 times.
    for i in range(1, 31):
        currentMember = f"snowfall_member{i:02d}"
        current_data = data[currentMember][next_hour]
        #for now, the loop only predicts for the next hour. If we want more hours like 24, then I can modify the logic to do so.
        if (current_data != 0):
            nextHourSnowCount+=1
            nextHourSnowAmount+=current_data
    
    #get the average percent of snowing chance
    snowPercent = (nextHourSnowCount/30)*100

    finalSnowAmount = 0
    if (nextHourSnowCount != 0): #this statement is required to prevent division by 0 error.
        finalSnowAmount = nextHourSnowAmount/nextHourSnowCount
    
    return (snowPercent, finalSnowAmount)
#     GEM_url = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=gem_global&forecast_days=7&timezone=America%2FYellowknife"
#     ICON_MODEL_data = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=icon_seamless&forecast_days=7&timezone=America%2FYellowknife"
#    #precipAndMake =

def fetch(url):
    return requests.get(url, timeout=10).json()

def get_nws_alerts(lat, lon):
    url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
    r = requests.get(url)
    r.raise_for_status()
    alerts_json = r.json()  # JSON with alert features
    results = ""

    for alert in alerts_json.get("features", []):
        props = alert.get("properties", {})

        event = props.get("event", "Unknown Alert")
        ends = props.get("ends") or props.get("expires")
        #only looking for winter related weather alerts
        if event == "Winter Weather Advisory" or event == "Winter Storm Warning" or event == "Winter Storm Watch" or event == "Blizzard Warning" or event == "Ice Storm Warning":
            # Convert to readable datetime
            if ends:
                ends_dt = datetime.fromisoformat(ends)
                ends_str = ends_dt.strftime("%Y-%m-%d %I:%M %p")
            else:
                ends_str = "Unknown"
            results += "Alert: " + event + " Valid Until " + ends_str
            
    return results
def schoolPredictionForDay(lat, lon, days=5, user_agent="school-predict/1.0"):
    order = ["very unlikely", "unlikely", "likely", "almost guaranteed"]
    def bumpCat(cat):
        if cat not in order:
            return cat
        if cat != "almost guaranteed":
            index = order.index(cat)
            return order[index + 1]
        return cat
    def decCat(cat):
        if cat not in order:
            return cat
        if cat != "very unlikely":
            index = order.index(cat)
            return order[index - 1]
        return cat

    # keywords 
    severe_warning_keywords = ["Blizzard Warning", "Winter Storm Warning", "Ice Storm Warning", "Blizzard", "Winter Storm"]
    advisory_keywords = ["Winter Weather Advisory", "Advisory", "Winter Storm Watch", "Winter Weather"]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&forecast_days={days}&timezone=America%2FNew_York"
    GFS_url = f"https://ensemble-api.open-meteo.com/v1/ensemble?latitude={lat}&longitude={lon}&hourly=snowfall&models=gfs_seamless&forecast_days={days}&timezone=America%2FNew_York"

    # fetch both in parallel using fetch()
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(fetch, url)
            f2 = executor.submit(fetch, GFS_url)
            data = f1.result()
            GFS_MODEL_data = f2.result()
    except Exception:
        # if fetch fails, return all very unlikely for both cancel and delay
        return {
            "cancel": {f"day{i}": "very unlikely" for i in range(1, days+1)},
            "delay":  {f"day{i}": "very unlikely" for i in range(1, days+1)}
        }

    # get NWS alerts string
    nws_alerts_str = get_nws_alerts(lat, lon)

    severe_alert_present = any(k.lower() in nws_alerts_str.lower() for k in severe_warning_keywords)
    advisory_alert_present = any(k.lower() in nws_alerts_str.lower() for k in advisory_keywords)

    # extract hourly arrays
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])

    gfs_hourly = GFS_MODEL_data.get("hourly", {}) if isinstance(GFS_MODEL_data, dict) else {}

    # parse times into datetimes and find start index closest to now
    now = datetime.now()
    time_datetimes = []
    for t in times:
        try:
            dt = datetime.fromisoformat(t)
        except Exception:
            try:
                dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            except Exception:
                continue
        time_datetimes.append(dt)

    start_idx = 0
    for idx, dt in enumerate(time_datetimes):
        # choose first hour that is >= now
        if dt >= now:
            start_idx = idx
            break

    # for each day compute aggregates using the ensemble helper per-hour
    cancel_out = {}
    delay_out = {}
    hours_per_day = 24
    for day in range(days):
        day_start = start_idx + day * hours_per_day
        day_end = day_start + hours_per_day  # exclusive
        expected_total_cm = 0.0
        max_hourly_expected = 0.0
        max_hourly_chance = 0.0
        temps_for_mean = []

        for hr_idx in range(day_start, day_end):
            if hr_idx >= len(times):
                break
            # temperature
            if hr_idx < len(temps):
                temps_for_mean.append(temps[hr_idx])
            # use ensemble function to get percent & amount for this hour
            try:
                snow_chance, snow_amount = get_snowfall_chance_amount_ensemble(hr_idx, gfs_hourly)
            except Exception:
                snow_chance, snow_amount = (0.0, 0.0)


            expected_total_cm += (snow_amount or 0.0)
            if (snow_amount or 0.0) > max_hourly_expected:
                max_hourly_expected = snow_amount or 0.0
            if (snow_chance or 0.0) > max_hourly_chance:
                max_hourly_chance = snow_chance or 0.0

        mean_temp_c = None
        if temps_for_mean:
            mean_temp_c = sum(temps_for_mean) / len(temps_for_mean)

        # cancel category)
        if severe_alert_present:
            cancel_cat = "almost guaranteed"
        elif expected_total_cm >= 12.0:
            cancel_cat = "almost guaranteed"
        elif expected_total_cm >= 5.0:
            cancel_cat = "likely"
        elif expected_total_cm >= 1.0:
            cancel_cat = "unlikely"
        else:
            cancel_cat = "very unlikely"

        # delay category 
        if severe_alert_present:
            delay_cat = "almost guaranteed"
        elif expected_total_cm >= 6.0:
            delay_cat = "almost guaranteed"
        elif expected_total_cm >= 3.0:
            delay_cat = "likely"
        elif expected_total_cm >= 0.5:
            delay_cat = "unlikely"
        else:
            delay_cat = "very unlikely"

        # bump/downgrade rules 
        if max_hourly_chance >= 80.0 and max_hourly_expected >= 5.0:
            cancel_cat = bumpCat(cancel_cat)
            delay_cat = bumpCat(delay_cat)
        elif max_hourly_chance >= 60.0 and max_hourly_expected >= 3.0:
            cancel_cat = bumpCat(cancel_cat)

        if advisory_alert_present and cancel_cat != "almost guaranteed":
            delay_cat = bumpCat(delay_cat)

        if mean_temp_c is not None and mean_temp_c > 2.0:
            if not severe_alert_present:
                cancel_cat = decCat(cancel_cat)
                delay_cat = decCat(delay_cat)

        if max_hourly_chance >= 90.0 and expected_total_cm < 0.5:
            delay_cat = bumpCat(delay_cat)

        cancel_out[f"day{day+1}"] = cancel_cat
        delay_out[f"day{day+1}"] = delay_cat

    return {"cancel": cancel_out, "delay": delay_out}
