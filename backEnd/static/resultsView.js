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
      const lines = data.forecast.trim().split("\n");
      forecastContent.innerHTML = "";

      lines.forEach(line => {
        // Example line:
        // Date: 2026-01-10 16:00 | Snow chance: 0.0% | Snow amount: 0.00cm | Temperature: 9.2°C

        const timeMatch = line.match(/(\d{2}:\d{2})/);
        const snowChanceMatch = line.match(/Snow chance:\s*([\d.]+%)/);
        const snowAmountMatch = line.match(/Snow amount:\s*([\d.]+cm)/);
        const tempMatch = line.match(/Temperature:\s*([\d.]+°C)/);

        const time = timeMatch ? timeMatch[1] : "--";
        const snowChance = snowChanceMatch ? snowChanceMatch[1] : "--";
        const snowAmount = snowAmountMatch ? snowAmountMatch[1] : "--";
        const temp = tempMatch ? tempMatch[1] : "--";

        const card = document.createElement("div");
        card.className = "hourCard";

        card.innerHTML = `
            <div class="hourTime">${time}</div>
            <div class="hourSnow">
                ❄️ ${snowChance}<br>
                🌨️ ${snowAmount}
            </div>
            <div class="hourTemp">🌡️ ${temp}</div>
        `;

        forecastContent.appendChild(card);
      });
    }
    else {
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
