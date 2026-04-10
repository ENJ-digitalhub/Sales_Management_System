let logoutButton = document.querySelector(".logout-icon");
const globalThemeToggle = document.getElementById("globalThemeToggle");

if (logoutButton) {
    logoutButton.addEventListener("click", () => {
        alert("Logging Out ...");
    });
}

const userMenu = document.querySelector(".user-menu");
const userDropdown = document.querySelector(".user-dropdown");

if (userMenu && userDropdown) {
    userMenu.addEventListener("click", (e) => {
        e.stopPropagation();
        userDropdown.style.display = userDropdown.style.display === "block" ? "none" : "block";
    });

    document.addEventListener("click", () => {
        userDropdown.style.display = "none";
    });
}

function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    const icon = globalThemeToggle?.querySelector("i");
    if (icon) {
        icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }
}

const savedTheme = localStorage.getItem("app-theme") || "light";
applyTheme(savedTheme);

if (globalThemeToggle) {
    globalThemeToggle.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        localStorage.setItem("app-theme", nextTheme);
        applyTheme(nextTheme);
    });
}

function syncMobileMenuWithFooter() {
    const mobileBreakpoint = 1024;
    const menu = document.querySelector(".menu");
    const footer = document.querySelector("footer");
    if (!menu || !footer) return;

    const isMobile = window.innerWidth <= mobileBreakpoint;
    if (!isMobile) {
        menu.classList.remove("menu-above-footer");
        document.documentElement.style.setProperty("--footer-visible-offset", "0px");
        return;
    }

    const footerRect = footer.getBoundingClientRect();
    const visibleFooterHeight = Math.max(0, window.innerHeight - footerRect.top);
    const offset = Math.min(visibleFooterHeight, footerRect.height);
    document.documentElement.style.setProperty("--footer-visible-offset", `${offset}px`);
    menu.classList.toggle("menu-above-footer", offset > 0);
}

window.addEventListener("scroll", syncMobileMenuWithFooter, { passive: true });
window.addEventListener("resize", syncMobileMenuWithFooter);
window.addEventListener("load", syncMobileMenuWithFooter);
syncMobileMenuWithFooter();
