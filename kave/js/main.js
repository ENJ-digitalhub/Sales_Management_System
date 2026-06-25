/* ===========================================================
   KAVE TECHNOLOGIES — MAIN.JS
   Smooth scrolling, scroll-triggered fade-ins, mobile nav toggle,
   and small interaction touches.
   =========================================================== */

document.addEventListener("DOMContentLoaded", () => {
  setYear();
  initMobileNav();
  initSmoothScroll();
  initFadeInOnScroll();
  initButtonRipple();
});

/* -----------------------------------------------------------
   Footer year
   ----------------------------------------------------------- */
function setYear() {
  const yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }
}

/* -----------------------------------------------------------
   Mobile menu toggle
   ----------------------------------------------------------- */
function initMobileNav() {
  const toggle = document.getElementById("navToggle");
  const links = document.getElementById("navLinks");

  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    const isOpen = links.classList.toggle("is-open");
    toggle.classList.toggle("is-open", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  // Close menu after a link is tapped
  links.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      links.classList.remove("is-open");
      toggle.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

/* -----------------------------------------------------------
   Smooth scrolling for in-page anchors
   (CSS scroll-behavior already covers most cases; this adds
   a small offset for the fixed nav and graceful fallback.)
   ----------------------------------------------------------- */
function initSmoothScroll() {
  const navHeight = document.getElementById("nav")?.offsetHeight || 0;

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (!targetId || targetId === "#") return;

      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();

      const top =
        target.getBoundingClientRect().top + window.scrollY - navHeight - 12;

      window.scrollTo({
        top,
        behavior: "smooth",
      });
    });
  });
}

/* -----------------------------------------------------------
   Fade-in on scroll using IntersectionObserver
   ----------------------------------------------------------- */
function initFadeInOnScroll() {
  const targets = document.querySelectorAll(".fade-in");
  if (!targets.length) return;

  // If the browser doesn't support IntersectionObserver, just show everything.
  if (!("IntersectionObserver" in window)) {
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
      rootMargin: "0px 0px -40px 0px",
    }
  );

  targets.forEach((el) => observer.observe(el));
}

/* -----------------------------------------------------------
   Subtle press feedback on buttons (beyond CSS :hover)
   ----------------------------------------------------------- */
function initButtonRipple() {
  const buttons = document.querySelectorAll(".btn");

  buttons.forEach((btn) => {
    btn.addEventListener("pointerdown", () => {
      btn.style.transform = "scale(0.97)";
    });

    ["pointerup", "pointerleave", "pointercancel"].forEach((evt) => {
      btn.addEventListener(evt, () => {
        btn.style.transform = "";
      });
    });
  });
}