#run "pip install requests" in terminal to allow for requests be used. 
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

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