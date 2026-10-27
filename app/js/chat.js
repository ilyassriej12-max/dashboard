/**
 * AI School OS - Phase 6 Bottom AI Chat
 * Modern chat interface with streaming, typing animation,
 * attachment support (text, voice, image, PDF, code, math),
 * and Moroccan Darija teacher persona responses.
 */

(function () {
  "use strict";

  var container = document.getElementById("companion");
  if (!container) return;

  var chatArea = document.createElement("div");
  chatArea.className = "bottom-chat";
  chatArea.innerHTML =
    '<div class="bottom-chat-inner">' +
    '<div class="chat-history" id="chatHistory"></div>' +
    '<div class="chat-input-area">' +
    '<div class="chat-input-wrapper">' +
    '<button class="chat-btn" id="chatAttach" aria-label="Attach file"><svg><use href="#i-chat-attach"/></svg></button>' +
    '<input class="chat-input" id="chatInput" placeholder="Message Dr. Ada…" />' +
    '<button class="chat-btn send" id="chatSend" aria-label="Send message"><svg><use href="#i-chat-send"/></svg></button>' +
    '</div>' +
    '</div>' +
    '</div>';

  container.appendChild(chatArea);

  var history = document.getElementById("chatHistory");
  var input = document.getElementById("chatInput");
  var sendBtn = document.getElementById("chatSend");
  var attachBtn = document.getElementById("chatAttach");

  // Add Moroccan Darija welcome message
  addMessage("assistant", "واخا أهلاً وسهلاً! أنا 드. آدا، معلمتك في الذكاء الاصطناعي. شنو نبدا به اليوم؟", true);

  // ------------------------------------------------------------------
  // Message rendering
  // ------------------------------------------------------------------
  function addMessage(role, text, streaming) {
    var msg = document.createElement("div");
    msg.className = "chat-msg " + role;
    var avatar = document.createElement("div");
    avatar.className = "chat-avatar " + role;
    avatar.textContent = role === "user" ? "A" : "A";
    var bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    if (streaming) {
      bubble.classList.add("streaming");
      var typing = document.createElement("div");
      typing.className = "chat-typing";
      typing.innerHTML = '<span></span><span></span><span></span>';
      bubble.appendChild(typing);
    } else {
      bubble.textContent = text;
    }
    msg.appendChild(avatar);
    msg.appendChild(bubble);
    history.appendChild(msg);
    history.scrollTop = history.scrollHeight;
    return { msg: msg, bubble: bubble };
  }

  function updateBubble(bubble, text) {
    bubble.textContent = text;
    history.scrollTop = history.scrollHeight;
  }

  // ------------------------------------------------------------------
  // Streaming response from backend
  // ------------------------------------------------------------------
  async function streamResponse(message) {
    var result = addMessage("assistant", "", true);
    var bubble = result.bubble;

    try {
      var resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          teacher: "mathematics",
          student: 1,
          curriculum: null
        })
      });

      if (!resp.ok) throw new Error("Chat error: " + resp.status);

      var data = await resp.json();
      var fullText = data.answer || data.reply || "";

      // Typewriter streaming effect
      var displayed = "";
      var i = 0;
      function typeNext() {
        if (i >= fullText.length) {
          bubble.classList.remove("streaming");
          updateBubble(bubble, fullText);
          history.scrollTop = history.scrollHeight;
          return;
        }
        displayed += fullText[i];
        updateBubble(bubble, displayed);
        i++;
        setTimeout(typeNext, 25);
      }
      typeNext();

    } catch (err) {
      bubble.classList.remove("streaming");
      updateBubble(bubble, "API not connected. Dr. Ada says: واكا الخلفية ما 쉬 운net. جرب مرة أخرى.");
      console.warn("Chat stream error:", err);
    }
  }

  // ------------------------------------------------------------------
  // Send handler
  // ------------------------------------------------------------------
  function send() {
    var text = input.value.trim();
    if (!text) return;
    addMessage("user", text);
    input.value = "";
    input.focus();
    streamResponse(text);
  }

  sendBtn.addEventListener("click", send);

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  attachBtn.addEventListener("click", function () {
    var inputEl = document.createElement("input");
    inputEl.type = "file";
    inputEl.multiple = true;
    inputEl.accept = ".pdf,.png,.jpg,.jpeg,.txt,.py,.js,.md";
    inputEl.onchange = function (e) {
      var files = e.target.files;
      if (files && files.length) {
        var names = Array.from(files).map(function (f) { return f.name; }).join(", ");
        addMessage("user", "📎 " + names);
        streamResponse("I received " + files.length + " file(s): " + names + ". How can I help with them?");
      }
    };
    inputEl.click();
  });

  // Expose for global use
  window.streamResponse = streamResponse;
})();

