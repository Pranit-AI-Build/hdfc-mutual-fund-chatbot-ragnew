// Use environment-specific API URL
const API_URL = window.location.hostname === 'localhost' 
  ? "http://localhost:8000/chat"
  : "https://hdfc-mutual-fund-chatbot-backend.onrender.com/chat";

const starterQuestions = [
  "What is the current NAV of HDFC Small Cap Fund Direct Growth?",
  "Can you tell me the exit load for HDFC Small Cap Fund Direct Growth?",
  "What is the minimum SIP amount for HDFC Banking & Financial Services Fund Direct Growth?",
];

function createMessageRow(message, role, source) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  if (role === "bot" && source) {
    const title = document.createElement("div");
    title.className = "bot-title";
    title.textContent = source;
    bubble.appendChild(title);
  }

  const text = document.createElement("div");
  text.textContent = message;
  bubble.appendChild(text);

  row.appendChild(bubble);
  return row;
}

function renderApp() {
  const root = document.getElementById("root");
  const shell = document.createElement("div");
  shell.className = "app-shell";

  const card = document.createElement("div");
  card.className = "chat-card";

  // Header
  const header = document.createElement("div");
  header.className = "chat-header";

  const brand = document.createElement("div");
  brand.className = "brand";
  const logo = document.createElement("div");
  logo.className = "brand-logo";
  logo.textContent = "H";
  const brandText = document.createElement("div");
  brandText.className = "brand-text";
  const brandTitle = document.createElement("div");
  brandTitle.className = "brand-title";
  brandTitle.textContent = "HDFC CHATBOT";
  const brandSubtitle = document.createElement("div");
  brandSubtitle.className = "brand-subtitle";
  brandSubtitle.textContent = "RAG ENGINE V2.0";
  brandText.appendChild(brandTitle);
  brandText.appendChild(brandSubtitle);
  brand.appendChild(logo);
  brand.appendChild(brandText);

  const headerActions = document.createElement("div");
  headerActions.className = "header-actions";
  const statusPill = document.createElement("div");
  statusPill.className = "pill";
  statusPill.textContent = "Safe, data-backed answers only";
  headerActions.appendChild(statusPill);

  header.appendChild(brand);
  header.appendChild(headerActions);

  // Main
  const main = document.createElement("div");
  main.className = "chat-main";

  const hero = document.createElement("div");
  hero.className = "chat-hero";
  const title = document.createElement("div");
  title.className = "chat-title";
  title.textContent = "How can I help you today?";
  const subtitle = document.createElement("div");
  subtitle.className = "chat-subtitle";
  subtitle.textContent =
    "I'm your HDFC Mutual Fund assistant. Ask me anything about our funds, NAVs, or exit loads.";
  hero.appendChild(title);
  hero.appendChild(subtitle);

  const chipsRow = document.createElement("div");
  chipsRow.className = "chips-row";
  starterQuestions.forEach((q) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    const icon = document.createElement("div");
    icon.className = "chip-icon";
    icon.textContent = "⟲";
    const label = document.createElement("span");
    label.textContent = q;
    chip.appendChild(icon);
    chip.appendChild(label);
    chip.addEventListener("click", () => {
      input.value = q;
      input.focus();
    });
    chipsRow.appendChild(chip);
  });

  const chatWindow = document.createElement("div");
  chatWindow.className = "chat-window";
  const messages = document.createElement("div");
  messages.className = "messages";

  const inputRow = document.createElement("div");
  inputRow.className = "chat-input-row";

  const inputShell = document.createElement("div");
  inputShell.className = "input-shell";
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = "Ask about funds...";
  inputShell.appendChild(input);

  const sendButton = document.createElement("button");
  sendButton.type = "button";
  sendButton.className = "send-button";
  sendButton.textContent = "➤";

  inputRow.appendChild(inputShell);
  inputRow.appendChild(sendButton);

  const footerNote = document.createElement("div");
  footerNote.className = "footer-note";
  footerNote.textContent =
    "AI can make mistakes. Information is based only on approved public fund data and is not investment advice.";

  chatWindow.appendChild(messages);
  chatWindow.appendChild(inputRow);
  chatWindow.appendChild(footerNote);

  main.appendChild(hero);
  main.appendChild(chipsRow);
  main.appendChild(chatWindow);

  card.appendChild(header);
  card.appendChild(main);
  shell.appendChild(card);
  root.appendChild(shell);

  // Chat behaviour
  let isSending = false;

  async function sendMessage() {
    if (isSending) return;
    const text = input.value.trim();
    if (!text) return;
    isSending = true;

    messages.appendChild(createMessageRow(text, "user"));
    messages.scrollTop = messages.scrollHeight;
    input.value = "";

    const thinkingRow = createMessageRow("Thinking...", "bot", "Assistant");
    messages.appendChild(thinkingRow);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      messages.removeChild(thinkingRow);
      const label = data.fund_name || "Assistant";
      messages.appendChild(createMessageRow(data.answer, "bot", label));
      messages.scrollTop = messages.scrollHeight;
    } catch (e) {
      messages.removeChild(thinkingRow);
      messages.appendChild(
        createMessageRow(
          "Sorry, something went wrong while contacting the server.",
          "bot",
          "Assistant",
        ),
      );
      messages.scrollTop = messages.scrollHeight;
    } finally {
      isSending = false;
    }
  }

  sendButton.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });
}

document.addEventListener("DOMContentLoaded", renderApp);

