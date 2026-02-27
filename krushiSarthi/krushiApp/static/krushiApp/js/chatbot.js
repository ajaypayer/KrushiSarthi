function sendMessage() {
  const input = document.getElementById("userInput");
  const chatBox = document.getElementById("chatBox");

  if (input.value.trim() === "") return;

  // User message
  const userDiv = document.createElement("div");
  userDiv.className = "user-msg";
  userDiv.innerText = input.value;
  chatBox.appendChild(userDiv);

  // Bot reply (demo)
  const botDiv = document.createElement("div");
  botDiv.className = "bot-msg";
  botDiv.innerText = "Thank you! I will help you soon. (Demo AI)";
  chatBox.appendChild(botDiv);

  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;
}