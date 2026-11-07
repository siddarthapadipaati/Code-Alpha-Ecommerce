
// ==========================================
// ShopEase - Django Shopping Cart
// ==========================================

let cart = [];

// ==========================================
// HTML ELEMENTS
// ==========================================

const productCards = document.querySelectorAll(".product-card");

const cartButton = document.getElementById("cartButton");
const cartOverlay = document.getElementById("cartOverlay");
const closeCart = document.getElementById("closeCart");

const cartItems = document.getElementById("cartItems");
const cartCount = document.getElementById("cartCount");
const cartTotal = document.getElementById("cartTotal");

const checkoutBtn = document.getElementById("checkoutBtn");


// ==========================================
// CSRF TOKEN
// ==========================================

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie) {
        const cookies = document.cookie.split(";");

        cookies.forEach(cookie => {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        });
    }

    return cookieValue;
}


// ==========================================
// DJANGO API REQUEST
// ==========================================

async function cartRequest(url, options = {}) {

    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            ...(options.headers || {})
        }
    });

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error("Invalid server response. Please refresh the page.");
    }

    if (!response.ok) {
        throw new Error(data.message || "Something went wrong.");
    }

    return data;
}


// ==========================================
// UPDATE CART DISPLAY
// ==========================================

function updateCartDisplay(data) {

    cart = data.items || [];

    // Update cart count if available
    if (cartCount) {
        cartCount.textContent = data.cart_count || 0;
    }

    // Update cart total if available
    if (cartTotal) {
        cartTotal.textContent = Number(
            data.total || 0
        ).toLocaleString("en-IN");
    }

    // Stop if this page does not contain the cart panel
    if (!cartItems) {
        return;
    }

    cartItems.innerHTML = "";

    if (cart.length === 0) {
        cartItems.textContent = "Your cart is empty.";
        return;
    }

    cart.forEach(item => {

        const itemElement = document.createElement("div");
        itemElement.className = "cart-item";

        // Product details
        const details = document.createElement("div");

        const heading = document.createElement("h4");
        heading.textContent = item.name;

        const price = document.createElement("p");
        price.textContent =
            `₹${item.price.toLocaleString("en-IN")} each`;

        const subtotal = document.createElement("p");
        subtotal.textContent =
            `Subtotal: ₹${item.subtotal.toLocaleString("en-IN")}`;

        // Quantity controls
        const controls = document.createElement("div");
        controls.className = "quantity-controls";

        const decrease = document.createElement("button");
        decrease.textContent = "−";

        decrease.addEventListener("click", () => {
            changeQuantity(item.id, item.quantity - 1);
        });

        const quantity = document.createElement("span");
        quantity.textContent = item.quantity;

        const increase = document.createElement("button");
        increase.textContent = "+";
        increase.disabled = item.quantity >= item.stock;

        increase.addEventListener("click", () => {
            changeQuantity(item.id, item.quantity + 1);
        });

        controls.append(decrease, quantity, increase);

        details.append(
            heading,
            price,
            subtotal,
            controls
        );

        // Remove button
        const remove = document.createElement("button");
        remove.className = "remove-btn";
        remove.textContent = "Remove";

        remove.addEventListener("click", () => {
            removeProduct(item.id);
        });

        itemElement.append(details, remove);
        cartItems.appendChild(itemElement);
    });
}


// ==========================================
// LOAD CART FROM DJANGO SESSION
// ==========================================

async function loadCart() {

    try {
        const data = await cartRequest("/cart/");
        updateCartDisplay(data);

    } catch (error) {
        console.error("Cart loading error:", error);
    }
}


// ==========================================
// ADD PRODUCT TO CART
// ==========================================

async function addProductToCart(productId, button) {

    if (!productId || !button) {
        return;
    }

    const originalText = button.textContent;

    try {

        button.disabled = true;
        button.textContent = "Adding...";

        const data = await cartRequest(
            `/cart/add/${productId}/`,
            {
                method: "POST"
            }
        );

        updateCartDisplay(data);

        button.textContent = "Added ✓";

        // Refresh cart panel if available
        if (cartOverlay && cartOverlay.classList.contains("show")) {
            await loadCart();
        }

        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 1000);

    } catch (error) {

        alert(error.message);

        button.textContent = originalText;
        button.disabled = false;
    }
}


// ==========================================
// HOMEPAGE ADD TO CART BUTTONS
// ==========================================

productCards.forEach(card => {

    const addButton = card.querySelector(".add-btn");

    if (!addButton || addButton.disabled) {
        return;
    }

    addButton.addEventListener("click", () => {

        const productId = card.dataset.productId;

        addProductToCart(productId, addButton);

    });
});


// ==========================================
// PRODUCT DETAILS PAGE ADD TO CART
// ==========================================

const detailAddButton = document.querySelector(".detail-add-btn");

if (detailAddButton && !detailAddButton.disabled) {

    detailAddButton.addEventListener("click", () => {

        const productId = detailAddButton.dataset.productId;

        addProductToCart(productId, detailAddButton);

    });
}


// ==========================================
// CHANGE PRODUCT QUANTITY
// ==========================================

async function changeQuantity(productId, quantity) {

    try {

        const body = new URLSearchParams();
        body.append("quantity", quantity);

        const data = await cartRequest(
            `/cart/update/${productId}/`,
            {
                method: "POST",
                body: body
            }
        );

        updateCartDisplay(data);

    } catch (error) {

        alert(error.message);
    }
}


// ==========================================
// REMOVE PRODUCT
// ==========================================

async function removeProduct(productId) {

    try {

        const data = await cartRequest(
            `/cart/remove/${productId}/`,
            {
                method: "POST"
            }
        );

        updateCartDisplay(data);

    } catch (error) {

        alert(error.message);
    }
}


// ==========================================
// OPEN CART
// ==========================================

if (cartButton && cartOverlay) {

    cartButton.addEventListener("click", () => {

        cartOverlay.classList.add("show");
        loadCart();

    });
}


// ==========================================
// CLOSE CART
// ==========================================

if (closeCart && cartOverlay) {

    closeCart.addEventListener("click", () => {

        cartOverlay.classList.remove("show");

    });
}


// Close cart by clicking outside the panel
if (cartOverlay) {

    cartOverlay.addEventListener("click", event => {

        if (event.target === cartOverlay) {
            cartOverlay.classList.remove("show");
        }

    });
}


// ==========================================
// CHECKOUT
// ==========================================

if (checkoutBtn) {

    checkoutBtn.addEventListener("click", () => {

        if (cart.length === 0) {

            alert("Your shopping cart is empty!");
            return;

        }

        window.location.href = "/checkout/";

    });
}


// ==========================================
// INITIALIZE CART
// ==========================================

if (cartCount || cartItems || cartButton) {
    loadCart();
}


// ==========================================
// END OF SHOPEASE JAVASCRIPT
// ==========================================
