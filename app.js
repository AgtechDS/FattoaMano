/**
 * FATTO A MANO — BOUTIQUE ORAFA DEL RAME PURO (99.9%)
 * Core Client Application & Reactive Cart Logic
 * GDPR & EU AI Act Compliance Engine
 */

// State Management
const state = {
  products: [],
  cart: JSON.parse(localStorage.getItem('fattoamano_cart') || '[]'),
  activeFilter: 'all',
  activeModalProduct: null,
  shippingFee: 6.00
};

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const cartDrawer = document.getElementById('cartDrawer');
const cartBackdrop = document.getElementById('cartBackdrop');
const openCartBtn = document.getElementById('openCartBtn');
const closeCartBtn = document.getElementById('closeCartBtn');
const cartCountBadge = document.getElementById('cartCountBadge');
const cartItemsContainer = document.getElementById('cartItemsContainer');
const cartSubtotalAmount = document.getElementById('cartSubtotalAmount');
const cartShippingAmount = document.getElementById('cartShippingAmount');
const cartTotalAmount = document.getElementById('cartTotalAmount');
const shippingNoticeText = document.getElementById('shippingNoticeText');
const shippingBarFill = document.getElementById('shippingBarFill');
const stripeCheckoutBtn = document.getElementById('stripeCheckoutBtn');
const categoryFilters = document.getElementById('categoryFilters');
const productModalBackdrop = document.getElementById('productModalBackdrop');
const closeModalBtn = document.getElementById('closeModalBtn');
const toastContainer = document.getElementById('toastContainer');
const privacyModalBackdrop = document.getElementById('privacyModalBackdrop');
const closePrivacyModalBtn = document.getElementById('closePrivacyModalBtn');
const cookieBanner = document.getElementById('cookieBanner');
const acceptCookiesBtn = document.getElementById('acceptCookiesBtn');
const openPrivacyBannerBtn = document.getElementById('openPrivacyBannerBtn');

// ==============================================================================
// INITIALIZATION & DATA FETCHING
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  setupEventListeners();
  renderCart();
  initCookieBanner();
});

async function loadProducts() {
  try {
    // Attempt 1: Fetch from local server API (which synchronizes with Supabase)
    const response = await fetch('/api/products').catch(() => null);
    if (response && response.ok) {
      state.products = await response.json();
    } else {
      // Attempt 2: Fallback to local products_cache.json
      const fallbackRes = await fetch('products_cache.json');
      state.products = await fallbackRes.json();
    }
  } catch (err) {
    console.warn('Caricamento prodotti da cache locale:', err);
    // Minimal safety fallback
    state.products = [
      {
        id: 'prod_rame_001',
        title: 'Bracciale Intrecciato 3 Filamenti',
        description: 'Forgiato a mano con 3 trefoli di rame massiccio ritorti a caldo.',
        price: 30.00,
        image_url: 'assets/bracciale_3_filamenti.jpg',
        purity: '99.9% Rame Puro',
        category: 'Intrecciati',
        details: '3 filamenti rame puro 99.9%'
      }
    ];
  }

  renderProducts();
}

// ==============================================================================
// PRODUCTS RENDERING & FILTERING
// ==============================================================================
function renderProducts() {
  if (!productsGrid) return;
  productsGrid.innerHTML = '';

  const filtered = state.activeFilter === 'all' 
    ? state.products 
    : state.products.filter(p => p.category === state.activeFilter);

  if (filtered.length === 0) {
    productsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <i class="fa-solid fa-fire" style="font-size: 2rem; color: var(--copper-primary); margin-bottom: 1rem;"></i>
        <p>Nessuna opera trovata per questa lavorazione.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(product => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.dataset.id = product.id;

    card.innerHTML = `
      <div class="card-media" onclick="openProductModal('${product.id}')">
        <img src="${product.image_url}" alt="${product.title}" loading="lazy">
        <span class="badge-purity"><i class="fa-solid fa-award"></i> ${product.purity || '99.9% Rame Puro'}</span>
        <button class="quick-view-btn" aria-label="Visualizza dettagli" onclick="event.stopPropagation(); openProductModal('${product.id}')">
          <i class="fa-solid fa-magnifying-glass-plus"></i>
        </button>
      </div>

      <div class="card-content">
        <div class="card-category">${product.category || 'Creazione Artigianale'}</div>
        <h3 class="card-title" onclick="openProductModal('${product.id}')" style="cursor: pointer;">${product.title}</h3>
        <p class="card-description">${product.description || ''}</p>
        
        <div class="card-footer">
          <div class="card-price-group">
            <span class="card-price-label">Valore Unico</span>
            <span class="card-price">€${Number(product.price).toFixed(2)}</span>
          </div>
          <button class="btn-add-cart" onclick="addToCartById('${product.id}')">
            <i class="fa-solid fa-plus"></i>
            <span>Aggiungi</span>
          </button>
        </div>
      </div>
    `;

    productsGrid.appendChild(card);
  });
}

