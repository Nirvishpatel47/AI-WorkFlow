const user = JSON.parse(
    localStorage.getItem("user")
);

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

    const response = await fetch("/addDocument", {

        method: "POST",

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