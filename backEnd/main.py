import data
import snowLogic
from flask import Flask

#print(snowLogic.__file__)
print("enter a city:")
city = input()
print("enter a state:")
state = input()
lat, lon = data.get_coordinates(city, state)
print(snowLogic.get_forecast_summary(lat, lon))

