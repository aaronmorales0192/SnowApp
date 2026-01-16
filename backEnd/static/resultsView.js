const forecastContent = document.getElementById("forecast");
const advisoryContent = document.getElementById("advisoryContent");

// Read query parameters from URL
const params = new URLSearchParams(window.location.search);
const city = params.get("city");
const state = params.get("state");

if (!city || !state) {
  alert('City and state are required!');
  window.location.href = '/';
}

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
        const tempMatch = line.match(/Temperature:\s*(-?[\d.]+°F)/);

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


fetchSchoolPredictions();

async function fetchSchoolPredictions() {
  try {
    const response = await fetch(`/get_school_prediction?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`);
    if (!response.ok) {
      throw new Error('Failed to fetch school predictions');
    }
    const predictionData = await response.json();
    displaySchoolPredictions(predictionData);
  } catch (error) {
    console.error('Error fetching school predictions:', error);
    // Only show error if the prediction container exists
    const predictionContainer = document.getElementById('schoolPredictionContent');
    if (predictionContainer) {
      predictionContainer.innerHTML =
        '<div class="error-prediction">Unable to load school predictions. Please try again later.</div>';
    }
  }
}

function displaySchoolPredictions(predictionData) {
  const container = document.getElementById('schoolPredictionContent');

  if (!container) {
    console.log('School prediction container not found');
    return;
  }

  if (!predictionData || !predictionData.cancel || !predictionData.delay) {
    container.innerHTML = '<div class="error-prediction">No prediction data available.</div>';
    return;
  }

  const days = ['Today', 'Tomorrow', 'Day 3', 'Day 4', 'Day 5'];

  let html = '';

  for (let i = 1; i <= 5; i++) {
    const cancelPrediction = predictionData.cancel[`day${i}`] || 'unknown';
    const delayPrediction = predictionData.delay[`day${i}`] || 'unknown';

    // Get date for this day
    const date = new Date();
    date.setDate(date.getDate() + i - 1);
    const dateString = date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });

    html += `
            <div class="day-card glass-card">
                <div class="day-header">
                    <h3>${days[i - 1]}</h3>
                    <div class="day-date">${dateString}</div>
                </div>
                <div class="prediction-items">
                    <div class="prediction-item">
                        <div class="prediction-label">Cancellation Chance</div>
                        <div class="prediction-value" data-category="${cancelPrediction}">
                            ${cancelPrediction}
                        </div>
                    </div>
                    <div class="prediction-item">
                        <div class="prediction-label">Delay Chance</div>
                        <div class="prediction-value" data-category="${delayPrediction}">
                            ${delayPrediction}
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  container.innerHTML = html;
}
