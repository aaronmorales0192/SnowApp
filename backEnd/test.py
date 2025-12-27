#until flask server is complete everyone test on this file. 
import data
import snowLogic

#print(snowLogic.__file__)
print("enter a city:")
city = input()
print("enter a state:")
state = input()
lat, lon = data.get_coordinates(city, state)
print(snowLogic.get_forecast_summary(lat, lon))