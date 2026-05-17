const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/";
}

const chatForm = document.getElementById("chatForm");
const chatBox = document.getElementById("chatBox");
const queryInput = document.getElementById("queryInput");

/**
 * Parses raw textual patterns into secure, structured HTML components.
 * Handles Code Blocks, Inline Code, and Execution Traces safely.
 */
function parseStructuredContent(rawText) {
    let formattedHtml = rawText;

    // 1. Parse RAG Execution System Traces: [TRACE] content [/TRACE]
    const traceRegex = /\[TRACE\]([\s\S]*?)\[\/TRACE\]/g;
    formattedHtml = formattedHtml.replace(traceRegex, (match, traceContent) => {
        return `
            <div class="rag-trace">
                <div class="trace-header">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    Vector Query Execution Pipeline Trace
                </div>
                <div class="trace-node">${escapeHtml(traceContent.trim())}</div>
            </div>
        `;
    });

    // 2. Parse Multi-line Block Code: ```code```
    const codeBlockRegex = /```([\s\S]*?)```/g;
    formattedHtml = formattedHtml.replace(codeBlockRegex, (match, codeContent) => {
        return `<pre><code>${escapeHtml(codeContent.trim())}</code></pre>`;
    });

    // 3. Parse Short Inline Code Elements: `variable`
    const inlineCodeRegex = /`([^`\n]+)`/g;
    formattedHtml = formattedHtml.replace(inlineCodeRegex, (match, codeText) => {
        return `<code>${escapeHtml(codeText)}</code>`;
    });

    return formattedHtml;
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function addMessage(text, type) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", type);

    const bodyDiv = document.createElement("div");
    bodyDiv.className = "msg-body";

    if (type === "bot") {
        // Apply our structured parsing rules to assistant outputs
        bodyDiv.innerHTML = parseStructuredContent(text);
    } else {
        bodyDiv.innerText = text; // Plain text escaping for user messages
    }

    messageDiv.appendChild(bodyDiv);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    return messageDiv;
}

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const query = queryInput.value.trim();
    if (!query) return;

    addMessage(query, "user");
    queryInput.value = "";

    const loadingBubble = addMessage("Analyzing indices...", "bot");
    loadingBubble.style.opacity = "0.5";

    const formData = new FormData();
    formData.append("query", query);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP Error Status: ${response.status}`);
        }

        const data = await response.json();
        loadingBubble.remove();

        if (data.success) {
            addMessage(data.message, "bot");
        } else {
            addMessage("Unable to successfully extract a matching data node response block.", "bot");
        }

    } catch (err) {
        console.error(err);
        loadingBubble.remove();
        addMessage("Communication failure. Core database execution or vector space extraction timed out.", "bot");
    }
});