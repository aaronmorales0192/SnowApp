const snowButton = document.getElementById("snowButton");
const num1 = document.getElementById("num1");
const num2 = document.getElementById("num2");
const answer = document.getElementById("answer");
//this code intends to fetch data from the web server.

snowButton.addEventListener("click", () => {
  const city = num1.value; //.value is a function that the user inputs as num1.
  const state = num2.value;

  fetch(`/get_forecast?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`) 
  //get_forecast is the destination of fetching data.
    .then(response => response.json()) 
    //response is an response type object provided by the browser. It contains metadata, so cannot be used yet. 
    //Have to convert the response to json object in order to access the data, and accesed data is stored into data.
    //so data is the converted json.
    .then (data => {
      //data is like dictionary. so like "forecast": "Snow tomorrow"
      //therefore we can use dot pointers to access them like key. the reason we are using .forecast is because
      //we used get call for forecast information object.
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

