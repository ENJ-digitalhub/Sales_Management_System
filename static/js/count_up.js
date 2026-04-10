function formatCountValue(value, format) {
    if (format === "currency") {
        return `N${Number(value).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    }

    return Math.round(Number(value)).toLocaleString();
}

function animateCountUp(element) {
    if (!element || element.dataset.countAnimated === "true") {
        return;
    }

    const rawValue = Number(element.dataset.value || 0);
    if (Number.isNaN(rawValue)) {
        return;
    }

    const format = element.dataset.format || "integer";
    const duration = 550;
    const start = performance.now();

    function frame(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const currentValue = rawValue * eased;
        element.textContent = formatCountValue(currentValue, format);

        if (progress < 1) {
            requestAnimationFrame(frame);
            return;
        }

        element.textContent = formatCountValue(rawValue, format);
        element.dataset.countAnimated = "true";
    }

    requestAnimationFrame(frame);
}

function animateCountUps(root = document) {
    root.querySelectorAll(".count-up").forEach(animateCountUp);
}
