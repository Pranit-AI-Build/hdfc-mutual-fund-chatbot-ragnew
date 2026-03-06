// Use environment-specific API URL
const API_URL = window.location.hostname === 'localhost' 
  ? "http://localhost:8000/chat"
  : "https://hdfc-mutual-fund-chatbot-backend.onrender.com/chat";

const suggestionQuestions = [
  {
    text: "What is the NAV of HDFC Banking & Financial Services Fund Direct Growth?",
    icon: "📊",
    color: "purple"
  },
  {
    text: "What is the exit load for HDFC Flexi Cap Direct Plan Growth?",
    icon: "⚖️",
    color: "blue"
  },
  {
    text: "What is the minimum amount for SIP in HDFC NIFTY Next 50 Index Fund Direct Growth?",
    icon: "💰",
    color: "pink"
  }
];

function createMessageRow(message, role, source) {
  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `message-avatar ${role}`;
  avatar.textContent = role === "user" ? "👤" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  
  if (role === "bot" && message) {
    // Parse markdown-like bold text
    let formattedMessage = message
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    
    // Check if message has bullet points
    if (message.includes('•') || message.includes('- ')) {
      formattedMessage = formattedMessage.replace(/•\s(.*?)(?=<br>|$)/g, '<li>$1</li>');
      if (formattedMessage.includes('<li>')) {
        formattedMessage = '<ul>' + formattedMessage + '</ul>';
      }
    }
    
    bubble.innerHTML = formattedMessage;
    
    // Add source citation if available
    if (source) {
      const citation = document.createElement("div");
      citation.className = "source-citation";
      citation.innerHTML = `<span class="source-icon">🔗</span> <a href="${source}" target="_blank" class="source-link">${source}</a>`;
      bubble.appendChild(citation);
    }
  } else {
    bubble.textContent = message;
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  return row;
}

function renderApp() {
  const root = document.getElementById("root");
  
  // Create app shell
  const shell = document.createElement("div");
  shell.className = "app-shell";

  // Header
  const header = document.createElement("header");
  header.className = "chat-header";
  
  const brand = document.createElement("div");
  brand.className = "brand";
  brand.innerHTML = `
    <div class="brand-logo">H</div>
    <div class="brand-text">
      <div class="brand-title">HDFC CHATBOT</div>
      <div class="brand-subtitle">RAG ENGINE V2.0</div>
    </div>
  `;
  
  header.appendChild(brand);

  // Main content
  const main = document.createElement("main");
  main.className = "chat-main";

  // Hero section
  const hero = document.createElement("div");
  hero.className = "chat-hero";
  hero.innerHTML = `
    <h1 class="chat-title">How can I help you today?</h1>
    <p class="chat-subtitle"><strong>I'm your HDFC Mutual Fund assistant.</strong></p>
    <p class="chat-disclaimer">Facts-only. No investment advice</p>
  `;

  // Suggestions
  const suggestionsRow = document.createElement("div");
  suggestionsRow.className = "suggestions-row";
  
  suggestionQuestions.forEach(q => {
    const card = document.createElement("div");
    card.className = "suggestion-card";
    card.innerHTML = `
      <div class="suggestion-icon ${q.color}">${q.icon}</div>
      <div class="suggestion-text">${q.text}</div>
    `;
    card.addEventListener("click", () => {
      input.value = q.text;
      input.focus();
    });
    suggestionsRow.appendChild(card);
  });

  // Chat container
  const chatContainer = document.createElement("div");
  chatContainer.className = "chat-container";

  const messages = document.createElement("div");
  messages.className = "messages";

  // Input area
  const inputContainer = document.createElement("div");
  inputContainer.className = "input-container";
  inputContainer.innerHTML = `
    <div class="input-wrapper">
      <input type="text" placeholder="Ask about funds..." />
      <div class="input-actions">
        <button class="send-btn">➤</button>
      </div>
    </div>
    <p class="footer-note">AI can make mistakes. Please verify important information.</p>
  `;

  const input = inputContainer.querySelector("input");
  const sendBtn = inputContainer.querySelector(".send-btn");

  chatContainer.appendChild(messages);
  chatContainer.appendChild(inputContainer);

  main.appendChild(hero);
  main.appendChild(suggestionsRow);
  main.appendChild(chatContainer);

  shell.appendChild(header);
  shell.appendChild(main);
  root.appendChild(shell);

  // Chat functionality
  let isSending = false;

  async function sendMessage() {
    if (isSending) return;
    const text = input.value.trim();
    if (!text) return;
    isSending = true;

    // Hide hero and suggestions after first message
    hero.style.display = "none";
    suggestionsRow.style.display = "none";

    messages.appendChild(createMessageRow(text, "user"));
    messages.scrollTop = messages.scrollHeight;
    input.value = "";

    const thinkingRow = createMessageRow("Thinking...", "bot");
    thinkingRow.querySelector(".message-bubble").classList.add("thinking");
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
      
      // Use source URL from data
      let source = data.source_url || "";
      let answer = data.answer;
      
      messages.appendChild(createMessageRow(answer, "bot", source));
      messages.scrollTop = messages.scrollHeight;
    } catch (e) {
      messages.removeChild(thinkingRow);
      messages.appendChild(
        createMessageRow(
          "Sorry, something went wrong while contacting the server.",
          "bot"
        ),
      );
      messages.scrollTop = messages.scrollHeight;
    } finally {
      isSending = false;
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendMessage();
    }
  });
}

document.addEventListener("DOMContentLoaded", renderApp);
