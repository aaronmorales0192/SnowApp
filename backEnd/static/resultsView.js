const forecastContent = document.getElementById("forecast");
const advisoryContent = document.getElementById("advisoryContent");

// Read query parameters from URL
const params = new URLSearchParams(window.location.search);
const city = params.get("city");
const state = params.get("state");

fetch(`/get_forecast?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`)
  .then(response => response.json())
  .then(data => {
    // ----- Forecast -----
    if (data.forecast) {
      forecastContent.innerHTML = data.forecast.replaceAll("\n", "<br>");
    } else {
      forecastContent.textContent = "Unable to retrieve forecast.";
    }

    // ----- Advisories -----
    if (data.advisory && data.advisory.length > 0) {
      advisoryContent.innerHTML = data.advisory.replaceAll("\n", "<br>");
    } else {
      advisoryContent.textContent = "No active winter advisories.";
    }
  })
  .catch(err => {
    forecastContent.textContent = "Request failed: " + err;
    advisoryContent.textContent = "Unable to load advisories.";
    console.error(err);
  });
