const token = localStorage.getItem("token");
if (!token) window.location.href = "/";

const logoutBtn = document.getElementById("logoutBtn");
const toastContainer = document.getElementById("toastContainer");

function showToast(text, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${text}</span>`;
    toastContainer.appendChild(toast);
}

logoutBtn.addEventListener("click", async () => {
    logoutBtn.disabled = true;
    logoutBtn.innerText = "Processing...";

    try {
        const response = await fetch("/logout", {
            method: "POST",
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await response.json();

        if (data.success) {
            showToast("Session closed successfully", "success");
            // Clear storage parameters entirely
            localStorage.removeItem("token");
            setTimeout(() => window.location.href = "/", 800);
        } else {
            showToast(data.message || "Logout failed", "error");
            logoutBtn.disabled = false;
            logoutBtn.innerHTML = `Sign Out of Account`;
        }
    } catch {
        showToast("Connection issue detected during session release.", "error");
        logoutBtn.disabled = false;
        logoutBtn.innerHTML = `Sign Out of Account`;
    }
});