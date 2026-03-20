// Smooth scroll from the home page "Explore Schemes" button to the quick access section.
const exploreBtn = document.getElementById("exploreBtn");
if (exploreBtn) {
  exploreBtn.addEventListener("click", function () {
    const quickSection = document.getElementById("quickSection");
    if (quickSection) {
      quickSection.scrollIntoView({ behavior: "smooth" });
    }
  });
}

// Chatbot small helper: adds a user/bot message to the chat box.
function _appendChatMessage(kind, text) {
  const chatBox = document.getElementById("chatBox");
  if (!chatBox) return;

  const message = document.createElement("div");
  message.className = kind === "user" ? "user-msg" : "bot-msg";
  message.innerHTML = `
    ${text}
    <div class="time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
  `;

  chatBox.appendChild(message);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Basic send message handler used by chatbot.html
function sendMessage() {
  const input = document.getElementById("userInput");
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  _appendChatMessage("user", text);
  input.value = "";

  // Simple placeholder response.
  setTimeout(() => {
    const response = "Sorry, I can only provide a demo response right now. Please check back later for full chatbot functionality.";
    _appendChatMessage("bot", response);
  }, 500);
}

// Allow pressing Enter in the chatbot input to send the message.
const userInput = document.getElementById("userInput");
if (userInput) {
  userInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      sendMessage();
    }
  });
}