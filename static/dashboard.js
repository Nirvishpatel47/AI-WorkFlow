const token = localStorage.getItem("token");
if (!token) window.location.href = "/";

function parseJwt(token) {
    try { return JSON.parse(atob(token.split(".")[1])); }
    catch { return null; }
}

const user = parseJwt(token);
if (!user) window.location.href = "/";

// Set user info
const usernameEl = document.getElementById("username");
const useremailEl = document.getElementById("useremail");
const avatarEl = document.getElementById("userAvatar");
usernameEl.innerText = user.name || "User";
useremailEl.innerText = user.email || "";
if (avatarEl) avatarEl.innerText = (user.name || "U").charAt(0).toUpperCase();

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const messageEl = document.getElementById("message");
const documentsList = document.getElementById("documentsList");
const docsMessage = document.getElementById("docsMessage");
const toastContainer = document.getElementById("toastContainer");

// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(text, type = "info", duration = 3500) {
    const icons = {
        success: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        error: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        info: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
    };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type]}</span><span>${text}</span>
        <button class="toast-dismiss" onclick="this.parentElement.remove()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>`;
    toastContainer.appendChild(toast);
    setTimeout(() => { toast.style.opacity = "0"; toast.style.transition = "opacity 0.3s"; setTimeout(() => toast.remove(), 300); }, duration);
}

// ─── Inline Banner ────────────────────────────────────────────────────────────
function displayFeedback(element, text, status) {
    const icons = {
        success: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        error: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        info: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line></svg>`
    };

    element.innerHTML = `${icons[status] || ''}<span>${text}</span>`;
    element.style.display = "flex";

    const styles = {
        success: { bg: "rgba(34, 197, 94, 0.1)", color: "var(--success)", border: "rgba(34, 197, 94, 0.2)" },
        error:   { bg: "rgba(239, 68, 68, 0.1)", color: "var(--error)",   border: "rgba(239, 68, 68, 0.2)" },
        info:    { bg: "rgba(59, 201, 219, 0.08)", color: "var(--accent-color)", border: "rgba(59, 201, 219, 0.2)" }
    };
    const s = styles[status] || styles.info;
    element.style.background = s.bg;
    element.style.color = s.color;
    element.style.borderColor = s.border;
}

// ─── Fetch Documents ──────────────────────────────────────────────────────────
async function fetchDocuments() {
    try {
        const response = await fetch("/show_documents", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        const data = await response.json();
        if (data.success) {
            renderDocuments(data.Documents_data);
        } else {
            displayFeedback(docsMessage, data.message || "Could not load documents.", "error");
        }
    } catch {
        displayFeedback(docsMessage, "Failed to reach the server. Check your connection.", "error");
    }
}

function renderDocuments(documents) {
    documentsList.innerHTML = "";
    docsMessage.style.display = "none";

    if (!documents || documents.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                No documents indexed yet.<br>Upload your first file to get started.
            </div>`;
        return;
    }

    documents.forEach(doc => {
        let formattedDate = "Unknown date";
        if (doc.created_at) {
            try {
                formattedDate = new Date(doc.created_at).toLocaleDateString(undefined, {
                    year: 'numeric', month: 'short', day: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
            } catch {}
        }

        const ext = (doc.extension || "file").toUpperCase();
        const item = document.createElement("div");
        item.className = "document-item";
        item.innerHTML = `
            <div class="document-info">
                <div class="doc-icon">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                </div>
                <div class="doc-text">
                    <div class="document-name">${doc.file_name || 'Document'}.${doc.extension || ''}</div>
                    <div class="document-meta">Uploaded ${formattedDate} · ${ext}</div>
                </div>
            </div>
            <button class="delete-btn" onclick="deleteDocument(${doc.id})">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6M14 11v6"></path></svg>
                Delete
            </button>`;
        documentsList.appendChild(item);
    });
}

// ─── Delete Document ──────────────────────────────────────────────────────────
window.deleteDocument = async (documentId) => {
    if (!confirm("Permanently delete this document from the index?")) return;
    try {
        const response = await fetch(`/delete_document?Document_id=${documentId}`, {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        const data = await response.json();
        if (data.success) {
            showToast("Document deleted successfully", "success");
            fetchDocuments();
        } else {
            showToast(data.message || "Delete failed", "error");
        }
    } catch {
        showToast("Network error — could not delete document", "error");
    }
};

// ─── Upload Form ──────────────────────────────────────────────────────────────
uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;

    const btn = uploadForm.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 0.8s linear infinite"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-.07-4.53"></path></svg> Uploading...`;

    displayFeedback(messageEl, "Uploading your file...", "info");
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/addDocument", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token },
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            displayFeedback(messageEl, data.message || "File uploaded and indexed successfully.", "success");
            showToast("Document indexed successfully", "success");
            uploadForm.reset();
            fetchDocuments();
        } else {
            displayFeedback(messageEl, data.message || "Upload failed.", "error");
            showToast("Upload failed — " + (data.message || "unknown error"), "error");
        }
    } catch {
        displayFeedback(messageEl, "Connection error. Please try again.", "error");
        showToast("Upload failed — server unreachable", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 16 12 12 8 16"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path></svg> Upload File`;
    }
});

fetchDocuments();