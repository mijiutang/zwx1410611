const textInput = document.getElementById("textInput");
const toggleBtn = document.getElementById("toggleBtn");
const annotationArea = document.getElementById("annotationArea");
const renderArea = document.getElementById("renderArea");
const importBtn = document.getElementById("importBtn");
const importJSON = document.getElementById("importJSON");
const importMsg = document.getElementById("importMsg");
const saveBtn = document.getElementById("saveBtn");

const regexPanel = document.getElementById("regexPanel");
const regexInput = document.getElementById("regexInput");
const regexFindBtn = document.getElementById("regexFindBtn");
const regexMatchInfo = document.getElementById("regexMatchInfo");
const regexActionSelect = document.getElementById("regexActionSelect");
const regexApplyBtn = document.getElementById("regexApplyBtn");

let data = [];
let editMode = true;
let highlightedIndices = [];

// 页面加载恢复
window.addEventListener("load", () => {
  const saved = localStorage.getItem("chatData");
  if (saved) {
    data = JSON.parse(saved);
    textInput.value = data.map(d => d.text).join("\n");
    renderChat(data);
  }
});

// 渲染标注区
function renderAnnotationUI(lines) {
  annotationArea.innerHTML = "";
  data = [];

  lines.forEach((line, index) => {
    data.push({ type: "system", text: line }); // 默认非对话
    const div = document.createElement("div");
    div.innerHTML = `
      <span>${index + 1}</span>
      <select data-index="${index}">
        <option value="system" selected>非对话</option>
        <option value="me">右气泡</option>
        <option value="other">左气泡</option>
      </select>
      <label>${line}</label>
    `;
    const select = div.querySelector("select");
    select.addEventListener("change", () => {
      data[index].type = select.value;
      renderChat(data);
    });
    annotationArea.appendChild(div);
  });

  annotationArea.style.display = "block";
  regexPanel.style.display = "flex";
  textInput.style.display = "none";
  renderChat(data);
}

// 渲染聊天区
function renderChat(data) {
  renderArea.innerHTML = "";
  data.forEach(item => {
    if (item.type === "system") {
      const div = document.createElement("div");
      div.className = "system-message";
      div.textContent = item.text;
      renderArea.appendChild(div);
    } else {
      const div = document.createElement("div");
      div.className = `chat-row ${item.type === "me" ? "right" : "left"}`;
      div.innerHTML = `<div class="message">${item.text}</div>`;
      renderArea.appendChild(div);
    }
  });
  renderArea.scrollTop = renderArea.scrollHeight;
}

// 切换模式
toggleBtn.addEventListener("click", () => {
  if (editMode) {
    const text = textInput.value.trim();
    if (!text) { alert("文本为空！"); return; }
    const lines = text.split(/\r?\n/).filter(l => l.trim());
    renderAnnotationUI(lines);
    toggleBtn.textContent = "编辑文本区";
    editMode = false;
  } else {
    textInput.style.display = "block";
    annotationArea.style.display = "none";
    regexPanel.style.display = "none";
    textInput.value = data.map(d => d.text).join("\n");
    toggleBtn.textContent = "生成标注区";
    editMode = true;
  }
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
      textInput.value = data.map(d => d.text).join("\n");
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

// 保存 JSON
saveBtn.addEventListener("click", () => {
  localStorage.setItem("chatData", JSON.stringify(data));
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "data.json";
  a.click();
});

// 正则检索
regexFindBtn.addEventListener("click", () => {
  const pattern = regexInput.value.trim();
  highlightedIndices = [];
  if (!pattern) { regexMatchInfo.textContent = "请输入正则"; clearHighlights(); return; }
  let reg;
  try { reg = new RegExp(pattern); } catch(e) { regexMatchInfo.textContent = "正则格式错误"; return; }
  annotationArea.querySelectorAll("div").forEach((div, idx) => {
    const label = div.querySelector("label");
    if (reg.test(label.textContent.trim())) {
      div.style.backgroundColor = "#ffcccc";
      highlightedIndices.push(idx);
    } else {
      div.style.backgroundColor = "";
    }
  });
  regexMatchInfo.textContent = `找到 ${highlightedIndices.length} 个`;
});

regexApplyBtn.addEventListener("click", () => {
  const type = regexActionSelect.value;
  highlightedIndices.forEach(idx => {
    data[idx].type = type;
    const select = annotationArea.children[idx].querySelector("select");
    if (select) select.value = type;
  });
  renderChat(data);
});

function clearHighlights() {
  annotationArea.querySelectorAll("div").forEach(div => div.style.backgroundColor = "");
}