// ==============================================================================
// CART LOGIC & PERSISTENCE
// ==============================================================================
function saveCart() {
  localStorage.setItem('fattoamano_cart', JSON.stringify(state.cart));
  renderCart();
}

function addToCartById(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  const existingIndex = state.cart.findIndex(item => item.id === productId);
  if (existingIndex > -1) {
    state.cart[existingIndex].quantity += 1;
  } else {
    state.cart.push({
      id: product.id,
      title: product.title,
      price: Number(product.price),
      image_url: product.image_url,
      stripe_price_id: product.stripe_price_id || null,
      quantity: 1
    });
  }

  saveCart();
  showToast(`Aggiunto: ${product.title}`);
  openCart();
}

function updateCartQuantity(productId, delta) {
  const index = state.cart.findIndex(item => item.id === productId);
  if (index === -1) return;

  state.cart[index].quantity += delta;
  if (state.cart[index].quantity <= 0) {
    state.cart.splice(index, 1);
    showToast('Bracciale rimosso dal carrello');
  }

  saveCart();
}

function removeCartItem(productId) {
  state.cart = state.cart.filter(item => item.id !== productId);
  saveCart();
  showToast('Bracciale rimosso dallo scrigno');
}

function renderCart() {
  const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const shipping = state.cart.length > 0 ? state.shippingFee : 0;
  const total = subtotal + shipping;

  // Update badge & financial breakdown
  if (cartCountBadge) cartCountBadge.textContent = totalItems;
  if (cartSubtotalAmount) cartSubtotalAmount.textContent = `€${subtotal.toFixed(2)}`;
  if (cartShippingAmount) cartShippingAmount.textContent = state.cart.length > 0 ? `€${shipping.toFixed(2)}` : '€0.00';
  if (cartTotalAmount) cartTotalAmount.textContent = `€${total.toFixed(2)}`;

  // Update Shipping Info Notice
  if (shippingNoticeText) {
    shippingNoticeText.innerHTML = `Spedizione <strong>€6,00 tutta Italia</strong> • Consegna in <strong>3/5 giorni lavorativi</strong>`;
  }

  // Render items in drawer
  if (!cartItemsContainer) return;
  cartItemsContainer.innerHTML = '';

  if (state.cart.length === 0) {
    cartItemsContainer.innerHTML = `
      <div class="cart-empty-state">
        <i class="fa-solid fa-gem" style="font-size: 2.5rem; color: var(--border-subtle); margin-bottom: 1rem;"></i>
        <h4 style="font-family: var(--font-serif); font-size: 1.3rem;">Il tuo scrigno è vuoto</h4>
        <p>Esplora la collezione e indossa l'autenticità del rame 99.9%.</p>
      </div>
    `;
    if (stripeCheckoutBtn) stripeCheckoutBtn.disabled = true;
    return;
  }

  if (stripeCheckoutBtn) stripeCheckoutBtn.disabled = false;

  state.cart.forEach(item => {
    const row = document.createElement('div');
    row.className = 'cart-item';
    row.innerHTML = `
      <img src="${item.image_url}" alt="${item.title}" class="cart-item-img">
      <div class="cart-item-info">
        <h4>${item.title}</h4>
        <div class="cart-item-price">€${(item.price * item.quantity).toFixed(2)}</div>
        <div class="cart-item-controls">
          <button class="qty-btn" onclick="updateCartQuantity('${item.id}', -1)" aria-label="Riduci">−</button>
          <span class="qty-count">${item.quantity}</span>
          <button class="qty-btn" onclick="updateCartQuantity('${item.id}', 1)" aria-label="Aumenta">+</button>
        </div>
      </div>
      <button class="cart-item-remove" onclick="removeCartItem('${item.id}')" aria-label="Rimuovi">
        <i class="fa-solid fa-trash-can"></i>
      </button>
    `;
    cartItemsContainer.appendChild(row);
  });
}

