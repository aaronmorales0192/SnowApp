const snowButton = document.getElementById("snowButton");
const num1 = document.getElementById("num1");
const num2 = document.getElementById("num2");
const answer = document.getElementById("answer");


snowButton.addEventListener("click", () => {
  answer.textContent = num1.value + " + " + num2.value + " = "  + (Number(num1.value) + Number(num2.value));
})
