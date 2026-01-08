const snowButton = document.getElementById("snowButton");
const num1 = document.getElementById("num1");
const num2 = document.getElementById("num2");
const answer = document.getElementById("answer");
const advisoryContent = document.getElementById("advisoryContent");
//this code intends to fetch data from the web server.

snowButton.addEventListener("click", () => {
  const city = num1.value; //.value is a function that the user inputs as num1.
  const state = num2.value;

//  fetch(`/get_forecast?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`)
//     .then(response => response.json())
//     .then(data => {

//       // ----- Forecast -----
//       if (data.forecast) {
//         answer.textContent = data.forecast;
//       } else {
//         answer.textContent = "Unable to retrieve forecast.";
//       }

//       // ----- Advisories -----
//       if (data.advisory && data.advisory.length > 0) {
//         advisoryContent.textContent = data.advisory;
//       } else {
//         advisoryContent.textContent = "No active winter advisories.";
//       }
//     })
//     .catch(err => {
//       answer.textContent = "Request failed: " + err;
//       advisoryContent.textContent = "Unable to load advisories.";
//     });

if (!city || !state) {
    alert("Please enter both city and state");
    return;
  }

  // Redirect to results page WITH data
  window.location.href = `/results?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`;
});
