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

    #since the return type of function is a tuple, need to initialize two variables at once.
    snow_chance, snow_amount = get_snowfall_chance_amount_ensemble(lat, lon)

    # Return as a formatted string
    summary = f"❄️ Snow chance: {snow_chance:.1f}% | 🌨️ Snow amount: {snow_amount:.2f} inches | 🌡️ Avg Temp: {avg_temp:.1f}°C"
    return summary

#more accurate for snowfall prediction as it accounts for snowfall amounts by ensemble member
#utilizes api from gfs seamless ensembles
def get_snowfall_chance_amount_ensemble(lat, lon):
    GFS_url = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=gfs_seamless&forecast_days=7&timezone=America/New_York"
    
    r = requests.get(GFS_url, timeout=10) #possible url change needed if time passes. Otherwise, it looks good
    r.raise_for_status()
    GFS_MODEL_data = r.json() 
    #i believe this converts the json into a dictionary, not string

    nextHourSnowCount = 0
    nextHourSnowAmount = 0

    #since there are 30 members given in the currently used data, just loop 30 times.
    for i in range(1, 31):
        currentMember = f"snowfall_member{i:02d}"
        #for now, the loop only predicts for the next hour. If we want more hours like 24, then I can modify the logic to do so.
        if (GFS_MODEL_data["hourly"][currentMember][0] != 0):
            nextHourSnowCount+=1
            nextHourSnowAmount+=GFS_MODEL_data["hourly"][currentMember][0]
    
    #get the average percent of snowing chance
    snowPercent = (nextHourSnowCount/30)*100

    finalSnowAmount = 0
    if (nextHourSnowCount != 0): #this statement is required to prevent division by 0 error.
        finalSnowAmount = nextHourSnowAmount/nextHourSnowCount
    
    return (snowPercent, finalSnowAmount)
#     GEM_url = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=gem_global&forecast_days=7&timezone=America%2FYellowknife"
#     ICON_MODEL_data = "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=" +  str(lat) + "&longitude="  + str(lon) + "&hourly=snowfall&models=icon_seamless&forecast_days=7&timezone=America%2FYellowknife"
#    #precipAndMake =