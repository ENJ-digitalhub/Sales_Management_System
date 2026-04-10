const memberList = document.getElementById("memberList");
const userStatus = document.getElementById("userStatus");
const addUserSection = document.getElementById("addUserSection");
const addUserForm = document.getElementById("addUserForm");
const toggleAddUserForm = document.getElementById("toggleAddUserForm");
const userDetailModal = document.getElementById("userDetailModal");
const closeUserDetailModal = document.getElementById("closeUserDetailModal");
const userDetailName = document.getElementById("userDetailName");
const userDetailUsername = document.getElementById("userDetailUsername");
const userDetailImage = document.getElementById("userDetailImage");
const userDetailGrid = document.getElementById("userDetailGrid");
const defaultUserAvatar = "/static/img/default-avatar.svg";

function formatUserDetail(value) {
    const normalized = `${value || ""}`.trim();
    return normalized || "Not provided";
}

function openUserDetailModal(member) {
    if (!userDetailModal || !member) return;

    const fullName = `${member.dataset.firstName || ""} ${member.dataset.lastName || ""}`.trim() || "User";
    if (userDetailName) userDetailName.textContent = fullName;
    if (userDetailUsername) userDetailUsername.textContent = `@${member.dataset.username || ""}`;
    if (userDetailImage) {
        userDetailImage.src = member.dataset.imagePath || defaultUserAvatar;
        userDetailImage.alt = "Avatar";
    }

    const fields = [
        ["First Name", member.dataset.firstName],
        ["Last Name", member.dataset.lastName],
        ["Email", member.dataset.email],
        ["Username", member.dataset.username ? `@${member.dataset.username}` : ""],
        ["Role", member.dataset.role],
        ["Status", member.dataset.isActive === "true" ? "Active" : "Deactivated"],
        ["Phone", member.dataset.phone],
        ["Account Number", member.dataset.accountName],
        ["Account Owner", member.dataset.accountOwnerName],
        ["Bank Name", member.dataset.bankName],
    ];

    if (userDetailGrid) {
        userDetailGrid.innerHTML = fields.map(([label, value]) => `
            <div class="user-detail_item">
                <span>${label}</span>
                <strong>${formatUserDetail(value)}</strong>
            </div>
        `).join("");
    }

    userDetailModal.hidden = false;
}

function closeDetailsModal() {
    if (userDetailModal) userDetailModal.hidden = true;
}

function showUserStatus(message, type = "success") {
    if (!userStatus) return;
    userStatus.textContent = message;
    userStatus.className = `status-banner ${type}`;
    userStatus.hidden = false;
}

function createStatusBadge(member, isActive) {
    const activeBadge = member.querySelector(".active-badge");
    if (activeBadge) {
        activeBadge.textContent = isActive ? "Active" : "Deactivated";
        activeBadge.className = `active-badge ${isActive ? "active" : "deactivated"}`;
    }
}

if (toggleAddUserForm) {
    toggleAddUserForm.addEventListener("click", () => {
        if (!addUserSection) return;
        addUserSection.hidden = !addUserSection.hidden;
    });
}

if (addUserForm) {
    addUserForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(addUserForm);
        const payload = {
            first_name: formData.get("first_name")?.trim(),
            last_name: formData.get("last_name")?.trim(),
            username: formData.get("username")?.trim(),
            password: formData.get("password"),
            is_active: formData.get("is_active") === "on",
        };

        try {
            const response = await fetch("/api/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await response.json();

            if (!response.ok) {
                showUserStatus(data.message || "Could not create user.", "error");
                return;
            }

            showUserStatus(data.message || "User created successfully.");
            addUserForm.reset();
            addUserSection.hidden = true;
            window.location.reload();
        } catch (error) {
            console.error(error);
            showUserStatus("Something went wrong while creating user.", "error");
        }
    });
}

if (memberList) {
    memberList.addEventListener("click", async (event) => {
        const toggleButton = event.target.closest(".role-toggle");
        const activeToggle = event.target.closest(".active-toggle");
        const memberCard = event.target.closest(".member");

        if (activeToggle) {
            const userId = activeToggle.dataset.userId;
            const isActive = activeToggle.checked;

            try {
                const response = await fetch(`/api/users/${userId}/active`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_active: isActive }),
                });
                const data = await response.json();

                if (!response.ok) {
                    showUserStatus(data.message || "Could not update active status.", "error");
                    activeToggle.checked = !isActive;
                    return;
                }

                const member = activeToggle.closest(".member");
                if (member) createStatusBadge(member, isActive);

                showUserStatus(data.message || "User status updated successfully.");
            } catch (error) {
                console.error(error);
                showUserStatus("Something went wrong while updating active status.", "error");
                activeToggle.checked = !isActive;
            }
            return;
        }

        if (memberCard && memberCard.dataset.isSelf !== "true" && !event.target.closest(".member-actions")) {
            openUserDetailModal(memberCard);
            return;
        }

        if (!toggleButton || toggleButton.disabled) {
            return;
        }

        const userId = toggleButton.dataset.userId;
        const role = toggleButton.dataset.role;

        try {
            const response = await fetch(`/api/users/${userId}/role`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ role }),
            });

            const data = await response.json();
            if (!response.ok) {
                showUserStatus(data.message || "Could not update user role.", "error");
                return;
            }

            const member = toggleButton.closest(".member");
            const roleBadge = member?.querySelector(".role-badge");

            if (member && roleBadge) {
                roleBadge.className = `role-badge ${role}`;
                roleBadge.textContent = role.charAt(0).toUpperCase() + role.slice(1);

                if (role === "admin") {
                    toggleButton.textContent = "Make User";
                    toggleButton.dataset.role = "user";
                    toggleButton.className = "role-toggle demote";
                } else {
                    toggleButton.textContent = "Make Admin";
                    toggleButton.dataset.role = "admin";
                    toggleButton.className = "role-toggle promote";
                }
            }

            showUserStatus(data.message || "User role updated successfully.");
        } catch (error) {
            console.error(error);
            showUserStatus("Something went wrong while updating the role.", "error");
        }
    });
}

if (closeUserDetailModal) {
    closeUserDetailModal.addEventListener("click", closeDetailsModal);
}

if (userDetailModal) {
    userDetailModal.addEventListener("click", (event) => {
        if (event.target === userDetailModal) closeDetailsModal();
    });
}
