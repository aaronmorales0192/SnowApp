import data
import snowLogic
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

#print(snowLogic.__file__)
print("enter a city:")
city = input()
print("enter a state:")
state = input()
lat, lon = data.get_coordinates(city, state)
print(snowLogic.get_forecast_summary(lat, lon))

