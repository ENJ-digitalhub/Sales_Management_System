const adminDashboardModals = document.querySelectorAll(".modal");
const adminDashboardButtons = document.querySelectorAll(".actionBtn[data-modal]");
const adminDashboardCloseButtons = document.querySelectorAll(".modal .closeBtn, .modal .iconCloseBtn");

const productCache = new Map();
let editingTransactionId = null;

function formatNaira(value) {
    return `N${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function openDashboardModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = "flex";
}

function closeDashboardModal(modal) {
    if (modal) modal.style.display = "none";
}

function formatPendingDate(value) {
    if (!value) return "Just now";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

async function renderPendingUsers() {
    const list = document.getElementById("pendingUsersList");
    if (!list) return;

    list.innerHTML = `<div class="pending-empty">Loading requests...</div>`;
    const response = await fetch("/api/users/pending");
    const data = await response.json();

    if (!response.ok) {
        list.innerHTML = `<div class="pending-empty">${data.message || "Could not load pending users."}</div>`;
        return;
    }

    const users = data.users || [];
    if (!users.length) {
        list.innerHTML = `<div class="pending-empty">No pending registration requests.</div>`;
        return;
    }

    list.innerHTML = users
        .map(
            (pendingUser) => `
                <article class="pending-user-item" data-user-id="${pendingUser.id}">
                    <div class="pending-user-head">
                        <div class="pending-user-name">${pendingUser.first_name} ${pendingUser.last_name} (@${pendingUser.username})</div>
                        <span class="pending-user-meta">Requested: ${formatPendingDate(pendingUser.created_at)}</span>
                    </div>
                    <div class="pending-user-actions">
                        <button type="button" class="pending-allow" data-action="allow">Allow</button>
                        <button type="button" class="pending-decline" data-action="decline">Decline</button>
                    </div>
                </article>
            `
        )
        .join("");
}

async function handlePendingUserAction(userId, action) {
    const endpoint = action === "allow"
        ? `/api/users/pending/${userId}/allow`
        : `/api/users/pending/${userId}/decline`;
    const response = await fetch(endpoint, { method: "POST" });
    const data = await response.json();
    if (!response.ok) {
        alert(data.message || "Could not update request.");
        return;
    }
    alert(data.message || "Request updated.");
    await renderPendingUsers();
}

function bindModalChrome() {
    adminDashboardButtons.forEach((button) => {
        button.addEventListener("click", () => openDashboardModal(button.dataset.modal));
    });

    adminDashboardCloseButtons.forEach((button) => {
        button.addEventListener("click", () => closeDashboardModal(button.closest(".modal")));
    });

    adminDashboardModals.forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeDashboardModal(modal);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        adminDashboardModals.forEach((modal) => {
            if (modal.style.display === "flex") closeDashboardModal(modal);
        });
    });
}

async function loadProducts() {
    if (productCache.size) return [...productCache.values()];
    const response = await fetch("/api/products");
    if (!response.ok) return [];
    const data = await response.json();
    (data.products || []).forEach((product) => productCache.set(product.name, product));
    return [...productCache.values()];
}

async function populateProductSelects() {
    const products = await loadProducts();
    ["itemSoldQuick", "itemSoldSales", "purchaseProduct", "priceProduct"].forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        const selectedValue = select.value;
        select.innerHTML = "";

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select a product";
        placeholder.disabled = true;
        placeholder.selected = !selectedValue;
        select.appendChild(placeholder);

        products.forEach((product) => {
            const option = document.createElement("option");
            option.value = product.name;
            option.textContent = product.name;
            option.selected = product.name === selectedValue;
            select.appendChild(option);
        });
    });
}

function bindQuantitySync(modalSelector, callback) {
    const qtyRange = document.querySelector(`${modalSelector} .qtyrange`);
    const qtyBox = document.querySelector(`${modalSelector} .qtybox`);
    if (!qtyRange || !qtyBox || qtyRange.dataset.bound === "true") return;

    qtyRange.addEventListener("input", () => {
        qtyBox.value = qtyRange.value;
        callback?.();
    });
    qtyBox.addEventListener("input", () => {
        qtyRange.value = qtyBox.value;
        callback?.();
    });
    qtyRange.dataset.bound = "true";
}

function updateEstimate(modalSelector, selectId, estimateId, unitPriceId) {
    const select = document.getElementById(selectId);
    const qtyBox = document.querySelector(`${modalSelector} .qtybox`);
    const estimate = document.getElementById(estimateId);
    const unitPrice = unitPriceId ? document.getElementById(unitPriceId) : null;
    const product = productCache.get(select?.value);
    if (!select || !qtyBox || !estimate) return;

    const quantity = Math.max(Number(qtyBox.value || 0), 0);
    const price = Number(product?.price || 0);
    const total = quantity * price;
    estimate.textContent = `Estimated total: ${formatNaira(total)}`;
    if (unitPrice) unitPrice.textContent = formatNaira(price);
    if (estimateId === "salesTotalPrice") {
        const totalPrice = document.getElementById("salesTotalPrice");
        if (totalPrice) totalPrice.textContent = formatNaira(total);
    }

    const qtyRange = document.querySelector(`${modalSelector} .qtyrange`);
    const maxQuantity = modalSelector === "#purchase" ? 10000 : Math.max(product?.quantity || 1, 1);
    if (qtyRange) qtyRange.max = String(maxQuantity);
    if (qtyBox) qtyBox.max = String(maxQuantity);
}

function refreshCustomerPreview(inputId, hideNameId, unpaidId, previewId) {
    const input = document.getElementById(inputId);
    const hideName = document.getElementById(hideNameId);
    const preview = document.getElementById(previewId);
    if (!input || !preview) return;

    const hidden = hideName?.checked || !input.value.trim();
    preview.hidden = hidden;
    preview.textContent = hidden ? "" : `Customer: ${input.value.trim()}`;
}

function enforceUnpaidCustomerRule(customerId, hideNameId, unpaidId, previewId) {
    const hideName = document.getElementById(hideNameId);
    const unpaid = document.getElementById(unpaidId);
    if (!hideName || !unpaid) return;

    if (unpaid.checked) hideName.checked = false;
    hideName.disabled = unpaid.checked;
    hideName.closest("label")?.classList.toggle("disabled", unpaid.checked);
    refreshCustomerPreview(customerId, hideNameId, unpaidId, previewId);
}

async function uploadAssets(invoiceInputId, proofInputId) {
    const formData = new FormData();
    const invoiceFile = document.getElementById(invoiceInputId)?.files?.[0];
    const proofFile = document.getElementById(proofInputId)?.files?.[0];
    if (invoiceFile) formData.append("invoice", invoiceFile);
    if (proofFile) formData.append("proof", proofFile);
    if (![...formData.keys()].length) return { invoice_path: "", proof_path: "" };

    const response = await fetch("/api/uploads/transaction-assets", { method: "POST", body: formData });
    return response.ok ? response.json() : { invoice_path: "", proof_path: "" };
}

async function prefillFromLastSale(config) {
    const response = await fetch("/api/transactions/last-sale");
    if (!response.ok) return;
    const data = await response.json();

    const select = document.getElementById(config.selectId);
    if (select && data.product_name) select.value = data.product_name;
    const qtyBox = document.querySelector(`${config.modalSelector} .qtybox`);
    const qtyRange = document.querySelector(`${config.modalSelector} .qtyrange`);
    if (qtyBox && data.quantity) qtyBox.value = data.quantity;
    if (qtyRange && data.quantity) qtyRange.value = data.quantity;
    if (config.customerId && data.customer_name) document.getElementById(config.customerId).value = data.customer_name;

    updateEstimate(config.modalSelector, config.selectId, config.estimateId, config.unitPriceId);
    if (config.previewId) {
        refreshCustomerPreview(config.customerId, config.hideNameId, config.unpaidId, config.previewId);
    }
}

async function saveSale(config) {
    const product = document.getElementById(config.selectId)?.value || "";
    const quantity = Number(document.querySelector(`#${config.modalId} .qtybox`)?.value || 0);
    const amount = Number(document.getElementById(config.amountId)?.value || 0);
    const customer = document.getElementById(config.customerId)?.value?.trim() || "";
    const isUnpaid = Boolean(document.getElementById(config.unpaidId)?.checked);
    const hiddenCustomer = Boolean(document.getElementById(config.hideNameId)?.checked);

    if (!product || quantity <= 0 || amount < 0 || (!isUnpaid && amount <= 0)) {
        alert("Please select a product and enter valid quantity and amount.");
        return;
    }
    if (isUnpaid && !customer) {
        alert("Customer name is required for unpaid sales.");
        return;
    }

    const payload = {
        type: "sale",
        product_name: product,
        quantity,
        amount,
        status: isUnpaid ? "unpaid" : "completed",
        customer_name: hiddenCustomer ? "" : customer,
    };

    const isEditing = config.modalId === "sales" && Boolean(editingTransactionId);
    const response = await fetch(isEditing ? `/api/transactions/${editingTransactionId}` : "/api/transactions", {
        method: isEditing ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
        alert(data.message || "Could not save sale.");
        return;
    }

    editingTransactionId = null;
    alert(data.message || "Sale saved successfully.");
    closeDashboardModal(document.getElementById(config.modalId));
    window.location.reload();
}

async function savePurchase() {
    const product = document.getElementById("purchaseProduct")?.value || "";
    const supplier = document.getElementById("purchaseSupplier")?.value?.trim() || "";
    const quantity = Number(document.querySelector("#purchase .qtybox")?.value || 0);
    const amount = Number(document.getElementById("purchasePrice")?.value || 0);
    if (!product || quantity <= 0 || amount <= 0) {
        alert("Please provide valid purchase details.");
        return;
    }

    const assets = await uploadAssets("purchaseInvoiceFile", "purchaseProofFile");
    const response = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            type: "purchase",
            product_name: product,
            quantity,
            amount,
            status: "completed",
            customer_name: supplier,
            invoice_path: assets.invoice_path || "",
            proof_path: assets.proof_path || "",
        }),
    });
    const data = await response.json();
    if (!response.ok) {
        alert(data.message || "Could not save purchase.");
        return;
    }

    alert(data.message || "Purchase saved successfully.");
    closeDashboardModal(document.getElementById("purchase"));
    window.location.reload();
}

