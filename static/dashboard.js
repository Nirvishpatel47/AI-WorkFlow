const token = localStorage.getItem("token");

// redirect if not logged in
if (!token) {
    window.location.href = "/";
}

// decode only for UI (optional)
function parseJwt(token) {
    return JSON.parse(atob(token.split(".")[1]));
}

const user = parseJwt(token);

// display
document.getElementById("username").innerText = user.name;
document.getElementById("useremail").innerText = user.email;

// Redirect if not logged in
if (!user) {

    window.location.href = "/";
}

// Display user info
document.getElementById("username").innerText =
    user.name;

document.getElementById("useremail").innerText =
    user.email;


// ----------------------------
// Upload Logic
// ----------------------------

const uploadForm = document.getElementById("uploadForm");

uploadForm.addEventListener("submit", async (e) => {

    e.preventDefault();

    const fileInput = document.getElementById("fileInput");

    const file = fileInput.files[0];

    if (!file) {

        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    fetch("/addDocument", {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: formData
    });

    const data = await response.json();

    const message = document.getElementById("message");

    const output = document.getElementById("output");

    if (data.success) {

        message.innerText = "File uploaded successfully";

        message.style.color = "green";

        output.value = data.text;

    } else {

        message.innerText = data.message;

        message.style.color = "red";
    }
});