const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const log = document.getElementById("chat-log");

const exampleButtons = document.querySelectorAll(".chip");

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function scrollToBottom() {
  log.scrollTo({ top: log.scrollHeight, behavior: "smooth" });
}

function renderExchange(userText, data) {
  const exchange = document.createElement("div");
  exchange.className = "exchange";

  const biasNote = data.bias_note ? `
    <div class="response-note">Why it's biased: ${escapeHtml(data.bias_note)}</div>
  ` : "";

  exchange.innerHTML = `
    <div class="user-line">
      <span class="user-label">You</span>
      <p>${escapeHtml(userText)}</p>
    </div>
    <div class="response-grid">
      <div class="response-card biased">
        <div class="response-title">Biased response (for demonstration)</div>
        <p>${escapeHtml(data.biased)}</p>
        ${biasNote}
      </div>
      <div class="response-card fair">
        <div class="response-title">Fair response</div>
        <p>${escapeHtml(data.fair)}</p>
      </div>
    </div>
  `;

  log.appendChild(exchange);
  scrollToBottom();
}

function showTyping() {
  const typing = document.createElement("div");
  typing.className = "typing";
  typing.textContent = "Preparing contrasting responses...";
  log.appendChild(typing);
  scrollToBottom();
  return typing;
}

async function sendMessage(message) {
  const trimmed = message.trim();
  if (!trimmed) return;

  const typing = showTyping();

  try {
    const response = await fetch("/api/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed }),
    });

    const data = await response.json();
    typing.remove();

    if (!response.ok) {
      renderExchange(trimmed, {
        biased: "",
        fair: data.error || "Something went wrong.",
        bias_note: "",
      });
      return;
    }

    renderExchange(trimmed, data);
  } catch (error) {
    typing.remove();
    renderExchange(trimmed, {
      biased: "",
      fair: "Network error. Please try again.",
      bias_note: "",
    });
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value;
  input.value = "";
  sendMessage(message);
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const example = button.getAttribute("data-example");
    sendMessage(example);
  });
});