async function populateDeleteModal() {
    const response = await fetch("/api/transactions/last-sale-today");
    if (!response.ok) return false;
    const data = await response.json();
    const summary = document.querySelector("#cancel .warning_summary");
    if (summary) {
        summary.innerHTML = `
            <div class="warning_row"><span>Inventory No</span><strong>${data.id}</strong></div>
            <div class="warning_row"><span>Item</span><strong>${data.product_name}</strong></div>
            <div class="warning_row"><span>Quantity</span><strong>${data.quantity || 1}</strong></div>
            <div class="warning_row"><span>Amount</span><strong>${formatNaira(data.amount)}</strong></div>
        `;
    }
    document.querySelector("#cancel .dangerBtn")?.setAttribute("data-transaction-id", data.id);
    document.querySelector("#cancel .editBtn")?.setAttribute("data-transaction-id", data.id);
    return true;
}

function bindAdminActions() {
    bindQuantitySync("#quickSales", () => updateEstimate("#quickSales", "itemSoldQuick", "quickSalesEstimate"));
    bindQuantitySync("#sales", () => updateEstimate("#sales", "itemSoldSales", "salesTotalPrice", "salesUnitPrice"));
    bindQuantitySync("#purchase", () => updateEstimate("#purchase", "purchaseProduct", "purchaseEstimate"));

    document.querySelector("button[data-modal='quickSales']")?.addEventListener("click", async () => {
        await populateProductSelects();
        await prefillFromLastSale({
            modalSelector: "#quickSales",
            selectId: "itemSoldQuick",
            customerId: "quickSalesCustomer",
            hideNameId: "quickSalesDontSave",
            unpaidId: "notPaidQuick",
            estimateId: "quickSalesEstimate",
            previewId: "quickCustomerPreview",
        });
    });

    document.querySelector("button[data-modal='sales']")?.addEventListener("click", async () => {
        await populateProductSelects();
        if (!editingTransactionId) {
            await prefillFromLastSale({
                modalSelector: "#sales",
                selectId: "itemSoldSales",
                customerId: "salesCustomer",
                hideNameId: "salesDontSave",
                unpaidId: "notPaidSales",
                estimateId: "salesTotalPrice",
                unitPriceId: "salesUnitPrice",
                previewId: "salesCustomerPreview",
            });
        }
    });

    document.querySelector("button[data-modal='purchase']")?.addEventListener("click", populateProductSelects);

    [["itemSoldQuick", "#quickSales", "quickSalesEstimate", null], ["itemSoldSales", "#sales", "salesTotalPrice", "salesUnitPrice"], ["purchaseProduct", "#purchase", "purchaseEstimate", null]].forEach(([selectId, modalSelector, estimateId, unitPriceId]) => {
        document.getElementById(selectId)?.addEventListener("change", () => {
            updateEstimate(modalSelector, selectId, estimateId, unitPriceId);
        });
    });

    [["quickSalesCustomer", "quickSalesDontSave", "notPaidQuick", "quickCustomerPreview"], ["salesCustomer", "salesDontSave", "notPaidSales", "salesCustomerPreview"]].forEach(([inputId, hideNameId, unpaidId, previewId]) => {
        document.getElementById(inputId)?.addEventListener("input", () => refreshCustomerPreview(inputId, hideNameId, unpaidId, previewId));
        document.getElementById(hideNameId)?.addEventListener("change", () => refreshCustomerPreview(inputId, hideNameId, unpaidId, previewId));
        document.getElementById(unpaidId)?.addEventListener("change", () => enforceUnpaidCustomerRule(inputId, hideNameId, unpaidId, previewId));
        enforceUnpaidCustomerRule(inputId, hideNameId, unpaidId, previewId);
    });

    const quickAmount = document.querySelector("#quickSales .amtbox");
    if (quickAmount) quickAmount.id = "quickSalesAmount";
    const salesAmount = document.querySelector("#sales .amtbox");
    if (salesAmount) salesAmount.id = "salesAmount";

    document.querySelector("#quickSales .submitBtn")?.addEventListener("click", () => saveSale({
        modalId: "quickSales",
        selectId: "itemSoldQuick",
        amountId: "quickSalesAmount",
        customerId: "quickSalesCustomer",
        hideNameId: "quickSalesDontSave",
        unpaidId: "notPaidQuick",
    }));

    document.querySelector("#sales .submitBtn")?.addEventListener("click", () => saveSale({
        modalId: "sales",
        selectId: "itemSoldSales",
        amountId: "salesAmount",
        customerId: "salesCustomer",
        hideNameId: "salesDontSave",
        unpaidId: "notPaidSales",
    }));

    document.querySelector("#purchase .submitBtn")?.addEventListener("click", savePurchase);

    document.querySelector("button[data-modal='cancel']")?.addEventListener("click", async () => {
        const hasTransaction = await populateDeleteModal();
        if (!hasTransaction) alert("No sale from today.");
    });

    document.querySelector("#cancel .dangerBtn")?.addEventListener("click", async (event) => {
        const transactionId = event.currentTarget.dataset.transactionId;
        if (!transactionId) return;
        const response = await fetch(`/api/transactions/${transactionId}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok) {
            alert(data.message || "Could not delete transaction.");
            return;
        }
        alert(data.message || "Transaction deleted successfully.");
        window.location.reload();
    });

    document.querySelector("#cancel .editBtn")?.addEventListener("click", async (event) => {
        const transactionId = event.currentTarget.dataset.transactionId;
        if (!transactionId) return;
        const response = await fetch(`/api/transactions/${transactionId}`);
        const data = await response.json();
        if (!response.ok) {
            alert(data.message || "Could not load transaction.");
            return;
        }

        editingTransactionId = transactionId;
        await populateProductSelects();
        closeDashboardModal(document.getElementById("cancel"));
        openDashboardModal("sales");
        document.getElementById("itemSoldSales").value = data.product_name || "";
        document.querySelector("#sales .qtybox").value = data.quantity || 1;
        document.querySelector("#sales .qtyrange").value = data.quantity || 1;
        document.getElementById("salesAmount").value = data.amount || "";
        document.getElementById("salesCustomer").value = data.customer_name || "";
        document.getElementById("notPaidSales").checked = data.status === "unpaid";
        updateEstimate("#sales", "itemSoldSales", "salesTotalPrice", "salesUnitPrice");
        refreshCustomerPreview("salesCustomer", "salesDontSave", "notPaidSales", "salesCustomerPreview");
    });

    document.querySelector("button[data-modal='user']")?.addEventListener("click", async () => {
        try {
            await renderPendingUsers();
        } catch (error) {
            console.error(error);
        }
    });

    document.getElementById("pendingUsersList")?.addEventListener("click", async (event) => {
        const actionButton = event.target.closest("button[data-action]");
        if (!actionButton) return;
        const userCard = actionButton.closest(".pending-user-item");
        const userId = userCard?.dataset?.userId;
        if (!userId) return;

        try {
            actionButton.disabled = true;
            await handlePendingUserAction(userId, actionButton.dataset.action);
        } catch (error) {
            console.error(error);
            alert("Something went wrong while updating the request.");
        } finally {
            actionButton.disabled = false;
        }
    });
}

if (typeof animateCountUps === "function") animateCountUps();
bindModalChrome();
populateProductSelects();
bindAdminActions();
