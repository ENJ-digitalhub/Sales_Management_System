const markAllNotificationsReadButton = document.getElementById("markAllNotificationsRead");
const notificationsFeedback = document.getElementById("notificationsFeedback");

function showNotificationsFeedback(message, type = "success") {
    if (!notificationsFeedback) {
        return;
    }

    notificationsFeedback.textContent = message;
    notificationsFeedback.className = `notifications-feedback ${type}`;
    notificationsFeedback.hidden = false;
}

if (markAllNotificationsReadButton) {
    markAllNotificationsReadButton.addEventListener("click", async () => {
        markAllNotificationsReadButton.disabled = true;

        try {
            const response = await fetch("/api/notifications/mark-all-read", {
                method: "POST",
            });
            const data = await response.json();

            if (!response.ok) {
                showNotificationsFeedback(data.message || "Could not mark notifications as read.", "error");
                markAllNotificationsReadButton.disabled = false;
                return;
            }

            document.querySelectorAll(".notification-badge").forEach((badge) => badge.remove());
            showNotificationsFeedback(data.message || "All notifications marked as read.");
        } catch (error) {
            console.error(error);
            showNotificationsFeedback("Something went wrong while updating notifications.", "error");
            markAllNotificationsReadButton.disabled = false;
        }
    });
}