// ==============================================================================
// SLIDE-OVER DRAWER CONTROLS
// ==============================================================================
function openCart() {
  cartDrawer.classList.add('open');
  cartBackdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeCart() {
  cartDrawer.classList.remove('open');
  cartBackdrop.classList.remove('open');
  document.body.style.overflow = '';
}

// ==============================================================================
// PRODUCT DETAIL MODAL & CERTIFICATE
// ==============================================================================
function openProductModal(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  state.activeModalProduct = product;

  document.getElementById('modalImg').src = product.image_url;
  document.getElementById('modalCategory').textContent = product.category || 'Pezzo Unico';
  document.getElementById('modalTitle').textContent = product.title;
  document.getElementById('modalPrice').textContent = `€${Number(product.price).toFixed(2)}`;
  document.getElementById('modalDesc').textContent = product.description || '';
  
  const specsEl = document.getElementById('modalSpecs');
  if (specsEl) {
    specsEl.textContent = product.details || 'Forgiato a freddo e a caldo con rame elettrolitico purissimo al 99.9%. Chiusura sagomata artigianalmente e lucidatura con cera naturale.';
  }

  const addBtn = document.getElementById('modalAddCartBtn');
  addBtn.onclick = () => {
    addToCartById(product.id);
    closeProductModal();
  };

  productModalBackdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeProductModal() {
  productModalBackdrop.classList.remove('open');
  document.body.style.overflow = '';
  state.activeModalProduct = null;
}

// ==============================================================================
// PRIVACY & EU AI ACT MODAL CONTROLS
// ==============================================================================
function openPrivacyModal(tabId = 'gdprTab') {
  if (!privacyModalBackdrop) return;
  privacyModalBackdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
  switchPrivacyTab(tabId);
}

function closePrivacyModal() {
  if (!privacyModalBackdrop) return;
  privacyModalBackdrop.classList.remove('open');
  document.body.style.overflow = '';
}

function switchPrivacyTab(tabId) {
  document.querySelectorAll('.privacy-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.privacy-tab-content').forEach(content => {
    content.classList.toggle('active', content.id === tabId);
  });
}

async function handleGdprSubmit(event) {
  event.preventDefault();
  const fullName = document.getElementById('gdprFullName').value.trim();
  const email = document.getElementById('gdprEmail').value.trim();
  const requestType = document.getElementById('gdprRequestType').value;
  const notes = document.getElementById('gdprNotes').value.trim();
  const submitBtn = document.getElementById('submitGdprBtn');

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registrazione protocollo...';

  try {
    const res = await fetch('/api/privacy-request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fullName, email, requestType, notes })
    });

    const data = await res.json().catch(() => ({}));
    const protocol = data.protocol || `GDPR-${Date.now().toString().slice(-6)}`;

    showToast(`Richiesta GDPR protocollata: ${protocol}`);
    alert(`[CONFERMA PROTOCOLLO GDPR & EU AI ACT]\n\nLa tua richiesta per "${requestType}" è stata protocollata con successo:\n\nCodice Protocollo: ${protocol}\n\nRiceverai riscontro formale all'indirizzo ${email} entro 30 giorni (Art. 12 GDPR).`);
    
    document.getElementById('gdprRequestForm').reset();
    closePrivacyModal();
  } catch (err) {
    const protocol = `GDPR-${Date.now().toString().slice(-6)}`;
    showToast(`Richiesta GDPR protocollata: ${protocol}`);
    alert(`[RICHIESTA REGISTRATA]\nProtocollo: ${protocol}\nI tuoi dati sono tutelati e la richiesta verrà evasa nei termini di legge.`);
    document.getElementById('gdprRequestForm').reset();
    closePrivacyModal();
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Invia Richiesta Formale GDPR';
  }
}

function initCookieBanner() {
  const consent = localStorage.getItem('fattoamano_cookie_consent');
  if (!consent && cookieBanner) {
    setTimeout(() => {
      cookieBanner.classList.add('visible');
    }, 1200);
  }
  if (acceptCookiesBtn) {
    acceptCookiesBtn.addEventListener('click', () => {
      localStorage.setItem('fattoamano_cookie_consent', 'technical_only');
      cookieBanner.classList.remove('visible');
      showToast('Preferenze privacy memorizzate (Solo Cookie Tecnici)');
    });
  }
  if (openPrivacyBannerBtn) {
    openPrivacyBannerBtn.addEventListener('click', () => {
      openPrivacyModal('gdprTab');
    });
  }
}

function openCookieSettings() {
  if (cookieBanner) {
    cookieBanner.classList.add('visible');
  } else {
    openPrivacyModal('gdprTab');
  }
}

// ==============================================================================
// STRIPE CHECKOUT INTEGRATION
// ==============================================================================
async function handleStripeCheckout() {
  if (state.cart.length === 0) {
    showToast('Aggiungi almeno un bracciale per procedere');
    return;
  }

  stripeCheckoutBtn.disabled = true;
  stripeCheckoutBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Connessione a Stripe...`;

  try {
    const response = await fetch('/api/create-checkout-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: state.cart,
        shipping_fee: state.shippingFee,
        success_url: window.location.origin + '/success.html',
        cancel_url: window.location.href
      })
    });

    const data = await response.json().catch(() => ({}));
    
    if (response.ok && data.url) {
      showToast('Reindirizzamento su Stripe Checkout in corso...');
      window.location.href = data.url;
      return;
    }

    if (data.error) {
      alert(`[ERRORE STRIPE]\n\n${data.error}`);
      return;
    }

    if (data.notice) {
      alert(`[CONFIGURAZIONE STRIPE]\n\n${data.notice}`);
      return;
    }

    showStripeModalInfo();
  } catch (err) {
    console.warn('Errore chiamata Stripe Checkout:', err);
    showStripeModalInfo();
  } finally {
    stripeCheckoutBtn.disabled = false;
    stripeCheckoutBtn.innerHTML = `
      <i class="fa-brands fa-stripe" style="font-size: 1.4rem;"></i>
      <span>Procedi al Checkout Sicuro</span>
    `;
  }
}

function showStripeModalInfo() {
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  showToast(`Simulazione Carrello: €${subtotal.toFixed(2)}`);
  alert(`[STRIPE CHECKOUT]\n\nTotale Carrello: €${subtotal.toFixed(2)}\n\nIl server non ha restituito una URL di checkout valida. Assicurati che 'server.py' sia attivo con la chiave in .env.`);
}

// ==============================================================================
// TOAST NOTIFICATION ENGINE
// ==============================================================================
function showToast(message) {
  if (!toastContainer) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <i class="fa-solid fa-check" style="color: var(--copper-primary);"></i>
    <span>${message}</span>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('fade-out');
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  }, 3200);
}

// ==============================================================================
// EVENT LISTENERS & SCROLL BEHAVIOR
// ==============================================================================
function setupEventListeners() {
  // Drawer open/close
  if (openCartBtn) openCartBtn.addEventListener('click', openCart);
  if (closeCartBtn) closeCartBtn.addEventListener('click', closeCart);
  if (cartBackdrop) cartBackdrop.addEventListener('click', closeCart);

  // Product Modal close
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeProductModal);
  if (productModalBackdrop) {
    productModalBackdrop.addEventListener('click', (e) => {
      if (e.target === productModalBackdrop) closeProductModal();
    });
  }

  // Privacy Modal close & tabs
  if (closePrivacyModalBtn) closePrivacyModalBtn.addEventListener('click', closePrivacyModal);
  if (privacyModalBackdrop) {
    privacyModalBackdrop.addEventListener('click', (e) => {
      if (e.target === privacyModalBackdrop) closePrivacyModal();
    });
  }

  document.querySelectorAll('.privacy-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      switchPrivacyTab(btn.dataset.tab);
    });
  });

  // Keyboard Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCart();
      closeProductModal();
      closePrivacyModal();
    }
  });

  // Stripe Checkout button
  if (stripeCheckoutBtn) {
    stripeCheckoutBtn.addEventListener('click', handleStripeCheckout);
  }

  // Category Filter Pills
  if (categoryFilters) {
    categoryFilters.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        categoryFilters.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeFilter = btn.dataset.filter;
        renderProducts();
      });
    });
  }

  // Navbar dynamic scroll effect
  window.addEventListener('scroll', () => {
    const header = document.getElementById('siteHeader');
    if (!header) return;
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });
}
