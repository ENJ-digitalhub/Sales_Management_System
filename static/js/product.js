const productPage = document.querySelector(".product-page");
const currentUserRole = productPage?.dataset.userRole || "user";
const isAdmin = currentUserRole === "admin";

const productQuickAction = document.getElementById("productQuickAction");
const productModal = document.getElementById("productModal");
const closeProductModal = document.getElementById("closeProductModal");
const cancelProductModal = document.getElementById("cancelProductModal");
const productForm = document.getElementById("productForm");
const productGrid = document.getElementById("productGrid");
const productStatus = document.getElementById("productStatus");

const productActionModal = document.getElementById("productActionModal");
const closeProductActionModal = document.getElementById("closeProductActionModal");
const cancelProductActionModal = document.getElementById("cancelProductActionModal");
const productActionTitle = document.getElementById("productActionTitle");
const productActionMeta = document.getElementById("productActionMeta");
const productActionSwitcher = document.getElementById("productActionSwitcher");
const actionPanels = document.querySelectorAll("[data-action-content]");
const productAddForm = document.getElementById("productAddForm");
const addQuantity = document.getElementById("addQuantity");
const cancelProductAddModal = document.getElementById("cancelProductAddModal");
const productRemoveForm = document.getElementById("productRemoveForm");
const removeQuantity = document.getElementById("removeQuantity");
const cancelProductRemoveModal = document.getElementById("cancelProductRemoveModal");
const removeReason = document.getElementById("removeReason");
const removeReasonGroup = document.getElementById("removeReasonGroup");

const productEditForm = document.getElementById("productEditForm");
const editProductName = document.getElementById("editProductName");
const editProductPrice = document.getElementById("editProductPrice");
const editProductQuantity = document.getElementById("editProductQuantity");
const cancelProductEditModal = document.getElementById("cancelProductEditModal");
const productDeletePanel = document.getElementById("productDeletePanel");
const cancelProductDelete = document.getElementById("cancelProductDelete");
const confirmProductDelete = document.getElementById("confirmProductDelete");

let selectedProduct = null;

function showProductStatus(message, type = "success") {
    if (!productStatus) {
        return;
    }

    productStatus.textContent = message;
    productStatus.className = `status-banner ${type}`;
    productStatus.hidden = false;
}

