#run "pip install requests" in terminal to allow for requests be used. 
import requests

def get_forecast_summary(lat, lon):
    #"""Fetch forecast data and return a readable string summary."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=" + str(lat) + "&longitude=" + str(lon) + "&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=2&timezone=America%2FNew_York"
    r = requests.get(url, timeout=10) #possible url change needed if time passes. Otherwise, it looks good
    r.raise_for_status()
    data = r.json() #i believe this converts the json into a dictionary, not string
    temps = data["hourly"]["temperature_2m"]
    precip = data["hourly"]["precipitation"]
    types = data["hourly"]["precipitation_type"] #null in data set for some reason
    

    # Compute simple stats
    avg_temp = sum(temps) / len(temps) 
    precipAndType = zip(types, precip)
    snow_hours = 0
    # zip pairs each precip type with corresponding precip amount
    for type, precip in precipAndType:
        if type == 2 and precip > 0:
            snow_2Hours+=1
    # note: precip type is null always in data so not working rn 
    total_hours = len(temps)
    snow_chance = (snow_hours / total_hours) * 100

    # Return as a formatted string
    summary = f"❄️ Snow chance: {snow_chance:.1f}% | 🌡️ Avg Temp: {avg_temp:.1f}°C"
    return summary

#more accurate for snowfall prediction as it accounts for snowfall amounts by ensemble member
#utilizes api from gfs seamless ensembles
#IN PROGRESS
def get_snowfall_amount_ensemble(lat, lon):
    url = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=65.28333&longitude=" + str(lat) + "&longitude=" + str(lon) + "&hourly=snowfall&models=gfs_seamless&forecast_days=7&timezone=America/New_York"
    r = requests.get(url, timeout=10) #possible url change needed if time passes. Otherwise, it looks good
    r.raise_for_status()
    data = r.json() 
    #i believe this converts the json into a dictionary, not string
   #precipAndMake =