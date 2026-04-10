const employeeModals = document.querySelectorAll(".employee-page .modal");
const employeeActionButtons = document.querySelectorAll(".employeeActionBtn[data-modal]");
const employeeCloseButtons = document.querySelectorAll(".employee-page .modal .closeBtn, .employee-page .modal .iconCloseBtn");

const employeeProducts = new Map();

function formatNaira(value) {
    return `N${Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function openEmployeeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = "flex";
}

function closeEmployeeModal(modal) {
    if (modal) modal.style.display = "none";
}

function bindEmployeeChrome() {
    employeeActionButtons.forEach((button) => {
        button.addEventListener("click", () => openEmployeeModal(button.dataset.modal));
    });

    employeeCloseButtons.forEach((button) => {
        button.addEventListener("click", () => closeEmployeeModal(button.closest(".modal")));
    });

    employeeModals.forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) closeEmployeeModal(modal);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        employeeModals.forEach((modal) => {
            if (modal.style.display === "flex") closeEmployeeModal(modal);
        });
    });
}

async function loadEmployeeProducts() {
    if (employeeProducts.size) return [...employeeProducts.values()];
    const response = await fetch("/api/products");
    if (!response.ok) return [];
    const data = await response.json();
    (data.products || []).forEach((product) => employeeProducts.set(product.name, product));
    return [...employeeProducts.values()];
}

async function populateEmployeeProductSelects() {
    const products = await loadEmployeeProducts();
    ["employeeQuickItem", "employeeSaleItem", "employeePurchaseProduct"].forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        const currentValue = select.value;
        select.innerHTML = "";

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select a product";
        placeholder.disabled = true;
        placeholder.selected = !currentValue;
        select.appendChild(placeholder);

        products.forEach((product) => {
            const option = document.createElement("option");
            option.value = product.name;
            option.textContent = product.name;
            option.selected = product.name === currentValue;
            select.appendChild(option);
        });
    });
}

function bindEmployeeQty(modalSelector, callback) {
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

function updateEmployeeEstimate(modalSelector, selectId, estimateId) {
    const select = document.getElementById(selectId);
    const qtyBox = document.querySelector(`${modalSelector} .qtybox`);
    const estimate = document.getElementById(estimateId);
    const product = employeeProducts.get(select?.value);
    if (!select || !qtyBox || !estimate) return;

    const quantity = Number(qtyBox.value || 0);
    const price = modalSelector === "#employeePurchase"
        ? Number(document.getElementById("employeePurchasePrice")?.value || 0)
        : Number(product?.price || 0);
    const total = quantity * price;
    estimate.textContent = `Estimated total: ${formatNaira(total)}`;

    const qtyRange = document.querySelector(`${modalSelector} .qtyrange`);
    const maxQuantity = modalSelector === "#employeePurchase" ? 10000 : Math.max(product?.quantity || 1, 1);
    if (qtyRange) qtyRange.max = String(maxQuantity);
    if (qtyBox) qtyBox.max = String(maxQuantity);
}

function refreshEmployeeCustomer(inputId, hideNameId, unpaidId, previewId) {
    const input = document.getElementById(inputId);
    const hideName = document.getElementById(hideNameId);
    const preview = document.getElementById(previewId);
    if (!input || !preview) return;

    const hidden = hideName?.checked || !input.value.trim();
    preview.hidden = hidden;
    preview.textContent = hidden ? "" : `Customer: ${input.value.trim()}`;
}

function enforceEmployeeUnpaidCustomerRule(customerId, hideNameId, unpaidId, previewId) {
    const hideName = document.getElementById(hideNameId);
    const unpaid = document.getElementById(unpaidId);
    if (!hideName || !unpaid) return;

    if (unpaid.checked) hideName.checked = false;
    hideName.disabled = unpaid.checked;
    hideName.closest("label")?.classList.toggle("disabled", unpaid.checked);
    refreshEmployeeCustomer(customerId, hideNameId, unpaidId, previewId);
}

async function uploadEmployeeAssets(invoiceInputId, proofInputId) {
    const formData = new FormData();
    const invoiceFile = document.getElementById(invoiceInputId)?.files?.[0];
    const proofFile = document.getElementById(proofInputId)?.files?.[0];
    if (invoiceFile) formData.append("invoice", invoiceFile);
    if (proofFile) formData.append("proof", proofFile);
    if (![...formData.keys()].length) return { invoice_path: "", proof_path: "" };

    const response = await fetch("/api/uploads/transaction-assets", { method: "POST", body: formData });
    return response.ok ? response.json() : { invoice_path: "", proof_path: "" };
}

async function fillEmployeeLastSale(config) {
    const response = await fetch("/api/transactions/last-sale");
    if (!response.ok) return;
    const data = await response.json();
    if (data.product_name) document.getElementById(config.selectId).value = data.product_name;
    const qtyBox = document.querySelector(`${config.modalSelector} .qtybox`);
    const qtyRange = document.querySelector(`${config.modalSelector} .qtyrange`);
    if (qtyBox && data.quantity) qtyBox.value = data.quantity;
    if (qtyRange && data.quantity) qtyRange.value = data.quantity;
    if (config.customerId && data.customer_name) document.getElementById(config.customerId).value = data.customer_name;
    if (config.amountId && data.amount) document.getElementById(config.amountId).value = data.amount;
    updateEmployeeEstimate(config.modalSelector, config.selectId, config.estimateId);
    if (config.previewId) refreshEmployeeCustomer(config.customerId, config.hideNameId, config.unpaidId, config.previewId);
}

async function saveEmployeeSale(config) {
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

    const response = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            type: "sale",
            product_name: product,
            quantity,
            amount,
            status: isUnpaid ? "unpaid" : "completed",
            customer_name: hiddenCustomer ? "" : customer,
        }),
    });
    const data = await response.json();
    if (!response.ok) {
        alert(data.message || "Could not save sale.");
        return;
    }

    alert(data.message || "Sale saved successfully.");
    closeEmployeeModal(document.getElementById(config.modalId));
    window.location.reload();
}

async function saveEmployeePurchase() {
    const product = document.getElementById("employeePurchaseProduct")?.value || "";
    const supplier = document.getElementById("employeePurchaseSupplier")?.value?.trim() || "";
    const quantity = Number(document.getElementById("employeePurchaseQty")?.value || 0);
    const amount = Number(document.getElementById("employeePurchasePrice")?.value || 0);
    if (!product || quantity <= 0 || amount <= 0) {
        alert("Please provide valid purchase details.");
        return;
    }

    const assets = await uploadEmployeeAssets("employeePurchaseInvoice", "employeePurchaseProof");
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
    closeEmployeeModal(document.getElementById("employeePurchase"));
    window.location.reload();
}

async function populateEmployeeCancelModal() {
    const response = await fetch("/api/transactions/last-sale-today");
    if (!response.ok) return false;
    const data = await response.json();
    const summary = document.querySelector("#employeeCancelSale .warning_summary");
    if (summary) {
        summary.innerHTML = `
            <div class="warning_row"><span>Item</span><strong>${data.product_name}</strong></div>
            <div class="warning_row"><span>Quantity</span><strong>${data.quantity || 1}</strong></div>
            <div class="warning_row"><span>Amount</span><strong>${formatNaira(data.amount)}</strong></div>
        `;
    }
    document.querySelector("#employeeCancelSale .dangerBtn")?.setAttribute("data-transaction-id", data.id);
    return true;
}

function bindEmployeeActions() {
    bindEmployeeQty("#employeeQuickSale", () => updateEmployeeEstimate("#employeeQuickSale", "employeeQuickItem", "employeeQuickEstimate"));
    bindEmployeeQty("#employeeSale", () => updateEmployeeEstimate("#employeeSale", "employeeSaleItem", "employeeSaleEstimate"));
    bindEmployeeQty("#employeePurchase", () => updateEmployeeEstimate("#employeePurchase", "employeePurchaseProduct", "employeePurchaseEstimate"));

    document.querySelector("button[data-modal='employeeQuickSale']")?.addEventListener("click", async () => {
        await populateEmployeeProductSelects();
        await fillEmployeeLastSale({
            modalSelector: "#employeeQuickSale",
            selectId: "employeeQuickItem",
            amountId: "employeeQuickAmount",
            customerId: "employeeQuickCustomer",
            hideNameId: "employeeQuickDontSave",
            unpaidId: "employeeQuickUnpaid",
            estimateId: "employeeQuickEstimate",
            previewId: "employeeQuickCustomerPreview",
        });
    });

    document.querySelector("button[data-modal='employeeSale']")?.addEventListener("click", async () => {
        await populateEmployeeProductSelects();
        await fillEmployeeLastSale({
            modalSelector: "#employeeSale",
            selectId: "employeeSaleItem",
            amountId: "employeeSaleAmount",
            customerId: "employeeSaleCustomer",
            hideNameId: "employeeSaleDontSave",
            unpaidId: "employeeSaleUnpaid",
            estimateId: "employeeSaleEstimate",
            previewId: "employeeSaleCustomerPreview",
        });
    });

    document.querySelector("button[data-modal='employeePurchase']")?.addEventListener("click", async () => {
        await populateEmployeeProductSelects();
        updateEmployeeEstimate("#employeePurchase", "employeePurchaseProduct", "employeePurchaseEstimate");
    });

    [["employeeQuickItem", "#employeeQuickSale", "employeeQuickEstimate"], ["employeeSaleItem", "#employeeSale", "employeeSaleEstimate"], ["employeePurchaseProduct", "#employeePurchase", "employeePurchaseEstimate"]].forEach(([selectId, modalSelector, estimateId]) => {
        document.getElementById(selectId)?.addEventListener("change", () => updateEmployeeEstimate(modalSelector, selectId, estimateId));
    });

    document.getElementById("employeePurchasePrice")?.addEventListener("input", () => {
        const estimate = document.getElementById("employeePurchaseEstimate");
        const quantity = Number(document.querySelector("#employeePurchase .qtybox")?.value || 0);
        const amount = Number(document.getElementById("employeePurchasePrice")?.value || 0);
        if (estimate) estimate.textContent = `Estimated total: ${formatNaira(quantity * amount)}`;
    });

    [["employeeQuickCustomer", "employeeQuickDontSave", "employeeQuickUnpaid", "employeeQuickCustomerPreview"], ["employeeSaleCustomer", "employeeSaleDontSave", "employeeSaleUnpaid", "employeeSaleCustomerPreview"]].forEach(([inputId, hideNameId, unpaidId, previewId]) => {
        document.getElementById(inputId)?.addEventListener("input", () => refreshEmployeeCustomer(inputId, hideNameId, unpaidId, previewId));
        document.getElementById(hideNameId)?.addEventListener("change", () => refreshEmployeeCustomer(inputId, hideNameId, unpaidId, previewId));
        document.getElementById(unpaidId)?.addEventListener("change", () => enforceEmployeeUnpaidCustomerRule(inputId, hideNameId, unpaidId, previewId));
        enforceEmployeeUnpaidCustomerRule(inputId, hideNameId, unpaidId, previewId);
    });

    document.querySelector("#employeeQuickSale .submitBtn")?.addEventListener("click", () => saveEmployeeSale({
        modalId: "employeeQuickSale",
        selectId: "employeeQuickItem",
        amountId: "employeeQuickAmount",
        customerId: "employeeQuickCustomer",
        hideNameId: "employeeQuickDontSave",
        unpaidId: "employeeQuickUnpaid",
    }));

    document.querySelector("#employeeSale .submitBtn")?.addEventListener("click", () => saveEmployeeSale({
        modalId: "employeeSale",
        selectId: "employeeSaleItem",
        amountId: "employeeSaleAmount",
        customerId: "employeeSaleCustomer",
        hideNameId: "employeeSaleDontSave",
        unpaidId: "employeeSaleUnpaid",
    }));

    document.querySelector("#employeePurchase .submitBtn")?.addEventListener("click", saveEmployeePurchase);

    document.querySelector("button[data-modal='employeeCancelSale']")?.addEventListener("click", async () => {
        const exists = await populateEmployeeCancelModal();
        if (!exists) alert("No sale from today.");
    });

    document.querySelector("#employeeCancelSale .dangerBtn")?.addEventListener("click", async (event) => {
        const transactionId = event.currentTarget.dataset.transactionId;
        if (!transactionId) return;
        const response = await fetch(`/api/transactions/${transactionId}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok) {
            alert(data.message || "Could not cancel transaction.");
            return;
        }
        alert(data.message || "Transaction cancelled successfully.");
        window.location.reload();
    });
}

if (typeof animateCountUps === "function") animateCountUps();
bindEmployeeChrome();
populateEmployeeProductSelects();
bindEmployeeActions();