function formatPrice(price) {
    return Number(price).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

function getProductFromCard(card) {
    return {
        id: Number(card.dataset.productId),
        name: card.dataset.productName,
        price: Number(card.dataset.productPrice),
        quantity: Number(card.dataset.productQuantity),
        image_url: card.dataset.productImage || "/static/img/logo.png",
    };
}

function updateCardDataset(card, product) {
    card.dataset.productId = product.id;
    card.dataset.productName = product.name;
    card.dataset.productPrice = product.price;
    card.dataset.productQuantity = product.quantity;
    card.dataset.productImage = product.image_url || "/static/img/logo.png";
}

function createProductCard(product) {
    const card = document.createElement("section");
    card.className = "product-card";
    updateCardDataset(card, product);
    card.innerHTML = `
        <img src="${product.image_url || "/static/img/logo.png"}" alt="${product.name} image">
        <div class="name"></div>
        <div class="properties">
            <div class="price"><abbr title="Price"><i class="fa-solid fa-naira-sign"></i><span class="price-value"></span></abbr></div>
            <div class="qty"><abbr title="Quantity"><span class="qty-value"></span></abbr></div>
        </div>
        <div class="card-actions">
            <button class="manageBtn" type="button">Open Actions</button>
        </div>
    `;

    syncProductCard(card, product);
    return card;
}

function syncProductCard(card, product) {
    if (!card) {
        return;
    }

    updateCardDataset(card, product);
    const image = card.querySelector("img");
    if (image) {
        image.src = product.image_url || "/static/img/logo.png";
        image.alt = `${product.name} image`;
    }
    card.querySelector(".name").textContent = product.name;
    card.querySelector(".price-value").textContent = formatPrice(product.price);
    card.querySelector(".qty-value").textContent = product.quantity;
}

function ensureEmptyState() {
    const cards = productGrid?.querySelectorAll(".product-card");
    let emptyState = document.getElementById("emptyProducts");

    if (!productGrid) {
        return;
    }

    if (!cards || cards.length === 0) {
        if (!emptyState) {
            emptyState = document.createElement("div");
            emptyState.id = "emptyProducts";
            emptyState.className = "empty-products";
            emptyState.textContent = "No products added yet.";
            productGrid.appendChild(emptyState);
        }
    } else if (emptyState) {
        emptyState.remove();
    }
}

function hideCreateModal() {
    if (productModal) {
        productModal.hidden = true;
    }
}

function showCreateModal() {
    if (productModal) {
        productModal.hidden = false;
    }
}

function hideActionModal() {
    if (!productActionModal) {
        return;
    }

    productActionModal.hidden = true;
    selectedProduct = null;
    productAddForm?.reset();
    productRemoveForm?.reset();
    productEditForm?.reset();
}

function setActionView(view) {
    if (!productActionSwitcher) {
        return;
    }

    productActionSwitcher.querySelectorAll(".action-pill").forEach((button) => {
        button.classList.toggle("active", button.dataset.actionView === view);
    });

    actionPanels.forEach((panel) => {
        const isActive = panel.dataset.actionContent === view;
        panel.hidden = !isActive;
        panel.classList.toggle("active", isActive);
    });

    if (productAddForm) {
        productAddForm.hidden = view !== "add";
    }

    if (productRemoveForm) {
        productRemoveForm.hidden = view !== "remove";
    }

    if (removeReasonGroup) {
        removeReasonGroup.hidden = view !== "remove";
    }

    if (addQuantity) {
        addQuantity.required = view === "add";
    }

    if (removeQuantity) {
        removeQuantity.required = view === "remove";
    }

    if (removeReason) {
        removeReason.required = view === "remove";
    }

    if (productEditForm) {
        productEditForm.hidden = view !== "edit";
    }

    if (productDeletePanel) {
        productDeletePanel.hidden = view !== "delete";
    }
}

function populateActionModal(product) {
    if (!productActionTitle || !productActionMeta) {
        return;
    }

    productActionTitle.textContent = product.name;
    productActionMeta.textContent = `Price: N${formatPrice(product.price)} | Quantity in stock: ${product.quantity}`;

    if (editProductName) {
        editProductName.value = product.name;
    }
    if (editProductPrice) {
        editProductPrice.value = product.price;
    }
    if (editProductQuantity) {
        editProductQuantity.value = product.quantity;
    }
}

function showActionModal(product) {
    if (!productActionModal) {
        return;
    }

    selectedProduct = product;
    populateActionModal(product);
    productActionModal.hidden = false;
}

function upsertProductCard(product) {
    const existingCard = productGrid?.querySelector(`[data-product-id="${product.id}"]`);
    if (existingCard) {
        syncProductCard(existingCard, product);
    } else if (productGrid) {
        productGrid.prepend(createProductCard(product));
    }

    ensureEmptyState();
}

if (productQuickAction) {
    productQuickAction.addEventListener("click", showCreateModal);
}

if (closeProductModal) {
    closeProductModal.addEventListener("click", hideCreateModal);
}

if (cancelProductModal) {
    cancelProductModal.addEventListener("click", hideCreateModal);
}

if (productModal) {
    productModal.addEventListener("click", (event) => {
        if (event.target === productModal) {
            hideCreateModal();
        }
    });
}

if (closeProductActionModal) {
    closeProductActionModal.addEventListener("click", hideActionModal);
}

if (cancelProductAddModal) {
    cancelProductAddModal.addEventListener("click", hideActionModal);
}

if (cancelProductRemoveModal) {
    cancelProductRemoveModal.addEventListener("click", hideActionModal);
}

if (cancelProductEditModal) {
    cancelProductEditModal.addEventListener("click", hideActionModal);
}

if (cancelProductDelete) {
    cancelProductDelete.addEventListener("click", hideActionModal);
}

if (productActionModal) {
    productActionModal.addEventListener("click", (event) => {
        if (event.target === productActionModal) {
            hideActionModal();
        }
    });
}

if (productActionSwitcher) {
    productActionSwitcher.addEventListener("click", (event) => {
        const trigger = event.target.closest("[data-action-view]");
        if (!trigger) {
            return;
        }

        setActionView(trigger.dataset.actionView);
    });
}

if (productForm) {
    productForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(productForm);

        try {
            const response = await fetch("/api/products", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                showProductStatus(data.message || "Could not save product.", "error");
                return;
            }

            upsertProductCard(data.product);
            productForm.reset();
            hideCreateModal();
            showProductStatus(data.message || "Product saved successfully.");
        } catch (error) {
            console.error(error);
            showProductStatus("Something went wrong while saving the product.", "error");
        }
    });
}

