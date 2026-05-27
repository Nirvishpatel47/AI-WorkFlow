// static/dashboard.js

const token = localStorage.getItem("token");
if (!token) window.location.href = "/";

function parseJwt(token) {
    try { return JSON.parse(atob(token.split(".")[1])); }
    catch { return null; }
}

const user = parseJwt(token);
if (!user) window.location.href = "/";

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
const dropZone = document.getElementById("dropZone");
const filePreviewContainer = document.getElementById("filePreviewContainer");

// Internal state tracking queue for continuous cross-browser multi-file handling
let activeFilesBatch = [];

// ─── Toast Feedback UI ────────────────────────────────────────────────────────
function showToast(text, type = "info", duration = 3500) {
    const icons = {
        success: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        error: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        info: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line></svg>`
    };
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type]}</span><span>${text}</span>
        <button class="toast-dismiss" onclick="this.parentElement.remove()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>`;
    toastContainer.appendChild(toast);
    setTimeout(() => { 
        toast.style.opacity = "0"; 
        toast.style.transition = "opacity 0.3s"; 
        setTimeout(() => toast.remove(), 300); 
    }, duration);
}

function displayFeedback(element, text, status) {
    if (!element) return;
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

// ─── Drag & Drop Recursive Engine ─────────────────────────────────────────────
if (dropZone && fileInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev => {
        dropZone.addEventListener(ev, (e) => { 
            e.preventDefault(); 
            e.stopPropagation(); 
        }, false);
    });

    ['dragenter', 'dragover'].forEach(ev => {
        dropZone.addEventListener(ev, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(ev => {
        dropZone.addEventListener(ev, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', async (e) => {
        const items = e.dataTransfer.items;
        if (!items || items.length === 0) return;

        let droppedFilesQueue = [];

        async function traverseDirectoryEntry(entry) {
            if (!entry) return;
            if (entry.isFile) {
                const file = await new Promise(res => entry.file(res));
                droppedFilesQueue.push(file);
            } else if (entry.isDirectory) {
                const dirReader = entry.createReader();
                const entries = await new Promise(res => dirReader.readEntries(res));
                for (let i = 0; i < entries.length; i++) {
                    await traverseDirectoryEntry(entries[i]);
                }
            }
        }

        const traversalPromises = [];
        for (let i = 0; i < items.length; i++) {
            if (items[i].kind === 'file') {
                const entry = items[i].webkitGetAsEntry();
                if (entry) traversalPromises.push(traverseDirectoryEntry(entry));
            }
        }

        await Promise.all(traversalPromises);

        if (droppedFilesQueue.length > 0) {
            activeFilesBatch = activeFilesBatch.concat(droppedFilesQueue);
            renderFilePreviews(activeFilesBatch);
        }
    });

    dropZone.addEventListener('click', (e) => {
        if (e.target.tagName !== 'INPUT') {
            fileInput.click();
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            activeFilesBatch = activeFilesBatch.concat(Array.from(fileInput.files));
            renderFilePreviews(activeFilesBatch);
        }
    });
}

function renderFilePreviews(files) {
    if (!filePreviewContainer) return;
    filePreviewContainer.innerHTML = "";
    if (!files || files.length === 0) return;

    const maxPreviews = 3;
    const itemsCount = Math.min(files.length, maxPreviews);

    for (let i = 0; i < itemsCount; i++) {
        const file = files[i];
        const previewItem = document.createElement("div");
        previewItem.className = "preview-item";
        previewItem.innerHTML = `
            <div class="preview-file-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-color)" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <span>${file.name}</span>
            </div>
            <span class="preview-file-size">${(file.size / 1024).toFixed(1)} KB</span>`;
        filePreviewContainer.appendChild(previewItem);
    }

    if (files.length > maxPreviews) {
        const excessItem = document.createElement("div");
        excessItem.className = "preview-item";
        excessItem.style.justifyContent = "center";
        excessItem.style.color = "var(--accent-secondary)";
        excessItem.innerHTML = `<strong>+ ${files.length - maxPreviews} more files in batch processing queue</strong>`;
        filePreviewContainer.appendChild(excessItem);
    }
}

// ─── Fetch Documents ──────────────────────────────────────────────────────────
async function fetchDocuments() {
    try {
        const response = await fetch("/show_documents", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });
        const data = await response.json();
        if (data.success) renderDocuments(data.Documents_data);
        else displayFeedback(docsMessage, data.message || "Could not load documents.", "error");
    } catch {
        displayFeedback(docsMessage, "Failed to reach the server. Check your connection.", "error");
    }
}

function renderDocuments(documents) {
    documentsList.innerHTML = "";
    docsMessage.style.display = "none";

    if (!documents || documents.length === 0) {
        documentsList.innerHTML = `<div class="empty-state">No documents indexed yet.<br>Upload files to get started.</div>`;
        return;
    }

    documents.forEach(doc => {
        let formattedDate = "Unknown date";
        if (doc.created_at) {
            try {
                formattedDate = new Date(doc.created_at).toLocaleDateString(undefined, {
                    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
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
            <button class="delete-btn" onclick="deleteDocument(${doc.id})">Delete</button>`;
        documentsList.appendChild(item);
    });
}

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
        } else { showToast(data.message || "Delete failed", "error"); }
    } catch { showToast("Network error — could not delete document", "error"); }
};

// ─── Pipeline Upload Submission ───────────────────────────────────────────────
uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    if (!activeFilesBatch || activeFilesBatch.length === 0) {
        displayFeedback(messageEl, "Please select or drag-drop valid documents first.", "error");
        return;
    }

    const btn = uploadForm.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.innerHTML = "Processing files...";

    const MAX_FILE_SIZE = 15 * 1024 * 1024;
    const BLACKLISTED_EXTENSIONS = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.z', '.exe'];
    
    // Instantiate target data structure container mapping back to single files multi-part array key
    const formData = new FormData();
    let validFilesCount = 0;

    for (let i = 0; i < activeFilesBatch.length; i++) {
        const file = activeFilesBatch[i];
        const filenameLower = file.name.toLowerCase();
        
        // Skip system metadata layer files
        if (file.name.startsWith("._") || filenameLower === ".ds_store") continue;

        const isBlacklisted = BLACKLISTED_EXTENSIONS.some(ext => filenameLower.endsWith(ext));
        if (isBlacklisted) {
            showToast(`Skipped blocked extension: ${file.name}`, "error");
            continue;
        }
        if (file.size > MAX_FILE_SIZE) {
            showToast(`Oversized file (>15MB): ${file.name}`, "error");
            continue;
        }

        // Standard dynamic field mapping matching FastAPI: files: list[UploadFile]
        formData.append("files", file);
        validFilesCount++;
    }

    if (validFilesCount === 0) {
        displayFeedback(messageEl, "No valid parseable items present in submission payload.", "error");
        btn.disabled = false;
        btn.innerHTML = "Upload Collective Batch";
        return;
    }

    displayFeedback(messageEl, `Transmitting batch payload containing ${validFilesCount} document(s)...`, "info");

    try {
        const response = await fetch("/addDocument", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token },
            body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
            const successNum = data.uploaded ? data.uploaded.length : 0;
            const failedNum = data.failed ? data.failed.length : 0;

            if (failedNum === 0) {
                displayFeedback(messageEl, `Successfully indexed all ${successNum} documents!`, "success");
                showToast(`Successfully uploaded ${successNum} files.`, "success");
            } else {
                displayFeedback(messageEl, `Partial processing: Indexed ${successNum} files successfully. ${failedNum} failed.`, "info");
                data.failed.forEach(f => {
                    showToast(`Failed [${f.filename}]: ${f.reason}`, "error");
                });
            }
        } else { 
            displayFeedback(messageEl, `Engine Rejection: ${data.message || 'Status Code ' + response.status}`, "error"); 
            showToast("Server refused processing package.", "error");
        }
    } catch (err) { 
        console.error(err);
        displayFeedback(messageEl, "Network failure transmitting payload batch package.", "error");
        showToast("Network error during upload.", "error"); 
    } finally {
        // Clear runtime state tracking boundaries safely
        uploadForm.reset();
        activeFilesBatch = [];
        filePreviewContainer.innerHTML = "";
        btn.disabled = false;
        btn.innerHTML = "Upload Collective Batch";
        fetchDocuments();
    }
});

fetchDocuments();