const snowButton = document.getElementById("snowButton");
const num1 = document.getElementById("num1");
const num2 = document.getElementById("num2");
const answer = document.getElementById("answer");


snowButton.addEventListener("click", () => {
  const city = num1.value;
  const state = num2.value;

  fetch(`/get_forecast?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`) 
    .then(response => response.json()) 
    .then (data => {
      if(data.forecast) {
        answer.textContent = data.forecast;
      }
      else {
        answer.textContent = "Error: " + data.error;
      }
    })
  .catch(err=> {
    answer.textContent = "Fetch Data Request failed: " + err;
  })
})

