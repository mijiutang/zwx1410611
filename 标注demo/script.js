const textInput = document.getElementById("textInput");
const confirmText = document.getElementById("confirmText");
const importBtn = document.getElementById("importBtn");
const importJSON = document.getElementById("importJSON");
const importMsg = document.getElementById("importMsg");
const annotationArea = document.getElementById("annotationArea");
const renderArea = document.getElementById("renderArea");
const saveBtn = document.getElementById("saveBtn");
const clearBtn = document.getElementById("clearBtn");

let data = [];

// 页面加载时恢复 localStorage（可选）
window.addEventListener("load", () => {
  const saved = localStorage.getItem("chatData");
  if (saved) {
    data = JSON.parse(saved);
    renderAnnotationUI(data.map(item => item.text), true);
    renderChat(data);
  }
});

// 确认文本
confirmText.addEventListener("click", () => {
  const text = textInput.value.trim();
  if (!text) { alert("文本为空！"); return; }

  const lines = text.split(/\r?\n/).filter(l => l.trim());
  renderAnnotationUI(lines, false);
});

// 导入 JSON
importBtn.addEventListener("click", () => importJSON.click());
importJSON.addEventListener("change", (event) => {
  const file = event.target.files[0];
  importMsg.textContent = "";
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const importedData = JSON.parse(e.target.result);
      if (!Array.isArray(importedData)) throw new Error("JSON 格式错误");
      data = importedData;

      renderAnnotationUI(data.map(item => item.text), true);
      renderChat(data);
      importMsg.style.color = "green";
      importMsg.textContent = `导入成功: ${file.name}`;
    } catch (err) {
      importMsg.style.color = "red";
      importMsg.textContent = "导入失败: " + err.message;
    }
  };
  reader.readAsText(file, "utf-8");
});

// 渲染标注 UI
function renderAnnotationUI(lines, restore = false) {
  annotationArea.innerHTML = "";
  if (!restore) data = [];

  lines.forEach((line, index) => {
    if (!restore) data.push({ type: "system", text: line });
    const current = restore ? data[index] : { type: "system", text: line };

    const div = document.createElement("div");

    div.innerHTML = `
      <select data-index="${index}">
        <option value="system" ${current.type === "system" ? "selected" : ""}>非对话</option>
        <option value="me" ${current.speaker === "me" ? "selected" : ""}>对话(我)</option>
        <option value="other" ${current.speaker === "other" ? "selected" : ""}>对话(别人)</option>
      </select>
      <span>${index + 1}</span>
      <label>${line}</label>
    `;
    annotationArea.appendChild(div);
  });

  annotationArea.querySelectorAll("select").forEach(sel => {
    sel.addEventListener("change", (e) => {
      const i = e.target.dataset.index;
      const type = e.target.value;

      if (type === "system") {
        data[i] = { type: "system", text: data[i].text };
      } else {
        data[i] = { type: "dialogue", speaker: type, text: data[i].text };
      }

      renderChat(data);
      renderArea.scrollTop = renderArea.scrollHeight;
    });
  });

  renderChat(data);
  renderArea.scrollTop = renderArea.scrollHeight;
}

// 渲染聊天气泡
function renderChat(jsonData) {
  renderArea.innerHTML = "";

  jsonData.forEach(item => {
    if (!item) return;

    if (item.type === "system") {
      const div = document.createElement("div");
      div.className = "system-message";
      div.textContent = item.text;
      renderArea.appendChild(div);
    }

    if (item.type === "dialogue") {
      const row = document.createElement("div");
      row.className = `chat-row ${item.speaker === "me" ? "right" : "left"}`;

      const msg = document.createElement("div");
      msg.className = "message";
      msg.textContent = item.text;

      const placeholder = document.createElement("div");
      placeholder.className = "avatar-placeholder";

      if (item.speaker === "me") {
        row.appendChild(msg);
        row.appendChild(placeholder);
      } else {
        row.appendChild(placeholder);
        row.appendChild(msg);
      }

      renderArea.appendChild(row);
    }
  });
}

// 保存 JSON
saveBtn.addEventListener("click", () => {
  if (data.length === 0) { alert("没有数据可以保存！"); return; }

  const filename = "data.json";
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
  alert(`已生成 ${filename} 下载文件`);
});

// 清空数据
clearBtn.addEventListener("click", () => {
  data = [];
  annotationArea.innerHTML = "";
  renderArea.innerHTML = "";
  textInput.value = "";
  importMsg.textContent = "";
  alert("数据已清空！");
});
