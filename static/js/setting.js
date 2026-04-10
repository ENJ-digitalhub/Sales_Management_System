const settingItems = document.querySelectorAll(".settings-item[data-panel]");
const settingsPanels = document.querySelectorAll(".settings-panel");
const settingsFeedback = document.getElementById("settingsFeedback");
const editAccountTrigger = document.getElementById("editAccountTrigger");
const themeToggle = document.getElementById("themeToggle");

function showSettingsFeedback(message, type = "success") {
    if (!settingsFeedback) {
        return;
    }

    settingsFeedback.textContent = message;
    settingsFeedback.className = `settings-feedback ${type}`;
    settingsFeedback.hidden = false;
}

function openSettingsPanel(panelId) {
    settingsPanels.forEach((panel) => {
        panel.hidden = panel.id !== panelId;
    });
}

async function submitSettingsForm(url, form, successMessage) {
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
        const response = await fetch(url, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json();

        if (!response.ok) {
            showSettingsFeedback(data.message || "Could not save settings.", "error");
            return;
        }

        showSettingsFeedback(data.message || successMessage, "success");
    } catch (error) {
        console.error(error);
        showSettingsFeedback("Something went wrong while saving settings.", "error");
    }
}

async function submitMultipartSettingsForm(url, form, successMessage) {
    const formData = new FormData(form);

    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
            showSettingsFeedback(data.message || "Could not save settings.", "error");
            return false;
        }

        showSettingsFeedback(data.message || successMessage, "success");
        return true;
    } catch (error) {
        console.error(error);
        showSettingsFeedback("Something went wrong while saving settings.", "error");
        return false;
    }
}

settingItems.forEach((item) => {
    item.addEventListener("click", () => {
        openSettingsPanel(item.dataset.panel);
    });
});

const passwordForm = document.getElementById("passwordForm");
if (passwordForm) {
    passwordForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitSettingsForm("/api/settings/password", passwordForm, "Password updated successfully.");
        passwordForm.reset();
    });
}

const accountForm = document.getElementById("accountForm");
if (accountForm) {
    accountForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitSettingsForm("/api/settings/account", accountForm, "Account details updated successfully.");
    });
}

const emailForm = document.getElementById("emailForm");
if (emailForm) {
    emailForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitSettingsForm("/api/settings/email", emailForm, "Email updated successfully.");
    });
}

const profileForm = document.getElementById("profileForm");
if (profileForm) {
    profileForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const didSave = await submitMultipartSettingsForm("/api/settings/profile", profileForm, "Profile details updated successfully.");
        if (didSave) {
            window.setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    });
}

const removeProfileImageButton = document.getElementById("removeProfileImageButton");
if (removeProfileImageButton) {
    removeProfileImageButton.addEventListener("click", async () => {
        try {
            const response = await fetch("/api/settings/profile/image", {
                method: "DELETE",
            });
            const data = await response.json();

            if (!response.ok) {
                showSettingsFeedback(data.message || "Could not remove profile picture.", "error");
                return;
            }

            showSettingsFeedback(data.message || "Profile picture removed successfully.", "success");
            window.setTimeout(() => {
                window.location.reload();
            }, 500);
        } catch (error) {
            console.error(error);
            showSettingsFeedback("Something went wrong while removing profile picture.", "error");
        }
    });
}

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
}

const savedTheme = localStorage.getItem("app-theme") || "light";
applyTheme(savedTheme);

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        localStorage.setItem("app-theme", nextTheme);
        applyTheme(nextTheme);
        showSettingsFeedback(`Theme switched to ${nextTheme}.`);
    });
}
