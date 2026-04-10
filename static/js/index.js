let loginModal = document.getElementById("login");
let signupModal = document.getElementById("signup");

let loginBtn = document.getElementById("loginBtn");
let signupBtn = document.getElementById("signupBtn");

let closeBtns = document.querySelectorAll(".closeBtn");

// Initial modals state
window.onload = () => {
    loginModal.style.display = "none";
    signupModal.style.display = "none";
    const params = new URLSearchParams(window.location.search);
    if (params.get("approved") === "1") {
        alert("Your account has been approved. You can now log in.");
        window.history.replaceState({}, "", window.location.pathname);
    }
};

// Open modals
loginBtn.onclick = () => loginModal.style.display = "flex";
signupBtn.onclick = () => signupModal.style.display = "flex";

// Close modals
closeBtns.forEach(btn => {
    btn.onclick = () => {
        loginModal.style.display = "none";
        signupModal.style.display = "none";
    };
});

// Initialize the two forms
const loginForm = document.querySelector(".login_form");
const signupForm = document.querySelector(".signup_form");

loginForm.querySelector("button").addEventListener("click", (e) => {
    e.preventDefault();
    const username = loginForm.querySelector('input[type="text"]').value;
    const password = loginForm.querySelector('input[type="password"]').value;

    if (!username || !password) {
        alert("Please enter both username and password");
        return;
    }

    alert("Loging In ...");
    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/JSON" },
        body: JSON.stringify({ username, password })
    })
        .then(res => {
            if (res.redirected) {
                window.location.href = res.url;
                return;
            }
            return res.json();
        })
        .then(data => {
            if (!data) {
                return;
            }
            if (data.redirect) {
                window.location.href = data.redirect;
                return;
            }
            alert(data.message);
            loginForm.reset();
        })
        .catch(err => {
            console.error(err);
            alert("Something went wrong")
        });
    // alert("Login successful (dummy check)");
});

signupForm.querySelector("button").addEventListener("click", (e) => {
    e.preventDefault();
    const firstname = signupForm.querySelector('input[name="firstname"]').value;
    const lastname = signupForm.querySelector('input[name="lastname"]').value;
    const username = signupForm.querySelector('input[name="username"]').value;
    const password = signupForm.querySelector('input[name="password"]').value;
    const confirmPassword = signupForm.querySelector('input[name="confirmPassword"]').value;

    if (!firstname || !lastname || !username || !password || !confirmPassword) {
        alert("All fields are required!");
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    if (password.length < 6) {
        alert("Password must be at least 6 characters long");
        return;
    }

    alert(username + " Signing in ....");
    fetch("/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firstname, lastname, username, password })
    })
        .then(res => {
            if (res.redirected) {
                window.location.href = res.url;
                return;
            }
            return res.json();
        })
        .then(data => {
            if (!data) {
                return;
            }
            if (data.redirect) {
                window.location.href = data.redirect;
                return;
            }
            alert(data.message);
            signupForm.reset();
        })
        .catch(err => {
            console.error(err);
            alert("Something went wrong");
        });
});
