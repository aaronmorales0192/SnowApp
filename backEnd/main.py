# Import necessary modules
from flask import Flask, render_template, request, jsonify
import data        # Your module to get coordinates
import snowLogic   # Your module to get snow forecast

# Create the Flask app
# Flask automatically looks for templates in "templates/" folder
# and static files (CSS/JS) in "static/" folder
app = Flask(__name__)

# -----------------------------
# Route for the homepage
# When someone visits http://127.0.0.1:5000/
# Flask will run this function
# -----------------------------
@app.route("/")
def home():
    # Render the HTML file called "homepage.html"
    # This must be in templates/
    return render_template("homepage.html")

@app.route("/results")
def results():
   # Render the HTML file called "results.html"
   return render_template("resultsPage.html")





# -----------------------------
# Route for the About page
# When someone visits http://127.0.0.1:5000/about
# Flask will run this function
# -----------------------------
@app.route("/about")
def about():
    # Render the HTML file called "about.html"
    return render_template("about.html")

# -----------------------------
# Route to handle Snow Forecast requests
# This will be called by your JavaScript using POST
# -----------------------------
@app.route("/get_snow", methods=["POST"])
def get_snow():
    # Get city and state from JSON sent by JS
    city = request.json.get("city")
    state = request.json.get("state")
    
    # Use your existing modules to get coordinates
    lat, lon = data.get_coordinates(city, state)
    
    # Use your existing module to get the snow forecast
    forecast = snowLogic.get_forecast_summary(lat, lon)
    
    # Return the forecast as JSON so JS can display it
    return jsonify({"forecast": forecast})

# -----------------------------
# Run the Flask server
# debug=True: automatically reloads the server when you save changes
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

