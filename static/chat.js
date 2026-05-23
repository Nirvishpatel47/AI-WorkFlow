const token = localStorage.getItem("token");
if (!token) window.location.href = "/";

const chatForm = document.getElementById("chatForm");
const chatBox = document.getElementById("chatBox");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");

// ─── Toast System ─────────────────────────────────────────────────────────────
const toastContainer = document.getElementById("toastContainer");

function showToast(message, type = "info", duration = 3500) {
    const icons = {
        success: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        error: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        info: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
    };

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span>${escapeHtml(message)}</span>
        <button class="toast-dismiss" onclick="this.parentElement.remove()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => { toast.style.opacity = "0"; toast.style.transition = "opacity 0.3s"; setTimeout(() => toast.remove(), 300); }, duration);
}

// ─── HTML Safety ──────────────────────────────────────────────────────────────
function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ─── Markdown Parser ──────────────────────────────────────────────────────────
function parseMarkdown(raw) {
    let html = raw;

    // 1. TRACE blocks (custom tag)
    html = html.replace(/\[TRACE\]([\s\S]*?)\[\/TRACE\]/g, (_, content) => `
        <div class="rag-trace">
            <div class="trace-header">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                Vector Query Execution Trace
            </div>
            <div class="trace-node">${escapeHtml(content.trim())}</div>
        </div>`);

    // 2. Fenced code blocks  ```lang\n...\n```
    html = html.replace(/```([a-zA-Z0-9_+-]*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        const langLabel = lang.trim() || "code";
        const id = "cb-" + Math.random().toString(36).slice(2, 8);
        return `<div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-block-lang">${escapeHtml(langLabel)}</span>
                <button class="copy-btn" data-target="${id}" onclick="copyCode(this)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    Copy
                </button>
            </div>
            <pre><code id="${id}">${escapeHtml(code.trim())}</code></pre>
        </div>`;
    });

    // 3. Blockquotes
    html = html.replace(/^&gt;\s?(.+)$/gm, '<blockquote>$1</blockquote>');

    // 4. Headings
    html = html.replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^#{1}\s+(.+)$/gm, '<h1>$1</h1>');

    // 5. Horizontal rules
    html = html.replace(/^[-*_]{3,}$/gm, '<hr>');

    // 6. Bold & Italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.+?)_/g, '<em>$1</em>');

    // 7. Inline code (after code blocks so backticks don't conflict)
    html = html.replace(/`([^`\n]+)`/g, (_, code) => `<code>${escapeHtml(code)}</code>`);

    // 8. Unordered lists
    html = html.replace(/((?:^[ \t]*[-*+]\s+.+\n?)+)/gm, (block) => {
        const items = block.trim().split('\n').map(l => `<li>${l.replace(/^[ \t]*[-*+]\s+/, '')}</li>`).join('');
        return `<ul>${items}</ul>`;
    });

    // 9. Ordered lists
    html = html.replace(/((?:^[ \t]*\d+\.\s+.+\n?)+)/gm, (block) => {
        const items = block.trim().split('\n').map(l => `<li>${l.replace(/^[ \t]*\d+\.\s+/, '')}</li>`).join('');
        return `<ol>${items}</ol>`;
    });

    // 10. Paragraphs — wrap bare lines
    html = html.replace(/^(?!<[a-z]).+$/gm, (line) => {
        if (line.trim() === '') return '';
        return `<p>${line}</p>`;
    });

    // 11. Collapse multiple blank lines
    html = html.replace(/(\s*\n){3,}/g, '\n\n');

    return html;
}

// ─── Copy Code Handler ────────────────────────────────────────────────────────
window.copyCode = async (btn) => {
    const id = btn.getAttribute("data-target");
    const codeEl = document.getElementById(id);
    if (!codeEl) return;
    try {
        await navigator.clipboard.writeText(codeEl.innerText);
        btn.classList.add("copied");
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        showToast("Code copied to clipboard", "success", 2000);
        setTimeout(() => {
            btn.classList.remove("copied");
            btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy`;
        }, 2000);
    } catch {
        showToast("Could not copy — please select text manually", "error");
    }
};

// ─── Message Renderer ─────────────────────────────────────────────────────────
function getTimestamp() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function addMessage(text, type, opts = {}) {
    const wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${type}`;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = type === "user" ? `You · ${getTimestamp()}` : `Assistant · ${getTimestamp()}`;

    const bubble = document.createElement("div");
    bubble.className = `message ${type}`;
    if (opts.loading) bubble.classList.add("loading");

    const body = document.createElement("div");
    body.className = "msg-body";

    if (opts.loading) {
        bubble.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div> Thinking...`;
    } else if (type === "bot") {
        body.innerHTML = parseMarkdown(text);
        bubble.appendChild(body);
    } else {
        body.textContent = text;
        bubble.appendChild(body);
    }

    wrapper.appendChild(meta);
    wrapper.appendChild(bubble);
    chatBox.appendChild(wrapper);
    chatBox.scrollTop = chatBox.scrollHeight;
    return wrapper;
}

// ─── Submit Handler ───────────────────────────────────────────────────────────
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    addMessage(query, "user");
    queryInput.value = "";
    queryInput.disabled = true;
    sendBtn.disabled = true;

    const loadingWrapper = addMessage("", "bot", { loading: true });

    const formData = new FormData();
    formData.append("query", query);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token },
            body: formData
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        loadingWrapper.remove();

        if (data.success) {
            addMessage(data.message, "bot");
            showToast("Response received", "success", 2000);
        } else {
            addMessage("The assistant could not retrieve a matching response. Please try rephrasing your question.", "bot");
            showToast("No matching response found", "error");
        }
    } catch (err) {
        console.error(err);
        loadingWrapper.remove();
        addMessage("Connection failed. The backend service may be unavailable — please try again shortly.", "bot");
        showToast("Request failed — check your connection", "error");
    } finally {
        queryInput.disabled = false;
        sendBtn.disabled = false;
        queryInput.focus();
    }
});

// Submit on Enter, newline on Shift+Enter
queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event("submit"));
    }
});