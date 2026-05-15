const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", async (e) => {

    e.preventDefault();

    const formData = new FormData(loginForm);

    const response = await fetch("/login", {

        method: "POST",

        body: formData
    });

    const data = await response.json();

    const message = document.getElementById("message");

    message.innerText = data.message;

    if (data.success) {

        message.style.color = "green";

        // Store user
        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );

        // Redirect
        window.location.href = "/dashboard";

    } else {

        message.style.color = "red";
    }
});