const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/";
}

function parseJwt(token) {
    try {
        return JSON.parse(atob(token.split(".")[1]));
    } catch (e) {
        return null;
    }
}

const user = parseJwt(token);
if (!user) {
    window.location.href = "/";
}

document.getElementById("username").innerText = user.name || "User";
document.getElementById("useremail").innerText = user.email || "";

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const message = document.getElementById("message");
const documentsList = document.getElementById("documentsList");
const docsMessage = document.getElementById("docsMessage");

function displayFeedback(element, text, status) {
    element.innerText = text;
    element.style.display = "block";
    
    if (status === "success") {
        element.style.background = "rgba(16, 185, 129, 0.12)";
        element.style.color = "var(--success)";
        element.style.border = "1px solid rgba(16, 185, 129, 0.2)";
    } else if (status === "error") {
        element.style.background = "rgba(239, 68, 68, 0.12)";
        element.style.color = "var(--error)";
        element.style.border = "1px solid rgba(239, 68, 68, 0.2)";
    } else {
        element.style.background = "rgba(59, 130, 246, 0.12)";
        element.style.color = "var(--info)";
        element.style.border = "1px solid rgba(59, 130, 246, 0.2)";
    }
}

async function fetchDocuments() {
    try {
        const response = await fetch("/show_documents", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            renderDocuments(data.Documents_data);
        } else {
            displayFeedback(docsMessage, data.message, "error");
        }
    } catch (error) {
        displayFeedback(docsMessage, "Error fetching repository documents.", "error");
    }
}

function renderDocuments(documents) {
    documentsList.innerHTML = "";
    docsMessage.style.display = "none";

    if (!documents || documents.length === 0) {
        documentsList.innerHTML = "<p style='color: var(--text-muted); font-size: 14px;'>No documents indexed yet.</p>";
        return;
    }

    documents.forEach(doc => {
        let formattedDate = "Unknown Date";
        if (doc.created_at) {
            try {
                const dateObj = new Date(doc.created_at);
                formattedDate = dateObj.toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                console.error(e);
            }
        }

        const item = document.createElement("div");
        item.className = "document-item";
        item.innerHTML = `
            <div class="document-info">
                <span class="document-name">${doc.file_name || 'Document'}.${doc.extension || ''}</span>
                <span class="document-meta">Uploaded: ${formattedDate}</span>
            </div>
            <button class="delete-btn" onclick="deleteDocument(${doc.id})">Delete</button>
        `;
        documentsList.appendChild(item);
    });
}

window.deleteDocument = async (documentId) => {
    if (!confirm("Are you sure you want to permanently delete this document mapping?")) return;

    try {
        const response = await fetch(`/delete_document?Document_id=${documentId}`, {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        const data = await response.json();

        if (data.success) {
            displayFeedback(docsMessage, "Document dropped successfully.", "success");
            fetchDocuments();
        } else {
            displayFeedback(docsMessage, data.message, "error");
        }
    } catch (error) {
        displayFeedback(docsMessage, "Network pipeline exception dropped transaction.", "error");
    }
};

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    displayFeedback(message, "Uploading vector payload...", "info");

    try {
        const response = await fetch("/addDocument", {
            method: "POST",
            headers: {
                "Authorization": "Bearer " + token
            },
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            displayFeedback(message, data.message || "File uploaded successfully", "success");
            uploadForm.reset();
            fetchDocuments();
        } else {
            displayFeedback(message, data.message, "error");
        }
    } catch (error) {
        displayFeedback(message, "Pipeline initialization failed.", "error");
    }
});

fetchDocuments();