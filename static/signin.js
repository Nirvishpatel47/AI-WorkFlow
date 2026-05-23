const signupForm = document.getElementById("signupForm");
const messageEl = document.getElementById("message");

signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = signupForm.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.textContent = "Creating account...";

    messageEl.style.display = "none";

    const formData = new FormData(signupForm);

    try {
        const response = await fetch("/signin", { method: "POST", body: formData });
        const data = await response.json();

        messageEl.style.display = "block";
        messageEl.textContent = data.message;

        if (data.success) {
            messageEl.style.background = "rgba(34, 197, 94, 0.1)";
            messageEl.style.color = "#22C55E";
            messageEl.style.border = "1px solid rgba(34, 197, 94, 0.2)";
            localStorage.setItem("token", data.token);
            setTimeout(() => window.location.href = "/dashboard", 700);
        } else {
            messageEl.style.background = "rgba(239, 68, 68, 0.1)";
            messageEl.style.color = "#EF4444";
            messageEl.style.border = "1px solid rgba(239, 68, 68, 0.2)";
            btn.disabled = false;
            btn.textContent = "Create Account";
        }
    } catch {
        messageEl.style.display = "block";
        messageEl.textContent = "Connection error. Please try again.";
        messageEl.style.background = "rgba(239, 68, 68, 0.1)";
        messageEl.style.color = "#EF4444";
        messageEl.style.border = "1px solid rgba(239, 68, 68, 0.2)";
        btn.disabled = false;
        btn.textContent = "Create Account";
    }
});