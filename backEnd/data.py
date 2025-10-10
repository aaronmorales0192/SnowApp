DC_Data_URL = "https://api.open-meteo.com/v1/forecast?latitude=38.8951&longitude=-77.0364&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=2&timezone=America%2FNew_York"

NewYork_Data_URL = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=2&timezone=America%2FNew_York"

Yellowknife_Data = "https://api.open-meteo.com/v1/forecast?latitude=62.45397&longitude=-114.37179&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=4&timezone=America%2FYellowknife"

#run "pip install requests" in terminal to allow for requests be used. 
import requests

def get_forecast_summary(url):
    """Fetch forecast data and return a readable string summary."""
   
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    temps = data["hourly"]["temperature_2m"]
    precip = data["hourly"]["precipitation"]
    types = data["hourly"]["precipitation_type"]

    # Compute simple stats
    avg_temp = sum(temps) / len(temps)
    snow_hours = sum(1 for t, p in zip(types, precip) if t == 2 and p > 0)
    total_hours = len(temps)
    snow_chance = (snow_hours / total_hours) * 100

    # Return as a formatted string
    summary = f"❄️ Snow chance: {snow_chance:.1f}% | 🌡️ Avg Temp: {avg_temp:.1f}°C"
    return summary


print(get_forecast_summary(Yellowknife_Data))
