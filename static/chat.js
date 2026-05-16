const chatForm = document.getElementById("chatForm");
const chatBox = document.getElementById("chatBox");
const queryInput = document.getElementById("queryInput");

function addMessage(text, type) {
    const div = document.createElement("div");
    div.classList.add("message", type);
    div.innerText = text;
    chatBox.appendChild(div);

    chatBox.scrollTop = chatBox.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const query = queryInput.value.trim();
    if (!query) return;

    // show user message
    addMessage(query, "user");

    queryInput.value = "";

    const formData = new FormData();
    formData.append("query", query);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            addMessage(data.message, "bot");
        } else {
            addMessage(data.message, "bot");
        }

    } catch (err) {
        addMessage("Server error. Try again.", "bot");
    }
});