async function submitAdjustForm(action, quantity, reason = "") {
    if (!selectedProduct) {
        return;
    }

    const payload = {
        action,
        quantity,
        reason,
    };

    try {
        const response = await fetch(`/api/products/${selectedProduct.id}/adjust`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
            showProductStatus(data.message || "Could not update this product.", "error");
            return;
        }

        upsertProductCard(data.product);
        populateActionModal(data.product);
        selectedProduct = data.product;
        productAddForm?.reset();
        productRemoveForm?.reset();
        setActionView("add");
        hideActionModal();
        showProductStatus(data.message || "Product updated successfully.");
    } catch (error) {
        console.error(error);
        showProductStatus("Something went wrong while updating the product.", "error");
    }
}

if (productAddForm) {
    productAddForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(productAddForm);
        await submitAdjustForm("add", formData.get("quantity"));
    });
}

if (productRemoveForm) {
    productRemoveForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(productRemoveForm);
        await submitAdjustForm("remove", formData.get("quantity"), formData.get("reason"));
    });
}

if (productEditForm) {
    productEditForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (!selectedProduct || !isAdmin) {
            return;
        }

        const formData = new FormData(productEditForm);
        const payload = {
            name: formData.get("name"),
            price: formData.get("price"),
            quantity: formData.get("quantity"),
        };

        try {
            const response = await fetch(`/api/products/${selectedProduct.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (!response.ok) {
                showProductStatus(data.message || "Could not edit this product.", "error");
                return;
            }

            upsertProductCard(data.product);
            selectedProduct = data.product;
            populateActionModal(data.product);
            hideActionModal();
            showProductStatus(data.message || "Product updated successfully.");
        } catch (error) {
            console.error(error);
            showProductStatus("Something went wrong while editing the product.", "error");
        }
    });
}

if (confirmProductDelete) {
    confirmProductDelete.addEventListener("click", async () => {
        if (!selectedProduct || !isAdmin) {
            return;
        }

        try {
            const response = await fetch(`/api/products/${selectedProduct.id}`, {
                method: "DELETE",
            });

            const data = await response.json();
            if (!response.ok) {
                showProductStatus(data.message || "Could not delete this product.", "error");
                return;
            }

            productGrid?.querySelector(`[data-product-id="${selectedProduct.id}"]`)?.remove();
            ensureEmptyState();
            hideActionModal();
            showProductStatus(data.message || "Product deleted successfully.");
        } catch (error) {
            console.error(error);
            showProductStatus("Something went wrong while deleting the product.", "error");
        }
    });
}

if (productGrid) {
    productGrid.addEventListener("click", (event) => {
        const card = event.target.closest(".product-card");
        if (!card || !productGrid.contains(card)) {
            return;
        }

        const product = getProductFromCard(card);
        if (event.target.classList.contains("manageBtn")) {
            showActionModal(product);
            setActionView("add");
        }
    });
}

ensureEmptyState();
