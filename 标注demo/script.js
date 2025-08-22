const textInput = document.getElementById("textInput");
const confirmText = document.getElementById("confirmText");
const editText = document.getElementById("editText");
const annotationArea = document.getElementById("annotationArea");
const importBtn = document.getElementById("importBtn");
const importJSON = document.getElementById("importJSON");
const importMsg = document.getElementById("importMsg");
const renderArea = document.getElementById("renderArea");
const saveBtn = document.getElementById("saveBtn");

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

// 确认文本 → 切换到标注模式
confirmText.addEventListener("click", () => {
  const text = textInput.value.trim();
  if (!text) { alert("文本为空！"); return; }

  const lines = text.split(/\r?\n/).filter(l => l.trim());
  renderAnnotationUI(lines, false);

  textInput.style.display = "none";
  confirmText.style.display = "none";
  editText.style.display = "inline-block";
  annotationArea.style.display = "grid";
});

// 编辑文本 → 切换回编辑模式
editText.addEventListener("click", () => {
  textInput.style.display = "block";
  confirmText.style.display = "inline-block";
  editText.style.display = "none";
  annotationArea.style.display = "none";

  textInput.value = data.map(item => item.text).join("\n");
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
      <span>${index + 1}</span>
      <select data-index="${index}">
        <option value="system" ${current.type === "system" ? "selected" : ""}>非对话</option>
        <option value="me" ${current.type === "me" ? "selected" : ""}>对话(我)</option>
        <option value="other" ${current.type === "other" ? "selected" : ""}>对话(别人)</option>
      </select>
      <label>${line}</label>
    `;

    const select = div.querySelector("select");
    const label = div.querySelector("label");

    // 下拉框改变类型
    select.addEventListener("change", () => {
      data[index].type = select.value;
      renderChat(data);
    });

    // 点击 label → 编辑
    label.addEventListener("click", () => {
      const textarea = document.createElement("textarea");
      textarea.value = label.textContent;
      textarea.style.flex = "1";
      div.replaceChild(textarea, label);
      textarea.focus();
      textarea.selectionStart = textarea.value.length;

      // 按 Enter 拆分
      textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const cursorPos = textarea.selectionStart;
          const textBefore = textarea.value.slice(0, cursorPos);
          const textAfter = textarea.value.slice(cursorPos);

          data[index].text = textBefore;

          if (index + 1 < annotationArea.children.length) {
            const nextDiv = annotationArea.children[index + 1];
            const nextLabel = nextDiv.querySelector("label");

            if (textAfter.trim()) {
              // 将光标后文本放到下一行前面
              data[index + 1].text = textAfter + nextLabel.textContent;
            }
          } else if (textAfter.trim()) {
            // 最后一行，光标后有文本 → 新建一行
            data.push({ type: "system", text: textAfter });
          }

          // 光标后没文本 → 当前行结束编辑
          renderAnnotationUI(data.map(d => d.text), true);

          // 焦点移动到下一行 textarea（如果存在）
          if (annotationArea.children[index + 1]) {
            const nextInput = annotationArea.children[index + 1].querySelector("textarea");
            if (nextInput) {
              nextInput.focus();
              nextInput.selectionStart = 0;
              nextInput.selectionEnd = 0;
            }
          }
        }
      });

      // 失焦事件
      textarea.addEventListener("blur", () => {
        data[index].text = textarea.value;
        renderAnnotationUI(data.map(d => d.text), true);
      });
    });

    annotationArea.appendChild(div);
  });

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

// 保存 JSON
saveBtn.addEventListener("click", () => {
  localStorage.setItem("chatData", JSON.stringify(data));
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "data.json";
  a.click();
});
