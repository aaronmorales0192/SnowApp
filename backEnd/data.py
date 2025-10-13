#Data sources
DC_Data_URL = "https://api.open-meteo.com/v1/forecast?latitude=38.8951&longitude=-77.0364&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=2&timezone=America%2FNew_York"

NewYork_Data_URL = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=2&timezone=America%2FNew_York"

Yellowknife_Data = "https://api.open-meteo.com/v1/forecast?latitude=62.45397&longitude=-114.37179&hourly=temperature_2m,precipitation,precipitation_type&forecast_days=4&timezone=America%2FYellowknife"

DC_lat = 38.8951
DC_lon = -77.0364
NewYork_lat = 40.712
NewYork_lon = -74.0060
Yellowknife_lat = 62.45397
Yellowknife_lon = -114.37179


import requests
#gets data based on city and state
def get_coordinates(city, state):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{city}, {state}, USA",
        "format": "json",
        "limit": 1
    }

    r = requests.get(url, params=params, headers={"User-Agent": "geoApp"})
    r.raise_for_status()
    data = r.json()

    if data:
        lat = data[0]["lat"]
        lon = data[0]["lon"]
        return float(lat), float(lon)
    else:
        return None, None

lat, lon = get_coordinates("Washington", "DC")
print(lat, lon)

#TODO: precip type in array is null so I iwll need to calculate it manually
#print(get_forecast_summary(Yellowknife_Data))
