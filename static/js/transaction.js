const transactionHistory = document.getElementById("transactionHistory");
const transactionLoadIndicator = document.getElementById("transactionLoadIndicator");
const transactionScrollSentinel = document.getElementById("transactionScrollSentinel");
const categoryFilterSelect = document.getElementById("categoryFilterSelect");
const statusFilterSelect = document.getElementById("statusFilterSelect");
const detailModal = document.getElementById("transactionDetailModal");
const detailBody = document.getElementById("transactionDetailBody");
const detailCloseButton = document.getElementById("detailModalClose");

let transactionOffset = Number(transactionHistory?.dataset.initialCount || 0);
let isLoadingTransactions = false;
let hasMoreTransactions = transactionOffset >= 50;
let transactionFilters = { category: "", status: "" };

function formatTransactionAmount(amount) {
    return `N${Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function createAttachmentMarkup(label, path) {
    if (!path) return "";
    const isImage = /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(path);
    return `
        <div class="detail-attachment">
            <strong>${label}</strong>
            <a href="${path}" target="_blank" rel="noopener noreferrer">Open file</a>
            ${isImage ? `<img src="${path}" alt="${label}">` : `<div class="file-pill">Preview available in new tab</div>`}
        </div>
    `;
}

function createAuditMarkup(auditHistory) {
    if (!auditHistory?.length) {
        return `<div class="detail-card"><strong>History</strong><p>No edits or cancellations recorded yet.</p></div>`;
    }

    return `
        <div class="detail-card">
            <strong>History</strong>
            <div class="audit-list">
                ${auditHistory.map((item) => `
                    <div class="audit-item">
                        <span class="audit-action">${item.action}</span>
                        <span>${item.created_at}</span>
                    </div>
                `).join("")}
            </div>
        </div>
    `;
}

function createTransactionItem(transaction) {
    const item = document.createElement("article");
    item.className = "transaction-item";
    item.dataset.transactionId = transaction.id;
    item.innerHTML = `
        <div class="transaction-main">
            <strong>@${transaction.username}</strong>
            <div class="transaction-badges">
                <span class="transaction-type ${transaction.type}">${transaction.type.charAt(0).toUpperCase() + transaction.type.slice(1)}</span>
                <span class="transaction-status ${transaction.status}">${transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}</span>
            </div>
            <span class="transaction-product">${transaction.product_name}</span>
        </div>
        <div class="transaction-meta">
            <strong class="transaction-amount">${formatTransactionAmount(transaction.amount)}</strong>
            <span class="transaction-date">${transaction.created_at}</span>
        </div>
    `;
    item.addEventListener("click", () => showTransactionDetails(transaction.id));
    return item;
}

async function showTransactionDetails(transactionId) {
    if (!detailModal || !detailBody) return;

    detailBody.innerHTML = "<p>Loading details...</p>";
    detailModal.hidden = false;

    try {
        const response = await fetch(`/api/transactions/${transactionId}`);
        const data = await response.json();
        if (!response.ok) {
            detailBody.innerHTML = `<p>${data.message || "Could not load transaction details."}</p>`;
            return;
        }

        detailBody.innerHTML = `
            <div class="detail-grid">
                <div class="detail-card"><strong>User</strong><span>@${data.username}</span></div>
                <div class="detail-card"><strong>Product</strong><span>${data.product_name}</span></div>
                <div class="detail-card"><strong>Type</strong><span>${data.type}</span></div>
                <div class="detail-card"><strong>Status</strong><span>${data.status}</span></div>
                <div class="detail-card"><strong>Quantity</strong><span>${data.quantity || 1}</span></div>
                <div class="detail-card"><strong>Amount</strong><span>${formatTransactionAmount(data.amount)}</span></div>
                <div class="detail-card"><strong>Customer</strong><span>${data.customer_name || "Not stored"}</span></div>
                <div class="detail-card"><strong>Created at</strong><span>${data.created_at}</span></div>
            </div>
            <div class="detail-attachments">
                ${createAttachmentMarkup("Invoice", data.invoice_path)}
                ${createAttachmentMarkup("Proof of payment", data.proof_path)}
            </div>
            ${createAuditMarkup(data.audit_history)}
        `;
    } catch (error) {
        console.error(error);
        detailBody.innerHTML = "<p>Failed to load transaction details.</p>";
    }
}

function closeTransactionDetailModal() {
    if (detailModal) detailModal.hidden = true;
}

function updateEmptyState(message = "No transactions found for this filter.") {
    if (!transactionHistory) return;
    let emptyState = document.getElementById("emptyTransactions");
    if (!emptyState) {
        emptyState = document.createElement("p");
        emptyState.id = "emptyTransactions";
        emptyState.className = "empty-state";
        transactionHistory.appendChild(emptyState);
    }
    emptyState.textContent = message;
}

function getTransactionQuery() {
    const params = new URLSearchParams({ offset: String(transactionOffset), limit: "50" });
    if (transactionFilters.category) params.set("category", transactionFilters.category);
    if (transactionFilters.status) params.set("status", transactionFilters.status);
    return params.toString();
}

async function loadMoreTransactions() {
    if (isLoadingTransactions || !hasMoreTransactions || !transactionHistory) return;

    isLoadingTransactions = true;
    if (transactionLoadIndicator) transactionLoadIndicator.hidden = false;

    try {
        const response = await fetch(`/api/transactions?${getTransactionQuery()}`);
        const data = await response.json();
        if (!response.ok) return;

        document.getElementById("emptyTransactions")?.remove();
        if (transactionOffset === 0 && data.transactions.length === 0) updateEmptyState();

        data.transactions.forEach((transaction) => {
            transactionHistory.appendChild(createTransactionItem(transaction));
        });

        transactionOffset += data.transactions.length;
        hasMoreTransactions = Boolean(data.has_more);
    } catch (error) {
        console.error(error);
    } finally {
        isLoadingTransactions = false;
        if (transactionLoadIndicator) transactionLoadIndicator.hidden = true;
    }
}

function resetTransactions() {
    if (!transactionHistory) return;
    transactionHistory.innerHTML = "";
    transactionOffset = 0;
    hasMoreTransactions = true;
}

categoryFilterSelect?.addEventListener("change", async () => {
    transactionFilters.category = categoryFilterSelect.value || "";
    resetTransactions();
    await loadMoreTransactions();
});

statusFilterSelect?.addEventListener("change", async () => {
    transactionFilters.status = statusFilterSelect.value || "";
    resetTransactions();
    await loadMoreTransactions();
});

detailCloseButton?.addEventListener("click", closeTransactionDetailModal);
detailModal?.addEventListener("click", (event) => {
    if (event.target === detailModal) closeTransactionDetailModal();
});

if (typeof animateCountUps === "function") animateCountUps();

if (transactionScrollSentinel && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) loadMoreTransactions();
        });
    }, { rootMargin: "200px 0px" });

    observer.observe(transactionScrollSentinel);
}
