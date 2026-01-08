const snowButton = document.getElementById("snowButton");
const num1 = document.getElementById("num1");
const num2 = document.getElementById("num2");
const answer = document.getElementById("answer");
const advisoryContent = document.getElementById("advisoryContent");
//this code intends to fetch data from the web server.

snowButton.addEventListener("click", () => {
  const city = num1.value; //.value is a function that the user inputs as num1.
  const state = num2.value;

if (!city || !state) {
    alert("Please enter both city and state");
    return;
  }

  // Redirect to results page WITH data
  window.location.href = `/results?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`;
});
