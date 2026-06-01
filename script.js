const chat = document.querySelector("#chat");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#userInput");
const sendBtn = document.querySelector("#sendBtn");
const clearBtn = document.querySelector("#clearBtn");

const messages = [];

function addMessage(role, content, sources = []) {
  const item = document.createElement("article");
  item.className = `message ${role}`;

  const text = document.createElement("div");
  text.className = "message-text";
  text.textContent = content;
  item.appendChild(text);

  if (sources.length > 0) {
    const sourceList = document.createElement("div");
    sourceList.className = "sources";
    const title = document.createElement("strong");
    title.textContent = "参考来源";
    sourceList.appendChild(title);

    sources.forEach((source) => {
      const sourceItem = document.createElement("p");
      sourceItem.textContent = `${source.source}：${source.text.slice(0, 120)}...`;
      sourceList.appendChild(sourceItem);
    });

    item.appendChild(sourceList);
  }

  chat.appendChild(item);
  chat.scrollTop = chat.scrollHeight;
}

async function sendMessage(userText) {
  messages.push({ role: "user", content: userText });
  addMessage("user", userText);
  sendBtn.disabled = true;
  sendBtn.textContent = "发送中";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    const data = await response.json();
    if (!response.ok) {
      const message = data.error?.message || data.error || "请求失败";
      throw new Error(message);
    }

    messages.push({ role: "assistant", content: data.answer });
    addMessage("assistant", data.answer, data.sources || []);
  } catch (error) {
    messages.pop();
    addMessage("assistant", `出错了：${error.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "发送";
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const userText = input.value.trim();
  if (!userText) return;
  input.value = "";
  sendMessage(userText);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

clearBtn.addEventListener("click", () => {
  messages.length = 0;
  chat.innerHTML = "";
  addMessage("assistant", "你好，我是 RAG 技术支持问答助手。你可以问我 API Key、401 报错、限流、Webhook 等问题。");
  input.focus();
});

addMessage("assistant", "你好，我是 RAG 技术支持问答助手。你可以问我 API Key、401 报错、限流、Webhook 等问题。");
