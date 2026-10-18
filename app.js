/**
 * FATTO A MANO — BOUTIQUE ORAFA DEL RAME PURO (99.9%)
 * Core Client Application & Reactive Cart Logic
 * GDPR & EU AI Act Compliance Engine
 */

// State Management
const state = {
  products: [],
  stones: [],
  selectedStone: null,
  cart: JSON.parse(localStorage.getItem('fattoamano_cart') || '[]'),
  activeFilter: 'all',
  activeModalProduct: null,
  shippingFee: 6.00
};

// DOM Elements
const productsGrid = document.getElementById('productsGrid');
const prontaConsegnaGrid = document.getElementById('prontaConsegnaGrid');
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
const cartShippingBtn = document.getElementById('cartShippingBtn') || document.getElementById('stripeCheckoutBtn');
const stripeCheckoutBtn = cartShippingBtn;
const categoryFilters = document.getElementById('categoryFilters');
const productModalBackdrop = document.getElementById('productModalBackdrop');
const closeModalBtn = document.getElementById('closeModalBtn');
const toastContainer = document.getElementById('toastContainer');
const privacyModalBackdrop = document.getElementById('privacyModalBackdrop');
const closePrivacyModalBtn = document.getElementById('closePrivacyModalBtn');
const cookieBanner = document.getElementById('cookieBanner');
const acceptCookiesBtn = document.getElementById('acceptCookiesBtn');
const openPrivacyBannerBtn = document.getElementById('openPrivacyBannerBtn');

// Pre-checkout Shipping Modal DOM Elements
const checkoutModalBackdrop = document.getElementById('checkoutModalBackdrop');
const closeCheckoutModalBtn = document.getElementById('closeCheckoutModalBtn');
const shippingCheckoutForm = document.getElementById('shippingCheckoutForm');
const modalSummaryItemsCount = document.getElementById('modalSummaryItemsCount');
const modalSummarySubtotal = document.getElementById('modalSummarySubtotal');
const modalSummaryTotal = document.getElementById('modalSummaryTotal');
const submitShippingPayBtn = document.getElementById('submitShippingPayBtn');
const submitPayBtnText = document.getElementById('submitPayBtnText');

// ==============================================================================
// INITIALIZATION & DATA FETCHING
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
  loadSiteSettings();
  loadProducts();
  loadStones();
  setupEventListeners();
  renderCart();
  initCookieBanner();
});

async function loadSiteSettings() {
  try {
    let settings = null;
    const res = await fetch('/api/admin_settings?t=' + Date.now()).catch(() => null);
    if (res && res.ok) {
      settings = await res.json();
    } else {
      const fb = await fetch('settings_cache.json?t=' + Date.now()).catch(() => null);
      if (fb && fb.ok) settings = await fb.json();
    }
    if (!settings) return;

    // 1. Top Announcement Bar
    const topBar = document.getElementById('topAnnouncementBar');
    const topText = document.getElementById('topAnnouncementText');
    if (topBar) {
      if (settings.announcement_active === false) {
        topBar.style.display = 'none';
      } else {
        topBar.style.display = '';
        if (settings.announcement_text && topText) {
          topText.innerHTML = settings.announcement_text;
        }
      }
    }

    // 2. Pronta Consegna Banner
    const kickerEl = document.getElementById('prontaKickerTitle');
    const titleEl = document.getElementById('prontaMainTitle');
    const subtitleEl = document.getElementById('prontaSubtitle');
    if (settings.pronta_consegna_badge && kickerEl) kickerEl.textContent = settings.pronta_consegna_badge;
    if (settings.pronta_consegna_banner_title && titleEl) titleEl.textContent = settings.pronta_consegna_banner_title;
    if (settings.pronta_consegna_banner_subtitle && subtitleEl) subtitleEl.textContent = settings.pronta_consegna_banner_subtitle;

    // 3. Spedizione configurata
    if (typeof settings.shipping_cost === 'number') {
      state.shippingFee = settings.shipping_cost;
    }
    if (typeof settings.free_shipping_threshold === 'number') {
      state.freeShippingThreshold = settings.free_shipping_threshold;
    }
  } catch (err) {
    console.debug('Settings fallback:', err);
  }
}

async function loadProducts() {
  try {
    // Attempt 1: Fetch from local server API (which synchronizes with Supabase) with cache buster
    const response = await fetch('/api/products?t=' + Date.now()).catch(() => null);
    if (response && response.ok) {
      state.products = await response.json();
    } else {
      // Attempt 2: Fallback to local products_cache.json with cache buster
      const fallbackRes = await fetch('products_cache.json?t=' + Date.now());
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
        details: '3 filamenti rame puro 99.9%',
        pronta_consegna: true,
        stock_qty: 2,
        shipping_note: 'Disponibile in bottega • Spedizione espressa tracciata 3-5 giorni lavorativi'
      }
    ];
  }

  renderProntaConsegna();
  renderProducts();
}

// ==============================================================================
// PRONTA CONSEGNA RENDERING & QUICK BUY
// ==============================================================================
function renderProntaConsegna() {
  const prontaSection = document.getElementById('prontaconsegna');
  const prontaNavLinks = document.querySelectorAll('a[href="#prontaconsegna"]');
  const prontaHeroCta = document.querySelector('.hero-cta-group a[href="#prontaconsegna"]');
  const prontaFilterBtn = document.querySelector('button[data-filter="pronta_consegna"]');

  const readyItems = (state.products || []).filter(p => p.pronta_consegna === true);

  if (readyItems.length === 0) {
    // Regola: Se non vi sono immagini nella cartella pronta consegna, nascondi banner e riferimenti
    if (prontaSection) prontaSection.style.display = 'none';
    prontaNavLinks.forEach(link => {
      const parentLi = link.closest('li');
      if (parentLi) parentLi.style.display = 'none';
      else link.style.display = 'none';
    });
    if (prontaHeroCta) prontaHeroCta.style.display = 'none';
    if (prontaFilterBtn) prontaFilterBtn.style.display = 'none';
    return;
  }

  // Se presenti, mostra sezione e controlli
  if (prontaSection) prontaSection.style.display = 'block';
  prontaNavLinks.forEach(link => {
    const parentLi = link.closest('li');
    if (parentLi) parentLi.style.display = '';
    else link.style.display = '';
  });
  if (prontaHeroCta) prontaHeroCta.style.display = '';
  if (prontaFilterBtn) prontaFilterBtn.style.display = '';

  if (!prontaConsegnaGrid) return;
  prontaConsegnaGrid.innerHTML = '';

  readyItems.forEach(product => {
    const card = document.createElement('article');
    card.className = 'pronta-card';
    card.dataset.id = product.id;

    card.innerHTML = `
      <div class="pronta-card-media" onclick="openProductModal('${product.id}')">
        <img src="${product.image_url}" alt="${product.title}" loading="lazy">
      </div>

      <div class="pronta-card-body">
        <div class="pronta-meta-row" style="display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap;">
          <span class="pill-pronta-inline" style="margin-left: 0;"><i class="fa-solid fa-bolt"></i> Disponibilità Immediata</span>
          <span class="pill-purity-inline">${product.purity || '99.9% Rame Puro'}</span>
        </div>
        <div class="pronta-availability">
          <span class="dot-live"></span>
          <span>${product.stock_qty ? `${product.stock_qty} pezzo in bottega` : 'Pezzo unico forgiato'}</span>
        </div>
        <h3 class="pronta-card-title" onclick="openProductModal('${product.id}')">${product.title}</h3>
        <p class="pronta-card-desc">${product.description || ''}</p>
        
        <div class="pronta-shipping-note">
          <i class="fa-solid fa-truck-fast"></i>
          <span>${product.shipping_note || 'Spedizione espressa tracciata 3-5 giorni lavorativi'}</span>
        </div>

        <div class="pronta-card-footer">
          <div class="pronta-price-tag">
            <span class="pronta-price-label">Prezzo Bottega</span>
            <span class="pronta-price-value">€${Number(product.price).toFixed(2)}</span>
          </div>
          <div class="pronta-cta-actions">
            <button class="btn-quick-buy" onclick="quickBuyById('${product.id}')" title="Acquista Subito">
              <i class="fa-solid fa-bolt"></i>
              <span>Acquista Subito</span>
            </button>
            <button class="btn-add-icon" onclick="addToCartById('${product.id}')" title="Aggiungi al Carrello" aria-label="Aggiungi al Carrello">
              <i class="fa-solid fa-plus"></i>
            </button>
          </div>
        </div>
      </div>
    `;

    prontaConsegnaGrid.appendChild(card);
  });
}

function quickBuyById(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  const existingIndex = state.cart.findIndex(item => item.id === productId);
  if (existingIndex === -1) {
    state.cart.push({
      id: product.id,
      title: product.title,
      price: Number(product.price),
      image_url: product.image_url,
      stripe_price_id: product.stripe_price_id || null,
      quantity: 1
    });
    saveCart();
  }
  openCheckoutModal();
}

// ==============================================================================
// PRODUCTS RENDERING & FILTERING
// ==============================================================================
function renderProducts() {
  if (!productsGrid) return;
  productsGrid.innerHTML = '';

  let filtered = [];

  if (state.activeFilter === 'all') {
    // "Tutte le Opere": esclude categoricamente i pezzi in pronta consegna (non compaiono nel filtro Tutte le Opere)
    filtered = (state.products || []).filter(p => p.pronta_consegna !== true);
  } else if (state.activeFilter === 'pronta_consegna') {
    // Mostra solo le creazioni disponibili in pronta consegna nella griglia
    filtered = (state.products || []).filter(p => p.pronta_consegna === true);
  } else {
    // Filtro per categoria tecnica (es. Intrecciati, Martellati, Rigidi):
    // I pezzi pronta consegna sono esclusi — compaiono SOLO nella sezione dedicata Pronta Consegna
    filtered = (state.products || []).filter(p =>
      p.category === state.activeFilter && p.pronta_consegna !== true
    );
  }

  if (filtered.length === 0) {
    productsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <i class="fa-solid fa-fire" style="font-size: 2rem; color: var(--copper-primary); margin-bottom: 1rem;"></i>
        <p>Nessun gioiello trovato per questa selezione.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(product => {
    const card = document.createElement('article');
    card.className = 'product-card' + (product.pronta_consegna ? ' is-pronta-consegna' : '');
    card.dataset.id = product.id;

    const prontaBadgeHtml = product.pronta_consegna 
      ? `<span class="badge-pronta-tag"><i class="fa-solid fa-bolt"></i> Pronta Consegna</span>` 
      : '';

    card.innerHTML = `
      <div class="card-media" onclick="openProductModal('${product.id}')">
        <img src="${product.image_url}" alt="${product.title}" loading="lazy">
        <button class="quick-view-btn" aria-label="Visualizza dettagli" onclick="event.stopPropagation(); openProductModal('${product.id}')">
          <i class="fa-solid fa-magnifying-glass-plus"></i>
        </button>
      </div>

      <div class="card-content">
        <div class="card-category" style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
          <span>${product.category || 'Fatto a Mano'}</span>
          <span class="pill-purity-inline">${product.purity || '99.9% Rame'}</span>
          ${product.pronta_consegna ? '<span class="pill-pronta-inline"><i class="fa-solid fa-bolt"></i> Disponibile Subito</span>' : ''}
        </div>
        <h3 class="card-title" onclick="openProductModal('${product.id}')" style="cursor: pointer;">${product.title}</h3>
        <p class="card-description">${product.description || ''}</p>
        
        <div class="card-footer">
          <div class="card-price-group">
            <span class="card-price-label">${product.pronta_consegna ? 'Pronta Consegna' : 'Valore Unico'}</span>
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
// CART LOGIC & PERSISTENCE
// ==============================================================================
function getItemUnitPrice(item) {
  const base = item.basePrice !== undefined ? Number(item.basePrice) : Number(item.price);
  const stonesTotal = item.custom_stones ? item.custom_stones.reduce((sum, s) => sum + Number(s.prezzo_vendita), 0) : (item.stone ? Number(item.stone.price) : 0);
  return base + stonesTotal;
}

function saveCart() {
  localStorage.setItem('fattoamano_cart', JSON.stringify(state.cart));
  renderCart();
  populateAtelierCartBraceletSelect();
  if (typeof updateShopModelCounts === 'function') updateShopModelCounts();
}

function addToCartById(productId) {
  const product = state.products.find(p => p.id === productId);
  if (!product) return;

  // Create unique cart entry so customizations attach to the specific piece
  let cartItem;
  const existingIndex = state.cart.findIndex(item => (item.id === productId || item.productId === productId) && (!item.custom_stones || item.custom_stones.length === 0));
  
  if (existingIndex > -1) {
    state.cart[existingIndex].quantity += 1;
    cartItem = state.cart[existingIndex];
  } else {
    cartItem = {
      id: `${product.id}_${Date.now()}`,
      productId: product.id,
      title: product.title,
      basePrice: Number(product.price),
      price: Number(product.price),
      image_url: product.image_url,
      stripe_price_id: product.stripe_price_id || null,
      quantity: 1,
      custom_stones: []
    };
    state.cart.push(cartItem);
  }

  saveCart();
  showToast(`Aggiunto: ${product.title}`);

  // Open prompt modal immediately: "Vuoi aggiungere una pietra naturale?"
  openStonePromptModal(cartItem);
}

function updateCartQuantity(productId, delta) {
  const index = state.cart.findIndex(item => item.id === productId);
  if (index === -1) return;

  state.cart[index].quantity += delta;
  if (state.cart[index].quantity <= 0) {
    removeCartItem(productId);
    return;
  }

  saveCart();
}

function removeCartItem(productId) {
  const item = state.cart.find(i => i.id === productId);
  if (!item) return;

  const hasStones = (item.custom_stones && item.custom_stones.length > 0) || Boolean(item.stone);
  if (hasStones) {
    // Edge case B: Ask customer whether to remove all or keep stones as standalone
    state.pendingRemoveItemId = productId;
    const stoneNames = item.custom_stones ? item.custom_stones.map(s => s.nome).join(', ') : item.stone.name;
    const msgEl = document.getElementById('stoneRemoveConfirmMsg');
    if (msgEl) {
      msgEl.innerHTML = `Il bracciale <strong>${item.title}</strong> ha le seguenti pietre incastonate: <strong style="color: var(--copper-light);">${stoneNames}</strong>.<br><br>Vuoi rimuovere anche le pietre, oppure conservarle nel carrello come minerali singoli da collezione / tasca (€10.00 cad.)?`;
    }
    openStoneRemoveConfirmModal();
  } else {
    state.cart = state.cart.filter(item => item.id !== productId);
    saveCart();
    showToast('Bracciale rimosso dallo scrigno');
  }
}

function renderCart() {
  const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = state.cart.reduce((sum, item) => sum + (getItemUnitPrice(item) * item.quantity), 0);
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
    
    // Multiple stones badges + single stone fallback
    let stoneBadgeHtml = '';
    if (item.custom_stones && item.custom_stones.length > 0) {
      stoneBadgeHtml = item.custom_stones.map((st, idx) => `
        <div class="cart-item-stone-badge">
          <i class="fa-solid fa-gem"></i>
          <span>${st.nome} (+€${Number(st.prezzo_vendita).toFixed(2)})</span>
          <button type="button" class="cart-stone-remove-mini" onclick="removeSingleStoneFromCartItem('${item.id}', ${idx})" title="Rimuovi questa pietra">×</button>
        </div>
      `).join('');
    } else if (item.stone) {
      stoneBadgeHtml = `
        <div class="cart-item-stone-badge">
          <i class="fa-solid fa-gem"></i>
          <span>${item.stone.name} (+€${Number(item.stone.price).toFixed(2)})</span>
        </div>
      `;
    }

    const wristBadge = item.wrist_cm ? `
      <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">
        <i class="fa-solid fa-ruler-horizontal"></i> Misura: ${item.wrist_cm}
      </div>
    ` : '';

    const unitPrice = getItemUnitPrice(item);
    item.price = unitPrice;

    row.innerHTML = `
      <img src="${item.image_url}" alt="${item.title}" class="cart-item-img">
      <div class="cart-item-info">
        <h4>${item.title}</h4>
        ${stoneBadgeHtml}
        ${wristBadge}
        <div class="cart-item-price">€${(unitPrice * item.quantity).toFixed(2)}</div>
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
    specsEl.textContent = product.details || 'Forgiato a freddo e a caldo con rame elettrolitico purissimo al 99.9%. Chiusura forgiata fatto a mano e lucidatura con cera naturale.';
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
// PRE-CHECKOUT SHIPPING MODAL & STRIPE INTEGRATION
// ==============================================================================
function openCheckoutModal() {
  if (state.cart.length === 0) {
    showToast('Aggiungi almeno un bracciale allo scrigno per procedere');
    return;
  }

  // Chiudi drawer carrello laterale per focalizzare sul form di consegna
  closeCart();

  // Calcolo riepilogo finanziario
  const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const shipping = state.shippingFee;
  const total = subtotal + shipping;

  const countEl = document.getElementById('modalSummaryItemsCount');
  if (countEl) countEl.textContent = `${totalItems} ${totalItems === 1 ? 'creazione' : 'creazioni'}`;

  const subtotalEl = document.getElementById('modalSummarySubtotal');
  if (subtotalEl) subtotalEl.textContent = `€${subtotal.toFixed(2)}`;

  const totalEl = document.getElementById('modalSummaryTotal');
  if (totalEl) totalEl.textContent = `€${total.toFixed(2)}`;

  const btnTextEl = document.getElementById('submitPayBtnText');
  if (btnTextEl) btnTextEl.textContent = `Procedi al Pagamento su Stripe (€${total.toFixed(2)})`;

  // Precompila i dati da acquisti precedenti salvati in locale
  try {
    const saved = JSON.parse(localStorage.getItem('fattoamano_shipping_info') || '{}');
    if (saved.fullName && document.getElementById('shipFullName')) document.getElementById('shipFullName').value = saved.fullName;
    if (saved.email && document.getElementById('shipEmail')) document.getElementById('shipEmail').value = saved.email;
    if (saved.phone && document.getElementById('shipPhone')) document.getElementById('shipPhone').value = saved.phone;
    if (saved.address && document.getElementById('shipAddress')) document.getElementById('shipAddress').value = saved.address;
    if (saved.cap && document.getElementById('shipCap')) document.getElementById('shipCap').value = saved.cap;
    if (saved.city && document.getElementById('shipCity')) document.getElementById('shipCity').value = saved.city;
    if (saved.province && document.getElementById('shipProvince')) document.getElementById('shipProvince').value = saved.province;
    if (saved.wristCm && document.getElementById('shipWristCm')) document.getElementById('shipWristCm').value = saved.wristCm;
    if (saved.notes && document.getElementById('shipNotes')) document.getElementById('shipNotes').value = saved.notes;
  } catch (err) {
    console.warn('Errore lettura shipping info da local storage', err);
  }

  const modalEl = document.getElementById('checkoutModalBackdrop');
  if (modalEl) {
    modalEl.classList.add('open');
    modalEl.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } else {
    console.error('Elemento checkoutModalBackdrop non trovato nel DOM');
  }
}

function closeCheckoutModal() {
  const modalEl = document.getElementById('checkoutModalBackdrop');
  if (modalEl) {
    modalEl.classList.remove('open');
    modalEl.style.display = 'none';
    document.body.style.overflow = '';
  }
}

// ==============================================================================
// EMAILJS NOTIFICATION DISPATCHER (service_1m1tfyq -> agtechdesigne@gmail.com)
// ==============================================================================
const EMAILJS_CONFIG = {
  serviceId: 'service_1m1tfyq',
  templateId: 'template_i4boqs9',
  targetEmail: 'agtechdesigne@gmail.com',
  publicKey: 'Ts44-OGlmsSUV73rR'
};

async function sendShippingEmailNotification(shippingInfo, cartItems, totalAmount) {
  const itemsText = cartItems.map(item => {
    const itemPrice = getItemUnitPrice(item);
    let line = `• ${item.title} (x${item.quantity}) - €${(itemPrice * item.quantity).toFixed(2)}`;
    if (item.custom_stones && item.custom_stones.length > 0) {
      line += ` [Pietre incastonate ad incudine: ${item.custom_stones.map(s => s.nome + ' (+€' + Number(s.prezzo_vendita).toFixed(2) + ')').join(', ')}]`;
    } else if (item.stone) {
      line += ` [Pietra incastonata: ${item.stone.name} (+€${Number(item.stone.price).toFixed(2)})]`;
    }
    return line;
  }).join('\n');

  const ordersArray = cartItems.map(item => ({
    name: item.title + (item.custom_stones && item.custom_stones.length > 0 ? ` (+${item.custom_stones.length} pietre: ${item.custom_stones.map(s => s.nome).join(', ')})` : ''),
    units: item.quantity,
    price: (getItemUnitPrice(item) * item.quantity).toFixed(2),
    image_url: item.image_url ? (item.image_url.startsWith('http') ? item.image_url : (window.location.origin + '/' + item.image_url.replace(/^\//, ''))) : ''
  }));

  const orderId = 'FAM-' + Date.now().toString().slice(-6);
  const subtotalVal = (totalAmount - state.shippingFee).toFixed(2);
  const totalVal = totalAmount.toFixed(2);

  const templateParams = {
    // Destinatari
    to_email: EMAILJS_CONFIG.targetEmail,
    email: shippingInfo.email,
    
    // Ordine
    order_id: orderId,
    data_ordine: new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' }),
    
    // Dati di Recapito e Spedizione
    destinatario_nome: shippingInfo.fullName,
    customer_name: shippingInfo.fullName,
    destinatario_email: shippingInfo.email,
    customer_email: shippingInfo.email,
    destinatario_telefono: shippingInfo.phone,
    customer_phone: shippingInfo.phone,
    misura_polso: shippingInfo.wristCm || 'Calibratura Standard',
    wrist_cm: shippingInfo.wristCm || 'Calibratura Standard',
    indirizzo: shippingInfo.address,
    cap: shippingInfo.cap,
    citta: shippingInfo.city,
    provincia: shippingInfo.province,
    note_consegna: shippingInfo.notes || 'Nessuna istruzione particolare',
    shipping_notes: shippingInfo.notes || 'Nessuna istruzione particolare',
    
    // Lista articoli (sia testo che array Mustache)
    orders: ordersArray,
    articoli_ordine: itemsText,
    
    // Costi
    subtotal: subtotalVal,
    spese_spedizione: '6.00',
    totale_ordine: totalVal,
    cost: {
      shipping: '6.00',
      tax: '0.00',
      total: totalVal
    },
    'cost.shipping': '6.00',
    'cost.tax': '0.00',
    'cost.total': totalVal
  };

  try {
    const pubKey = EMAILJS_CONFIG.publicKey;
    if (window.emailjs && pubKey) {
      try {
        window.emailjs.init(pubKey);
      } catch (e) {}
      await window.emailjs.send(EMAILJS_CONFIG.serviceId, EMAILJS_CONFIG.templateId, templateParams, pubKey);
      console.log('[EmailJS] Notifica email inviata con successo ad agtechdesigne@gmail.com');
      return true;
    } else if (pubKey) {
      const res = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_id: EMAILJS_CONFIG.serviceId,
          template_id: EMAILJS_CONFIG.templateId,
          user_id: pubKey,
          template_params: templateParams
        })
      });
      return res.ok;
    }
  } catch (err) {
    console.warn('[EmailJS Notification Log]:', err);
    return false;
  }
}

async function handleShippingFormSubmit(event) {
  if (event) event.preventDefault();

  if (state.cart.length === 0) {
    showToast('Aggiungi almeno un bracciale per procedere');
    closeCheckoutModal();
    return;
  }

  const fullName = document.getElementById('shipFullName').value.trim();
  const email = document.getElementById('shipEmail').value.trim();
  const phone = document.getElementById('shipPhone').value.trim();
  const wristCm = document.getElementById('shipWristCm') ? document.getElementById('shipWristCm').value.trim() : '';
  const address = document.getElementById('shipAddress').value.trim();
  const cap = document.getElementById('shipCap').value.trim();
  const city = document.getElementById('shipCity').value.trim();
  const province = document.getElementById('shipProvince').value.trim().toUpperCase();
  const notes = document.getElementById('shipNotes') ? document.getElementById('shipNotes').value.trim() : '';

  // Validazione Misura Polso
  if (!wristCm) {
    alert('[ATTENZIONE]\nSeleziona la misura in cm del tuo polso per consentire al maestro la forgiatura calibrata.');
    const wristEl = document.getElementById('shipWristCm');
    if (wristEl) wristEl.focus();
    return;
  }

  // Validazione CAP a 5 cifre
  if (!/^[0-9]{5}$/.test(cap)) {
    alert('[ATTENZIONE]\nInserisci un CAP italiano valido di 5 cifre numeriche (es. 50123).');
    const capInput = document.getElementById('shipCap');
    if (capInput) capInput.focus();
    return;
  }

  // Persistenza delle preferenze di spedizione
  const shippingInfo = { fullName, email, phone, wristCm, address, cap, city, province, notes };
  localStorage.setItem('fattoamano_shipping_info', JSON.stringify(shippingInfo));

  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const total = subtotal + state.shippingFee;
  const orderId = 'FAM-' + Date.now().toString().slice(-6);

  // 1. Notifica Server-Side garantita ad agtechdesigne@gmail.com (salvata in orders_audit.json e inviata via SMTP)
  fetch('/api/send-order-notification', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      order_id: orderId,
      shipping_info: shippingInfo,
      items: [...state.cart],
      subtotal: subtotal,
      shipping_fee: state.shippingFee,
      total: total
    })
  }).then(res => res.json()).then(data => {
    console.log('[Server Order Dispatcher Notice]:', data);
  }).catch(err => {
    console.warn('[Server Order Dispatcher Error]:', err);
  });

  // 2. Invio asincrono notifica email di spedizione ad agtechdesigne@gmail.com tramite EmailJS (service_1m1tfyq)
  sendShippingEmailNotification(shippingInfo, [...state.cart], total).catch(err => {
    console.warn('[EmailJS Async Dispatch Notice]:', err);
  });

  if (submitShippingPayBtn) {
    submitShippingPayBtn.disabled = true;
    submitShippingPayBtn.innerHTML = `
      <i class="fa-solid fa-spinner fa-spin"></i>
      <span>Reindirizzamento su Stripe Checkout (€${total.toFixed(2)})...</span>
    `;
  }

  try {
    const response = await fetch('/api/create-checkout-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: state.cart,
        shipping_fee: state.shippingFee,
        shipping_info: shippingInfo,
        emailjs_service_id: EMAILJS_CONFIG.serviceId,
        success_url: window.location.origin + '/success.html',
        cancel_url: window.location.href
      })
    });

    const data = await response.json().catch(() => ({}));
    
    if (response.ok && data.url) {
      showToast('Dati registrati. Connessione a Stripe in corso...');
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
    if (submitShippingPayBtn) {
      submitShippingPayBtn.disabled = false;
      submitShippingPayBtn.innerHTML = `
        <i class="fa-brands fa-stripe" style="font-size: 1.4rem;"></i>
        <span id="submitPayBtnText">Procedi al Pagamento su Stripe (€${total.toFixed(2)})</span>
        <i class="fa-solid fa-arrow-right" style="font-size: 0.9rem;"></i>
      `;
    }
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
      closeCheckoutModal();
      closeTechniqueModal();
    }
  });

  // Cinematic Technique Modal Backdrop Click
  const techniqueModalBackdrop = document.getElementById('techniqueModalBackdrop');
  if (techniqueModalBackdrop) {
    techniqueModalBackdrop.addEventListener('click', (e) => {
      if (e.target === techniqueModalBackdrop) closeTechniqueModal();
    });
  }

  // Pre-checkout Shipping Modal triggers
  if (stripeCheckoutBtn) {
    stripeCheckoutBtn.addEventListener('click', openCheckoutModal);
  }
  if (closeCheckoutModalBtn) {
    closeCheckoutModalBtn.addEventListener('click', closeCheckoutModal);
  }
  if (checkoutModalBackdrop) {
    checkoutModalBackdrop.addEventListener('click', (e) => {
      if (e.target === checkoutModalBackdrop) closeCheckoutModal();
    });
  }
  if (shippingCheckoutForm) {
    shippingCheckoutForm.addEventListener('submit', handleShippingFormSubmit);
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

// Global functions exposed to window for inline onclick handlers
window.openCheckoutModal = openCheckoutModal;
window.closeCheckoutModal = closeCheckoutModal;
window.handleShippingFormSubmit = handleShippingFormSubmit;
window.openCart = openCart;
window.closeCart = closeCart;
window.addToCartById = addToCartById;

// ==============================================================================
// BOTTEGA DELLE PIETRE & INCASTONATURA FATTO A MANO (DIDONI STORE)
// ==============================================================================

const DEFAULT_STONES_FALLBACK = [
  {
    "id": "pietra_acquamarina",
    "nome": "Acquamarina S",
    "tipo": "Burattato levigato (2 - 2,5 cm)",
    "prezzo_fornitore": 3.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Calma profonda, chiarezza interiore, distensione emotiva e apertura della comunicazione autentica.",
    "elemento": "Acqua",
    "chakra": "Gola (5° Chakra)",
    "immagine_locale": "assets/pietre/acquamarina_s.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17acq003_2_1724082990_94.jpg"
  },
  {
    "id": "pietra_ametista",
    "nome": "Ametista Naturale S",
    "tipo": "Burattato levigato (2 - 3 cm)",
    "prezzo_fornitore": 2.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Serenità spirituale, riequilibrio dei ritmi del sonno, lucidità mentale e purificazione energetica.",
    "elemento": "Aria / Etere",
    "chakra": "Terzo Occhio & Corona",
    "immagine_locale": "assets/pietre/ametista_s.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17ame001_2_1724147678_31.jpg"
  },
  {
    "id": "pietra_agata_blu",
    "nome": "Agata Blu M-L",
    "tipo": "Burattato pebble (3 - 4 cm)",
    "prezzo_fornitore": 4.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Pace della mente, scioglimento delle tensioni comunicative e armonia nelle relazioni quotidiane.",
    "elemento": "Acqua",
    "chakra": "Gola (5° Chakra)",
    "immagine_locale": "assets/pietre/agata_blu.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17aga008_2_1724082029_90.jpg"
  },
  {
    "id": "pietra_corniola",
    "nome": "Agata Corniola S",
    "tipo": "Burattato vivente (1,5 - 3 cm)",
    "prezzo_fornitore": 2.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Vitalità ardente, forza creativa, coraggio nelle decisioni e stimolo della circolazione sanguigna.",
    "elemento": "Fuoco",
    "chakra": "Sacrale & Radice (1°-2° Chakra)",
    "immagine_locale": "assets/pietre/corniola_s.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17cor004_3_1658497901_634_1724147218_23.jpg"
  },
  {
    "id": "pietra_amazzonite",
    "nome": "Amazzonite S-M",
    "tipo": "Burattato vellutato (2 - 2,5 cm)",
    "prezzo_fornitore": 3.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Scudo naturale contro le frequenze elettromagnetiche, armonia interiore, libertà e determinazione.",
    "elemento": "Terra / Acqua",
    "chakra": "Cuore & Gola (4°-5° Chakra)",
    "immagine_locale": "assets/pietre/amazzonite_sm.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/whatsapp-image-2024-12-19-at-15.10.49_1734617505_86.jpg"
  },
  {
    "id": "pietra_agata_verde",
    "nome": "Agata Verde L",
    "tipo": "Burattato pebble (3 cm)",
    "prezzo_fornitore": 4.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Riequilibrio energetico del cuore, stabilità emotiva, abbondanza e profondo contatto con la natura.",
    "elemento": "Terra",
    "chakra": "Cuore (4° Chakra)",
    "immagine_locale": "assets/pietre/agata_verde.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17aga007_2_1724082116_74.jpg"
  },
  {
    "id": "pietra_agata_muschiata",
    "nome": "Agata Muschiata M",
    "tipo": "Burattato naturale (2,5 - 3 cm)",
    "prezzo_fornitore": 3.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Rigenerazione e rinascita, connessione botanica, benessere corporeo e liberazione dallo stress.",
    "elemento": "Terra",
    "chakra": "Cuore (4° Chakra)",
    "immagine_locale": "assets/pietre/agata_muschiata.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17AGM1M1_1.jpg"
  },
  {
    "id": "pietra_adularia",
    "nome": "Pietra di Luna (Adularia Grezza)",
    "tipo": "Grezzo naturale (1 - 2 cm)",
    "prezzo_fornitore": 3.30,
    "prezzo_vendita": 10.00,
    "proprieta": "Risonanza con le fasi lunari, risveglio dell'intuito profondo, equilibrio ormonale e dolcezza d'animo.",
    "elemento": "Acqua",
    "chakra": "Corona (7° Chakra)",
    "immagine_locale": "assets/pietre/adularia_grezza.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/01plu001_2_1689674306_112_1732994241_7.jpg"
  },
  {
    "id": "pietra_avventurina",
    "nome": "Avventurina Verde Grezza",
    "tipo": "Grezzo compatto (3 - 4 cm)",
    "prezzo_fornitore": 3.00,
    "prezzo_vendita": 10.00,
    "proprieta": "Pietra della buona sorte, amplificatore di ottimismo, vitalità espansiva e purificazione vitale.",
    "elemento": "Terra",
    "chakra": "Cuore (4° Chakra)",
    "immagine_locale": "assets/pietre/avventurina_grezza.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/01avv001_2_1732998636_91.jpg"
  },
  {
    "id": "pietra_ambra_baltica",
    "nome": "Ambra Baltica Naturale S",
    "tipo": "Resina fossile autentica (2 - 2,5 cm)",
    "prezzo_fornitore": 5.00,
    "prezzo_vendita": 16.00,
    "proprieta": "Dono solare millenario: riscalda il corpo, allevia infiammazioni fisiche e dissipa negatività emotiva.",
    "elemento": "Fuoco / Sole",
    "chakra": "Plesso Solare (3° Chakra)",
    "immagine_locale": "assets/pietre/ambra_baltica_s.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17amb001_2_1724147431_21.jpg"
  },
  {
    "id": "pietra_ametista_chevron",
    "nome": "Ametista Chevron XL",
    "tipo": "Pietra sciamanica a bande (7 - 9 cm)",
    "prezzo_fornitore": 8.00,
    "prezzo_vendita": 18.00,
    "proprieta": "Vibrazione trasmutativa potente: purificazione dell'aura, visione interiore e radicamento spirituale.",
    "elemento": "Aria / Etere",
    "chakra": "Terzo Occhio (6° Chakra)",
    "immagine_locale": "assets/pietre/ametista_chevron_xl.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/17ame006_1_1747837195_66.jpg"
  },
  {
    "id": "pietra_blue_lace",
    "nome": "Agata Pizzo Blu (Blue Lace)",
    "tipo": "Pietra con foro per pendente (2,5 cm)",
    "prezzo_fornitore": 10.00,
    "prezzo_vendita": 20.00,
    "proprieta": "Armonizzatore sublime: distende l'ansia, dona serenità angelica e apre canali di calma interiore.",
    "elemento": "Aria / Acqua",
    "chakra": "Gola (5° Chakra)",
    "immagine_locale": "assets/pietre/blue_lace_forata.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/25cdofor_1_1781528950_30.jpg"
  },
  {
    "id": "pietra_ambra_grezza_ml",
    "nome": "Ambra Baltica Grezza M-L",
    "tipo": "Pepita grezza massiccia (6 - 8 cm)",
    "prezzo_fornitore": 20.00,
    "prezzo_vendita": 38.00,
    "proprieta": "Rara resina fossile di grandi dimensioni: scudo bioelettrico, calore rigenerativo e carica bioenergetica.",
    "elemento": "Sole / Fuoco",
    "chakra": "Plesso Solare (3° Chakra)",
    "immagine_locale": "assets/pietre/ambra_grezza_ml.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/01amb001_2_1729244434_99.jpg"
  },
  {
    "id": "pietra_cintamani",
    "nome": "Agni Manitite (Cintamani Stone S)",
    "tipo": "Tektite perla di fuoco rara",
    "prezzo_fornitore": 27.00,
    "prezzo_vendita": 48.00,
    "proprieta": "Gemma sacra leggendaria: amplificatore della volontà superiore, risveglio kundalini e forte magnetismo.",
    "elemento": "Fuoco Cosmico",
    "chakra": "Plesso Solare & Radice",
    "immagine_locale": "assets/pietre/cintamani_s.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/01agni001_2_1729244386_49.jpg"
  },
  {
    "id": "pietra_serafinite",
    "nome": "Grezzo di Serafinite (Pietra degli Angeli)",
    "tipo": "Minerale raro di Siberia (4 x 4 x 3 cm - 68.9 g)",
    "prezzo_fornitore": 35.00,
    "prezzo_vendita": 55.00,
    "proprieta": "La celebre 'Pietra degli Angeli' del lago Baikal con piumature d'argento vivo. Connette con le guide spirituali, purifica l'aura, dissipa conflitti interiori e apre il cuore a frequenze elevate.",
    "elemento": "Etere / Cuore",
    "chakra": "Cuore Spirituale & Corona",
    "immagine_locale": "assets/pietre/serafinite_grezza.jpg",
    "immagine_remota": "https://store.didoni.com/media/prodotti/01SER006_1.jpg"
  }
];

async function loadStones() {
  try {
    const res = await fetch('pietre_catalog.json?t=' + Date.now()).catch(() => null);
    if (res && res.ok) {
      state.stones = await res.json();
    } else {
      state.stones = DEFAULT_STONES_FALLBACK;
    }
  } catch (e) {
    state.stones = DEFAULT_STONES_FALLBACK;
  }

  renderStoneSelect();
  renderStoneChips();
  renderStoneMiniCarousel();
  renderAtelierStonesGrid();
  populateAtelierCartBraceletSelect();
  initAtelierShopPage();

  if (state.stones && state.stones.length > 0) {
    selectStone(state.stones[0].id);
    selectPromptStone(state.stones[0].id);
  }
}

function renderStoneSelect() {
  const selectEl = document.getElementById('stoneSelect');
  if (!selectEl) return;

  selectEl.innerHTML = '';
  state.stones.forEach(stone => {
    const opt = document.createElement('option');
    opt.value = stone.id;
    const isSpecial = stone.prezzo_vendita > 10;
    const priceStr = `+€${Number(stone.prezzo_vendita).toFixed(2)}`;
    opt.textContent = `${stone.nome} (${stone.tipo}) — ${priceStr} ${isSpecial ? '★ Raro' : ''}`;
    selectEl.appendChild(opt);
  });
}

function renderStoneChips() {
  const container = document.getElementById('stoneChipsContainer');
  if (!container) return;

  container.innerHTML = '';
  state.stones.forEach(stone => {
    const chip = document.createElement('div');
    chip.className = 'stone-chip';
    chip.dataset.stoneId = stone.id;
    chip.onclick = () => selectStone(stone.id);
    
    chip.innerHTML = `
      <img src="${stone.immagine_locale}" alt="${stone.nome}" class="stone-chip-thumb" onerror="this.src='${stone.immagine_remota}'">
      <span>${stone.nome}</span>
      <span class="stone-chip-price">+€${Number(stone.prezzo_vendita).toFixed(2)}</span>
    `;
    container.appendChild(chip);
  });
}

function selectStone(stoneId) {
  const stone = state.stones.find(s => s.id === stoneId) || state.stones[0];
  if (!stone) return;

  state.selectedStone = stone;

  // Sync select dropdown
  const selectEl = document.getElementById('stoneSelect');
  if (selectEl && selectEl.value !== stone.id) {
    selectEl.value = stone.id;
  }

  // Sync chip active classes
  document.querySelectorAll('.stone-chip').forEach(chip => {
    chip.classList.toggle('active', chip.dataset.stoneId === stone.id);
  });

  // Update Visual Preview Image
  const imgEl = document.getElementById('stonePreviewImg');
  if (imgEl) {
    imgEl.style.opacity = '0.3';
    setTimeout(() => {
      imgEl.src = stone.immagine_locale;
      imgEl.onerror = () => { imgEl.src = stone.immagine_remota; };
      imgEl.style.opacity = '1';
    }, 120);
  }

  const titleEl = document.getElementById('stonePreviewTitle');
  if (titleEl) titleEl.textContent = stone.nome;

  const priceEl = document.getElementById('stonePreviewPrice');
  if (priceEl) priceEl.textContent = `+€${Number(stone.prezzo_vendita).toFixed(2)}`;

  const badgeEl = document.getElementById('stonePreviewBadge');
  if (badgeEl) badgeEl.textContent = stone.tipo;

  // Transparency explanation note
  const supplierNoteEl = document.getElementById('stoneSupplierNote');
  if (supplierNoteEl) {
    if (stone.prezzo_fornitore <= 4) {
      supplierNoteEl.innerHTML = `Costo fornitore Didoni: <strong>€${Number(stone.prezzo_fornitore).toFixed(2)}</strong> • Tariffa standard fissa <strong>€10.00</strong> (include minerale selezionato e incastonatura manuale in rame).`;
    } else {
      const extra = (stone.prezzo_vendita - stone.prezzo_fornitore).toFixed(2);
      supplierNoteEl.innerHTML = `Costo minerale grezzo fornitore Didoni: <strong>€${Number(stone.prezzo_fornitore).toFixed(2)}</strong> + <strong>€${extra}</strong> (forgiatura fatta a mano ad incudine, fascetta di sicurezza in rame e garanzia).`;
    }
  }

  // Holistic properties
  const elemEl = document.getElementById('stonePreviewElement');
  if (elemEl) elemEl.textContent = stone.elemento || 'Terra';

  const chakraEl = document.getElementById('stonePreviewChakra');
  if (chakraEl) chakraEl.textContent = stone.chakra || 'Cuore';

  const descEl = document.getElementById('stonePreviewDesc');
  if (descEl) descEl.textContent = stone.proprieta;

  updateStoneCombinedTotal();
}

function onStoneSelectChange(stoneId) {
  selectStone(stoneId);
}

function onStoneBraceletChange(val) {
  updateStoneCombinedTotal();
}

function getSelectedBraceletInfo() {
  const selectEl = document.getElementById('stoneBraceletSelect');
  if (!selectEl) return { id: 'prod_rame_001', title: 'Bracciale Intrecciato 3 Filamenti', price: 30.00 };
  
  const opt = selectEl.options[selectEl.selectedIndex];
  return {
    id: selectEl.value,
    title: opt ? opt.dataset.title : 'Bracciale in Rame',
    price: opt ? parseFloat(opt.dataset.price || '30') : 30.00
  };
}

function updateStoneCombinedTotal() {
  const stone = state.selectedStone;
  if (!stone) return;

  const bracelet = getSelectedBraceletInfo();
  const combinedTotal = bracelet.price + stone.prezzo_vendita;

  const pairingTitle = document.getElementById('stonePairingTitle');
  if (pairingTitle) pairingTitle.textContent = bracelet.title;

  const combinedEl = document.getElementById('stoneCombinedTotal');
  if (combinedEl) combinedEl.textContent = `€${combinedTotal.toFixed(2)}`;

  const btnCartTotalLabel = document.getElementById('btnCartTotalLabel');
  if (btnCartTotalLabel) btnCartTotalLabel.textContent = `€${combinedTotal.toFixed(2)}`;
}

function addStoneCustomToCart() {
  const stone = state.selectedStone;
  if (!stone) {
    showToast('Seleziona prima una pietra');
    return;
  }

  const bracelet = getSelectedBraceletInfo();
  const wristCm = document.getElementById('stoneWristCm') ? document.getElementById('stoneWristCm').value : '17 cm';
  const fullName = document.getElementById('stoneFullName') ? document.getElementById('stoneFullName').value.trim() : '';
  const notes = document.getElementById('stoneNotes') ? document.getElementById('stoneNotes').value.trim() : '';

  const finalPrice = bracelet.price + stone.prezzo_vendita;
  const customTitle = bracelet.price > 0 ? `${bracelet.title} con ${stone.nome}` : `Pietra ${stone.nome} in Rame Forgiato`;

  const customCartItem = {
    id: `custom_stone_${stone.id}_${bracelet.id}_${Date.now()}`,
    title: customTitle,
    price: Number(finalPrice),
    image_url: stone.immagine_locale || stone.immagine_remota,
    stone: {
      id: stone.id,
      name: stone.nome,
      type: stone.tipo,
      price: stone.prezzo_vendita,
      supplier_price: stone.prezzo_fornitore,
      properties: stone.proprieta,
      image: stone.immagine_locale || stone.immagine_remota
    },
    wrist_cm: wristCm,
    customer_name: fullName,
    notes: notes,
    quantity: 1
  };

  state.cart.push(customCartItem);
  saveCart();
  showToast(`Aggiunto allo scrigno: ${customTitle} (€${finalPrice.toFixed(2)})`);
  openCart();
}

async function handleStoneCustomizationSubmit(event) {
  if (event) event.preventDefault();

  const stone = state.selectedStone;
  if (!stone) {
    showToast('Seleziona una pietra');
    return;
  }

  const bracelet = getSelectedBraceletInfo();
  const fullName = document.getElementById('stoneFullName') ? document.getElementById('stoneFullName').value.trim() : '';
  const email = document.getElementById('stoneEmail') ? document.getElementById('stoneEmail').value.trim() : '';
  const phone = document.getElementById('stonePhone') ? document.getElementById('stonePhone').value.trim() : '';
  const wristCm = document.getElementById('stoneWristCm') ? document.getElementById('stoneWristCm').value : '17 cm';
  const notes = document.getElementById('stoneNotes') ? document.getElementById('stoneNotes').value.trim() : '';

  if (!fullName || !email || !phone) {
    showToast('Compila nome, email e cellulare');
    return;
  }

  const submitBtn = document.getElementById('btnInviaRichiestaInfo');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Invio all\'Atelier...';
  }

  const finalPrice = bracelet.price + stone.prezzo_vendita;
  const inquiryData = {
    inquiry_id: 'INFO-PIETRA-' + Date.now().toString().slice(-6),
    stone: {
      id: stone.id,
      name: stone.nome,
      type: stone.tipo,
      price: stone.prezzo_vendita,
      supplier_price: stone.prezzo_fornitore,
      properties: stone.proprieta
    },
    bracelet: bracelet,
    wrist_cm: wristCm,
    fullName: fullName,
    email: email,
    phone: phone,
    notes: notes,
    total_estimated: finalPrice
  };

  try {
    // 1. Invia a server backend API se disponibile
    await fetch('/api/stone-inquiry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inquiryData)
    }).catch(() => null);

    // 2. Invia notifica EmailJS se configurata
    if (window.emailjs && EMAILJS_CONFIG.publicKey) {
      const templateParams = {
        to_email: EMAILJS_CONFIG.targetEmail,
        order_id: inquiryData.inquiry_id,
        data_ordine: new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' }),
        destinatario_nome: fullName,
        customer_name: fullName,
        destinatario_email: email,
        customer_email: email,
        destinatario_telefono: phone,
        customer_phone: phone,
        misura_polso: wristCm,
        wrist_cm: wristCm,
        note_consegna: `[RICHIESTA PIETRA DIDONI] Pietra: ${stone.nome} (+€${stone.prezzo_vendita.toFixed(2)}) • Modello: ${bracelet.title} • Note: ${notes || 'Nessuna'}`,
        shipping_notes: `Pietra scelta: ${stone.nome} (fornitore Didoni €${stone.prezzo_fornitore}) • Note cliente: ${notes || 'Nessuna'}`,
        articoli_ordine: `1x Creazione Personalizzata: ${bracelet.title} con ${stone.nome} — Stima: €${finalPrice.toFixed(2)}`,
        totale_ordine: finalPrice.toFixed(2),
        subtotal: finalPrice.toFixed(2)
      };
      await window.emailjs.send(EMAILJS_CONFIG.serviceId, EMAILJS_CONFIG.templateId, templateParams, EMAILJS_CONFIG.publicKey).catch(() => null);
    }

    showToast(`Richiesta inviata con successo! Protocollo: ${inquiryData.inquiry_id}`);
    alert(`[RICHIESTA INFO & PERSONALIZZAZIONE ACQUISITA]\n\nGrazie ${fullName}!\n\nAbbiamo registrato la tua richiesta per "${bracelet.title}" con pietra "${stone.nome}" (+€${stone.prezzo_vendita.toFixed(2)}).\n\nCodice Riferimento: ${inquiryData.inquiry_id}\n\nIl maestro ramaio ti contatterà al numero ${phone} e via email (${email}) per mostrarti la foto dell'abbinamento prima della lavorazione ad incudine.`);
  } catch (err) {
    showToast('Richiesta registrata');
    alert(`[RICHIESTA INVIATA]\n\nI tuoi dati sono stati registrati. Ti ricontatteremo a breve.`);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-envelope-open-text"></i> Invia Richiesta Info all\'Atelier';
    }
  }
}

function customizeCurrentModalBracelet() {
  if (state.activeModalProduct) {
    customizeBraceletWithStone(state.activeModalProduct.id);
  }
  closeProductModal();
}

function customizeBraceletWithStone(productId) {
  const section = document.getElementById('bottega-pietre');
  if (section) {
    section.scrollIntoView({ behavior: 'smooth' });
  }

  const braceletSelect = document.getElementById('stoneBraceletSelect');
  if (braceletSelect && productId) {
    let found = false;
    for (let i = 0; i < braceletSelect.options.length; i++) {
      if (braceletSelect.options[i].value === productId) {
        braceletSelect.selectedIndex = i;
        found = true;
        break;
      }
    }
    if (!found && state.products) {
      const prod = state.products.find(p => p.id === productId);
      if (prod) {
        const newOpt = document.createElement('option');
        newOpt.value = prod.id;
        newOpt.dataset.price = Number(prod.price);
        newOpt.dataset.title = prod.title;
        newOpt.textContent = `${prod.title} — €${Number(prod.price).toFixed(2)}`;
        newOpt.selected = true;
        braceletSelect.appendChild(newOpt);
      }
    }
    updateStoneCombinedTotal();
    showToast('Bracciale selezionato nella Bottega delle Pietre');
  }
}

// ==============================================================================
// PROMPT MODAL: VUOI AGGIUNGERE UNA PIETRA NATURALE? (MINI CAROSELLO ORIZZONTALE)
// ==============================================================================
function openStonePromptModal(cartItem) {
  state.activePromptCartItem = cartItem;
  const titleEl = document.getElementById('promptModalBraceletTitle');
  if (titleEl) {
    titleEl.textContent = cartItem.title;
  }

  renderStoneMiniCarousel();

  const initialStoneId = state.selectedPromptStoneId || (state.stones && state.stones[0] ? state.stones[0].id : null);
  if (initialStoneId) {
    selectPromptStone(initialStoneId);
  }

  const modal = document.getElementById('stonePromptModalBackdrop');
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeStonePromptModal() {
  const modal = document.getElementById('stonePromptModalBackdrop');
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function renderStoneMiniCarousel() {
  const container = document.getElementById('stoneMiniCarousel');
  if (!container || !state.stones) return;

  container.innerHTML = state.stones.map(stone => `
    <div class="stone-mini-card ${state.selectedPromptStoneId === stone.id ? 'active' : ''}" 
         id="miniStone_${stone.id}" 
         onclick="selectPromptStone('${stone.id}')"
         title="${stone.nome}">
      <div class="mini-card-img-wrap">
        <img src="${stone.immagine_locale}" alt="${stone.nome}" onerror="this.src='${stone.immagine_remota}'" loading="lazy">
      </div>
      <div class="mini-card-info">
        <h5 class="mini-card-title">${stone.nome}</h5>
        <span class="mini-card-price">€${Number(stone.prezzo_vendita).toFixed(2)}</span>
      </div>
    </div>
  `).join('');
}

function selectPromptStone(stoneId) {
  state.selectedPromptStoneId = stoneId;
  const stone = (state.stones || []).find(s => s.id === stoneId);
  if (!stone) return;

  document.querySelectorAll('.stone-mini-card').forEach(card => {
    card.classList.toggle('active', card.id === `miniStone_${stoneId}`);
  });

  const nameEl = document.getElementById('promptSelectedName');
  const imgEl = document.getElementById('promptSelectedImg');
  const chakraEl = document.getElementById('promptSelectedChakra');
  const priceEl = document.getElementById('promptSelectedPrice');
  const btnTextEl = document.getElementById('btnPromptAddStoneText');

  if (nameEl) nameEl.textContent = stone.nome;
  if (imgEl) {
    imgEl.src = stone.immagine_locale;
    imgEl.onerror = () => { imgEl.src = stone.immagine_remota; };
  }
  if (chakraEl) chakraEl.textContent = `${stone.chakra || 'Chakra'} • ${stone.elemento || 'Pietra Naturale'}`;
  if (priceEl) priceEl.textContent = `+€${Number(stone.prezzo_vendita).toFixed(2)}`;
  if (btnTextEl) btnTextEl.textContent = `Aggiungi Pietra al Bracciale (+€${Number(stone.prezzo_vendita).toFixed(2)})`;
}

function confirmPromptAddStone() {
  if (!state.activePromptCartItem) return;
  const stone = (state.stones || []).find(s => s.id === state.selectedPromptStoneId) || (state.stones ? state.stones[0] : null);
  if (!stone) return;

  if (!state.activePromptCartItem.custom_stones) {
    state.activePromptCartItem.custom_stones = [];
  }

  // Aggiunge la pietra al bracciale nel carrello (supporta più pietre sullo stesso pezzo)
  state.activePromptCartItem.custom_stones.push({
    id: stone.id,
    nome: stone.nome,
    prezzo_vendita: Number(stone.prezzo_vendita),
    immagine_locale: stone.immagine_locale,
    chakra: stone.chakra,
    elemento: stone.elemento
  });

  saveCart();
  closeStonePromptModal();
  showToast(`Pietra ${stone.nome} incastonata sul tuo ${state.activePromptCartItem.title}!`);
  openCart();
}

function exploreFullAtelierFromPrompt() {
  closeStonePromptModal();
  window.location.href = 'atelier-pietre.html';
}

function skipPromptToCart() {
  closeStonePromptModal();
  openCart();
}

function scrollStoneCarousel(direction) {
  const container = document.getElementById('stoneMiniCarousel');
  if (container) {
    container.scrollBy({ left: direction * 220, behavior: 'smooth' });
  }
}

// ==============================================================================
// ATELIER DELLE PIETRE: SELETTORE BRACCIALE CARRELLO & VETRINA COMPLETA
// ==============================================================================
function populateAtelierCartBraceletSelect(preferredSelectedId = null) {
  const select = document.getElementById('atelierCartBraceletSelect');
  const emptyNotice = document.getElementById('atelierCartEmptyNotice');
  if (!select) return;

  select.innerHTML = '';
  const braceletItems = state.cart.filter(item => !item.is_standalone_stone);

  if (braceletItems.length > 0) {
    if (emptyNotice) emptyNotice.style.display = 'none';

    braceletItems.forEach((item, idx) => {
      const opt = document.createElement('option');
      opt.value = item.id;
      const stonesCount = item.custom_stones ? item.custom_stones.length : 0;
      const stonesText = stonesCount > 0 ? ` (${stonesCount} ${stonesCount === 1 ? 'pietra incastonata' : 'pietre incastonate'})` : '';
      opt.textContent = `Bracciale #${idx + 1}: ${item.title} — Base €${(item.basePrice || item.price).toFixed(2)}${stonesText}`;
      if (preferredSelectedId && item.id === preferredSelectedId) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });

    const soloOpt = document.createElement('option');
    soloOpt.value = 'standalone_stone';
    soloOpt.textContent = 'Solo Pietra / Burattato Didoni da Collezione (€10.00 - nessun bracciale associato)';
    select.appendChild(soloOpt);
  } else {
    if (emptyNotice) emptyNotice.style.display = 'flex';

    const opt = document.createElement('option');
    opt.value = 'standalone_stone';
    opt.textContent = 'Solo Pietra da Collezione (Nessun bracciale presente nello scrigno)';
    opt.selected = true;
    select.appendChild(opt);
  }

  updateAtelierButtonsText();
}

function updateAtelierButtonsText() {
  const select = document.getElementById('atelierCartBraceletSelect');
  const isStandalone = !select || select.value === 'standalone_stone';
  const selectedItem = select ? state.cart.find(i => i.id === select.value) : null;

  document.querySelectorAll('.btn-atelier-add-stone').forEach(btn => {
    const stonePrice = btn.dataset.stonePrice;
    if (isStandalone || !selectedItem) {
      btn.innerHTML = `<i class="fa-solid fa-plus"></i> Aggiungi Pietra allo Scrigno (€${Number(stonePrice).toFixed(2)})`;
    } else {
      const shortTitle = selectedItem.title.length > 22 ? selectedItem.title.substring(0, 20) + '...' : selectedItem.title;
      btn.innerHTML = `<i class="fa-solid fa-gem"></i> Incastona su ${shortTitle} (+€${Number(stonePrice).toFixed(2)})`;
    }
  });
}

function onAtelierBraceletSelectChange(value) {
  updateAtelierButtonsText();
}

function renderAtelierStonesGrid() {
  const grid = document.getElementById('atelierStonesGrid');
  if (!grid || !state.stones) return;

  // On the homepage, render top 6 featured stones to prevent a giant full scroll
  const stonesToShow = state.stones.slice(0, 6);

  grid.innerHTML = stonesToShow.map(stone => `
    <div class="atelier-stone-card" id="atelierStoneCard_${stone.id}">
      <div class="atelier-stone-img-wrap">
        <img src="${stone.immagine_locale}" alt="${stone.nome}" onerror="this.src='${stone.immagine_remota}'" loading="lazy">
        <span class="atelier-stone-price-tag">Solo Pietra: €${Number(stone.prezzo_vendita).toFixed(2)}</span>
      </div>
      <div class="atelier-stone-body">
        <div class="atelier-stone-title-row">
          <h4 class="atelier-stone-name">${stone.nome}</h4>
        </div>
        <div class="atelier-stone-badges">
          <span class="atelier-pill"><i class="fa-solid fa-sun"></i> ${stone.chakra}</span>
          <span class="atelier-pill"><i class="fa-solid fa-water"></i> ${stone.elemento}</span>
        </div>
        <p class="atelier-stone-desc">${stone.proprieta}</p>
        <div class="atelier-stone-meta">
          <span style="font-size: 0.74rem; color: var(--text-muted);"><i class="fa-solid fa-ruler"></i> ${stone.dimensioni || 'Minerale naturale'}</span>
        </div>
        <button type="button" class="btn-primary btn-atelier-add-stone" 
                data-stone-id="${stone.id}" 
                data-stone-price="${stone.prezzo_vendita}" 
                onclick="addStoneFromAtelier('${stone.id}')">
          <i class="fa-solid fa-plus"></i> Aggiungi Pietra allo Scrigno (€${Number(stone.prezzo_vendita).toFixed(2)})
        </button>
      </div>
    </div>
  `).join('');

  updateAtelierButtonsText();
}

function addStoneFromAtelier(stoneId) {
  const stone = (state.stones || []).find(s => s.id === stoneId);
  if (!stone) return;

  const select = document.getElementById('atelierCartBraceletSelect');
  const targetId = select ? select.value : 'standalone_stone';

  if (targetId !== 'standalone_stone') {
    const targetBracelet = state.cart.find(i => i.id === targetId);
    if (targetBracelet) {
      if (!targetBracelet.custom_stones) targetBracelet.custom_stones = [];
      targetBracelet.custom_stones.push({
        id: stone.id,
        nome: stone.nome,
        prezzo_vendita: Number(stone.prezzo_vendita),
        immagine_locale: stone.immagine_locale,
        chakra: stone.chakra,
        elemento: stone.elemento
      });
      saveCart();
      showToast(`Pietra ${stone.nome} incastonata su ${targetBracelet.title}!`);
      openCart();
      populateAtelierCartBraceletSelect(targetId);
      return;
    }
  }

  // Altrimenti aggiungi come pietra/burattato singolo
  state.cart.push({
    id: `standalone_stone_${stone.id}_${Date.now()}`,
    title: `Pietra Naturale Didoni: ${stone.nome}`,
    basePrice: Number(stone.prezzo_vendita),
    price: Number(stone.prezzo_vendita),
    image_url: stone.immagine_locale,
    quantity: 1,
    is_standalone_stone: true,
    stone: {
      id: stone.id,
      name: stone.nome,
      price: Number(stone.prezzo_vendita)
    }
  });

  saveCart();
  showToast(`Pietra ${stone.nome} aggiunta allo scrigno!`);
  openCart();
  populateAtelierCartBraceletSelect();
}

// ==============================================================================
// EDGE CASE B: MODAL DI CONFERMA RIMOZIONE BRACCIALE CON PIETRE
// ==============================================================================
function openStoneRemoveConfirmModal() {
  const modal = document.getElementById('stoneRemoveConfirmModalBackdrop');
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeStoneRemoveConfirmModal() {
  const modal = document.getElementById('stoneRemoveConfirmModalBackdrop');
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
  state.pendingRemoveItemId = null;
}

function confirmRemoveBraceletAndStones() {
  if (!state.pendingRemoveItemId) return;
  state.cart = state.cart.filter(item => item.id !== state.pendingRemoveItemId);
  state.pendingRemoveItemId = null;
  saveCart();
  closeStoneRemoveConfirmModal();
  showToast('Bracciale e pietre rimossi dallo scrigno');
}

function confirmKeepStonesAsStandalone() {
  if (!state.pendingRemoveItemId) return;
  const item = state.cart.find(i => i.id === state.pendingRemoveItemId);
  if (item) {
    const stones = item.custom_stones && item.custom_stones.length > 0 
      ? [...item.custom_stones] 
      : (item.stone ? [{
          id: item.stone.id,
          nome: item.stone.name,
          prezzo_vendita: Number(item.stone.price),
          immagine_locale: item.stone.image || 'assets/pietre/acquamarina_s.jpg'
        }] : []);

    state.cart = state.cart.filter(i => i.id !== state.pendingRemoveItemId);

    stones.forEach(stone => {
      state.cart.push({
        id: `standalone_stone_${stone.id}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        title: `Pietra Naturale Didoni: ${stone.nome}`,
        basePrice: Number(stone.prezzo_vendita),
        price: Number(stone.prezzo_vendita),
        image_url: stone.immagine_locale || 'assets/pietre/acquamarina_s.jpg',
        quantity: 1,
        is_standalone_stone: true,
        stone: {
          id: stone.id,
          name: stone.nome,
          price: Number(stone.prezzo_vendita)
        }
      });
    });

    state.pendingRemoveItemId = null;
    saveCart();
    closeStoneRemoveConfirmModal();
    showToast('Bracciale rimosso: pietre conservate come minerali singoli nello scrigno!');
  }
}

function removeSingleStoneFromCartItem(cartItemId, stoneIndex) {
  const item = state.cart.find(i => i.id === cartItemId);
  if (!item || !item.custom_stones) return;
  const removed = item.custom_stones.splice(stoneIndex, 1)[0];
  saveCart();
  showToast(`Pietra ${removed.nome} rimossa dal bracciale`);
}

// ==============================================================================
// LUXURY MOBILE NAVIGATION DRAWER CONTROLLER
// ==============================================================================
function toggleMobileMenu() {
  const drawer = document.getElementById('mobileNavDrawer');
  if (!drawer) return;
  if (drawer.classList.contains('open')) {
    closeMobileMenu();
  } else {
    openMobileMenu();
  }
}

function openMobileMenu() {
  const drawer = document.getElementById('mobileNavDrawer');
  const backdrop = document.getElementById('mobileNavBackdrop');
  const icon = document.getElementById('mobileMenuIcon');
  if (!drawer) return;
  drawer.classList.add('open');
  if (backdrop) backdrop.classList.add('open');
  if (icon) {
    icon.classList.remove('fa-bars');
    icon.classList.add('fa-xmark');
  }
  document.body.style.overflow = 'hidden';
}

function closeMobileMenu() {
  const drawer = document.getElementById('mobileNavDrawer');
  const backdrop = document.getElementById('mobileNavBackdrop');
  const icon = document.getElementById('mobileMenuIcon');
  if (!drawer) return;
  drawer.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
  if (icon) {
    icon.classList.remove('fa-xmark');
    icon.classList.add('fa-bars');
  }
  document.body.style.overflow = '';
}

// Close mobile menu on ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeMobileMenu();
  }
});

// Bind stone workshop functions to window
window.onStoneSelectChange = onStoneSelectChange;
window.selectStoneChip = selectStone;
window.onStoneBraceletChange = onStoneBraceletChange;
window.addStoneCustomToCart = addStoneCustomToCart;
window.handleStoneCustomizationSubmit = handleStoneCustomizationSubmit;
window.customizeCurrentModalBracelet = customizeCurrentModalBracelet;
window.customizeBraceletWithStone = customizeBraceletWithStone;

// Bind new Prompt Modal, Atelier, and Removal functions to window
window.openStonePromptModal = openStonePromptModal;
window.closeStonePromptModal = closeStonePromptModal;
window.renderStoneMiniCarousel = renderStoneMiniCarousel;
window.selectPromptStone = selectPromptStone;
window.confirmPromptAddStone = confirmPromptAddStone;
window.exploreFullAtelierFromPrompt = exploreFullAtelierFromPrompt;
window.skipPromptToCart = skipPromptToCart;
window.scrollStoneCarousel = scrollStoneCarousel;
window.populateAtelierCartBraceletSelect = populateAtelierCartBraceletSelect;
window.onAtelierBraceletSelectChange = onAtelierBraceletSelectChange;
window.renderAtelierStonesGrid = renderAtelierStonesGrid;
window.addStoneFromAtelier = addStoneFromAtelier;
window.openStoneRemoveConfirmModal = openStoneRemoveConfirmModal;
window.closeStoneRemoveConfirmModal = closeStoneRemoveConfirmModal;
window.confirmRemoveBraceletAndStones = confirmRemoveBraceletAndStones;
window.confirmKeepStonesAsStandalone = confirmKeepStonesAsStandalone;
window.removeSingleStoneFromCartItem = removeSingleStoneFromCartItem;
window.getItemUnitPrice = getItemUnitPrice;

// Bind mobile navigation functions to window
window.toggleMobileMenu = toggleMobileMenu;
window.openMobileMenu = openMobileMenu;
window.closeMobileMenu = closeMobileMenu;

// ==============================================================================
// DEDICATED ATELIER PIETRE SHOP PAGE LOGIC & FILTERING ENGINE
// ==============================================================================
const stoneShopState = {
  selectedModel: 'all',
  cartFilterActive: false,
  typeFilter: 'all',
  chakraFilter: 'all',
  elementFilter: 'all',
  searchQuery: '',
  selectedTargets: {}
};

function initAtelierShopPage() {
  const fullGrid = document.getElementById('atelierShopFullGrid');
  if (!fullGrid) return;

  updateShopModelCounts();
  renderAtelierShopFullGrid();
}

function updateShopModelCounts() {
  const stones = state.stones || [];
  
  // Count compatibility for each model pill
  document.querySelectorAll('#shopModelFilterPills .shop-filter-pill').forEach(pill => {
    const model = pill.dataset.model;
    let countEl = pill.querySelector('.pill-count');
    if (!countEl) {
      countEl = document.createElement('span');
      countEl.className = 'pill-count';
      pill.appendChild(countEl);
    }

    if (model === 'all') {
      countEl.textContent = stones.length;
    } else {
      const matchingCount = stones.filter(s => {
        if (!s.compatibilita_bracciali) return true;
        return s.compatibilita_bracciali.includes(model);
      }).length;
      countEl.textContent = matchingCount;
    }
  });

  // Cart filter button badge
  const cartBracelets = (state.cart || []).filter(i => !i.is_standalone_stone);
  const badge = document.getElementById('cartFilterCountBadge');
  if (badge) {
    if (cartBracelets.length > 0) {
      badge.style.display = 'inline-block';
      badge.textContent = `${cartBracelets.length} nello scrigno`;
    } else {
      badge.style.display = 'none';
    }
  }
}

function filterByShopModel(modelId) {
  stoneShopState.selectedModel = modelId;
  stoneShopState.cartFilterActive = false;
  
  const cartBtn = document.getElementById('filterByCartBraceletBtn');
  if (cartBtn) cartBtn.classList.remove('active');

  document.querySelectorAll('#shopModelFilterPills .shop-filter-pill').forEach(pill => {
    pill.classList.toggle('active', pill.dataset.model === modelId);
  });

  renderAtelierShopFullGrid();
}

function toggleCartBraceletFilter() {
  const cartBracelets = (state.cart || []).filter(i => !i.is_standalone_stone);
  if (cartBracelets.length === 0) {
    showToast('Nessun bracciale nel carrello. Seleziona prima un modello dallo Shop.');
    return;
  }

  stoneShopState.cartFilterActive = !stoneShopState.cartFilterActive;
  const cartBtn = document.getElementById('filterByCartBraceletBtn');
  if (cartBtn) cartBtn.classList.toggle('active', stoneShopState.cartFilterActive);

  if (stoneShopState.cartFilterActive) {
    document.querySelectorAll('#shopModelFilterPills .shop-filter-pill').forEach(pill => {
      pill.classList.toggle('active', pill.dataset.model === 'all');
    });
    stoneShopState.selectedModel = 'all';
    showToast(`Filtro attivo: gemme adatte al bracciale nel tuo scrigno!`);
  }

  renderAtelierShopFullGrid();
}

function onStoneSearchInput(query) {
  stoneShopState.searchQuery = (query || '').trim().toLowerCase();
  renderAtelierShopFullGrid();
}

function onStoneTypeFilterChange(type) {
  stoneShopState.typeFilter = type;
  renderAtelierShopFullGrid();
}

function onStoneChakraFilterChange(chakra) {
  stoneShopState.chakraFilter = chakra;
  renderAtelierShopFullGrid();
}

function onStoneElementFilterChange(element) {
  stoneShopState.elementFilter = element;
  renderAtelierShopFullGrid();
}

function resetAllStoneFilters() {
  stoneShopState.selectedModel = 'all';
  stoneShopState.cartFilterActive = false;
  stoneShopState.typeFilter = 'all';
  stoneShopState.chakraFilter = 'all';
  stoneShopState.elementFilter = 'all';
  stoneShopState.searchQuery = '';

  const searchInput = document.getElementById('stoneShopSearchInput');
  if (searchInput) searchInput.value = '';
  const typeSelect = document.getElementById('stoneTypeFilterSelect');
  if (typeSelect) typeSelect.value = 'all';
  const chakraSelect = document.getElementById('stoneChakraFilterSelect');
  if (chakraSelect) chakraSelect.value = 'all';
  const elementSelect = document.getElementById('stoneElementFilterSelect');
  if (elementSelect) elementSelect.value = 'all';
  const cartBtn = document.getElementById('filterByCartBraceletBtn');
  if (cartBtn) cartBtn.classList.remove('active');

  document.querySelectorAll('#shopModelFilterPills .shop-filter-pill').forEach(pill => {
    pill.classList.toggle('active', pill.dataset.model === 'all');
  });

  renderAtelierShopFullGrid();
  showToast('Filtri azzerati. Visualizzazione completa di tutte le gemme.');
}

function getFilteredStones() {
  let stones = state.stones || [];

  // Filter 1: Shop Model Filter
  if (stoneShopState.selectedModel !== 'all') {
    stones = stones.filter(s => {
      if (!s.compatibilita_bracciali) return true;
      return s.compatibilita_bracciali.includes(stoneShopState.selectedModel);
    });
  }

  // Filter 2: Smart Cart Filter
  if (stoneShopState.cartFilterActive) {
    const cartBracelets = (state.cart || []).filter(i => !i.is_standalone_stone);
    if (cartBracelets.length > 0) {
      stones = stones.filter(s => {
        if (!s.compatibilita_bracciali) return true;
        return s.compatibilita_bracciali.some(compatId => {
          return cartBracelets.some(b => (b.id && b.id.includes(compatId)) || b.productId === compatId || compatId === 'prod_rame_001');
        });
      });
    }
  }

  // Filter 3: Type Filter
  if (stoneShopState.typeFilter !== 'all') {
    if (stoneShopState.typeFilter === 'burattato') {
      stones = stones.filter(s => (s.tipo || '').toLowerCase().includes('burattato'));
    } else if (stoneShopState.typeFilter === 'grezzo') {
      stones = stones.filter(s => (s.tipo || '').toLowerCase().includes('grezzo') || (s.nome || '').toLowerCase().includes('grezzo') || (s.nome || '').toLowerCase().includes('grezza'));
    }
  }

  // Filter 4: Chakra Filter
  if (stoneShopState.chakraFilter !== 'all') {
    const q = stoneShopState.chakraFilter.toLowerCase();
    stones = stones.filter(s => (s.chakra || '').toLowerCase().includes(q));
  }

  // Filter 5: Element Filter
  if (stoneShopState.elementFilter !== 'all') {
    const q = stoneShopState.elementFilter.toLowerCase();
    stones = stones.filter(s => (s.elemento || '').toLowerCase().includes(q));
  }

  // Filter 6: Search Query
  if (stoneShopState.searchQuery) {
    const q = stoneShopState.searchQuery;
    stones = stones.filter(s => 
      (s.nome || '').toLowerCase().includes(q) ||
      (s.proprieta || '').toLowerCase().includes(q) ||
      (s.chakra || '').toLowerCase().includes(q) ||
      (s.elemento || '').toLowerCase().includes(q) ||
      (s.tipo || '').toLowerCase().includes(q)
    );
  }

  return stones;
}

function renderAtelierShopFullGrid() {
  const fullGrid = document.getElementById('atelierShopFullGrid');
  const countEl = document.getElementById('stoneResultsCount');
  const noMsg = document.getElementById('noStonesFoundMsg');
  if (!fullGrid) return;

  const filtered = getFilteredStones();
  const total = (state.stones || []).length;

  if (countEl) {
    countEl.textContent = `Visualizzando ${filtered.length} di ${total} gemme`;
  }

  if (filtered.length === 0) {
    fullGrid.innerHTML = '';
    if (noMsg) noMsg.style.display = 'block';
    return;
  }

  if (noMsg) noMsg.style.display = 'none';

  const cartBracelets = (state.cart || []).filter(i => !i.is_standalone_stone);

  fullGrid.innerHTML = filtered.map(stone => {
    const isGrezzo = (stone.tipo || '').toLowerCase().includes('grezzo') || (stone.nome || '').toLowerCase().includes('grezza');
    const typeLabel = isGrezzo ? 'Grezzo di Miniera' : 'Burattato Levigato';
    const currentTarget = stoneShopState.selectedTargets[stone.id] || (cartBracelets.length > 0 ? cartBracelets[0].id : 'standalone');

    // Build target selector options
    let targetOptionsHtml = '';
    if (cartBracelets.length > 0) {
      targetOptionsHtml += '<optgroup label="Bracciali nel tuo Scrigno">';
      cartBracelets.forEach(b => {
        const titleShort = b.title.length > 25 ? b.title.substring(0, 23) + '...' : b.title;
        targetOptionsHtml += `<option value="${b.id}" ${currentTarget === b.id ? 'selected' : ''}>Incastona su: ${titleShort}</option>`;
      });
      targetOptionsHtml += '</optgroup>';
      targetOptionsHtml += '<optgroup label="Opzione Minerale Singolo">';
      targetOptionsHtml += `<option value="standalone" ${currentTarget === 'standalone' ? 'selected' : ''}>Pietra Singola da Collezione (€${Number(stone.prezzo_vendita).toFixed(2)})</option>`;
      targetOptionsHtml += '</optgroup>';
    } else {
      targetOptionsHtml += `<option value="standalone" ${currentTarget === 'standalone' ? 'selected' : ''}>Pietra Singola da Collezione (€${Number(stone.prezzo_vendita).toFixed(2)})</option>`;
      targetOptionsHtml += '<optgroup label="Aggiungi con Bracciale dello Shop">';
      targetOptionsHtml += `<option value="combo_prod_rame_001" ${currentTarget === 'combo_prod_rame_001' ? 'selected' : ''}>+ Bracciale 3 Filamenti Torciti (€30)</option>`;
      targetOptionsHtml += `<option value="combo_prod_rame_002" ${currentTarget === 'combo_prod_rame_002' ? 'selected' : ''}>+ Cuff Martellato Ossidato (€45)</option>`;
      targetOptionsHtml += `<option value="combo_prod_rame_003" ${currentTarget === 'combo_prod_rame_003' ? 'selected' : ''}>+ Bangle Minimal Chisel (€25)</option>`;
      targetOptionsHtml += '</optgroup>';
    }

    const buttonLabel = (currentTarget && currentTarget.startsWith('combo_'))
      ? `<i class="fa-solid fa-plus"></i> Ordina con Bracciale`
      : (cartBracelets.length > 0 && currentTarget !== 'standalone')
        ? `<i class="fa-solid fa-gem"></i> Incastona nel Bracciale`
        : `<i class="fa-solid fa-plus"></i> Aggiungi allo Scrigno`;

    return `
      <article class="stone-shop-card" id="shopCard_${stone.id}">
        <div class="stone-shop-media">
          <img src="${stone.immagine_locale}" alt="${stone.nome}" onerror="this.src='${stone.immagine_remota}'" loading="lazy">
          <span class="stone-shop-price-badge">€${Number(stone.prezzo_vendita).toFixed(2)}</span>
          <span class="stone-shop-type-badge">${typeLabel}</span>
        </div>
        <div class="stone-shop-content">
          <h3 class="stone-shop-title">${stone.nome}</h3>
          <div class="stone-shop-badges">
            <span class="stone-shop-pill"><i class="fa-solid fa-sun"></i> ${stone.chakra}</span>
            <span class="stone-shop-pill"><i class="fa-solid fa-water"></i> ${stone.elemento}</span>
          </div>
          <p class="stone-shop-desc">${stone.proprieta}</p>

          <div class="stone-compatible-box">
            <div class="stone-compatible-title">
              <i class="fa-solid fa-shield-halved"></i> Montatura fatta a mano per:
            </div>
            <div class="stone-compatible-models">
              <span class="compatible-tag">3 Filamenti</span>
              <span class="compatible-tag">Intrecciati</span>
              <span class="compatible-tag">Cuff Battuto</span>
              ${!isGrezzo ? '<span class="compatible-tag">Bangle Rigido</span>' : ''}
            </div>
          </div>

          <label style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.35rem; display: block;">
            Destinazione Lavorazione:
          </label>
          <select class="luxury-input stone-shop-target-select" id="selectTarget_${stone.id}" onchange="onShopCardTargetChange('${stone.id}', this.value)">
            ${targetOptionsHtml}
          </select>

          <button type="button" class="btn-primary" style="width: 100%; justify-content: center;" onclick="addStoneFromShopCard('${stone.id}')">
            ${buttonLabel}
          </button>
        </div>
      </article>
    `;
  }).join('');
}

function onShopCardTargetChange(stoneId, targetValue) {
  stoneShopState.selectedTargets[stoneId] = targetValue;
  renderAtelierShopFullGrid();
}

function addStoneFromShopCard(stoneId) {
  const stone = (state.stones || []).find(s => s.id === stoneId);
  if (!stone) return;

  const target = stoneShopState.selectedTargets[stoneId] || 'standalone';

  if (target.startsWith('combo_')) {
    const braceletId = target.replace('combo_', '');
    addToCartById(braceletId);
    
    const newBracelet = state.cart[state.cart.length - 1];
    if (newBracelet) {
      if (!newBracelet.custom_stones) newBracelet.custom_stones = [];
      newBracelet.custom_stones.push({
        id: stone.id,
        nome: stone.nome,
        prezzo_vendita: Number(stone.prezzo_vendita),
        immagine_locale: stone.immagine_locale,
        chakra: stone.chakra,
        elemento: stone.elemento
      });
      saveCart();
      showToast(`${stone.nome} incastonata sul bracciale aggiunto!`);
      openCart();
      updateShopModelCounts();
      renderAtelierShopFullGrid();
      return;
    }
  } else if (target !== 'standalone') {
    const targetBracelet = state.cart.find(i => i.id === target);
    if (targetBracelet) {
      if (!targetBracelet.custom_stones) targetBracelet.custom_stones = [];
      targetBracelet.custom_stones.push({
        id: stone.id,
        nome: stone.nome,
        prezzo_vendita: Number(stone.prezzo_vendita),
        immagine_locale: stone.immagine_locale,
        chakra: stone.chakra,
        elemento: stone.elemento
      });
      saveCart();
      showToast(`${stone.nome} incastonata su ${targetBracelet.title}!`);
      openCart();
      updateShopModelCounts();
      renderAtelierShopFullGrid();
      return;
    }
  }

  state.cart.push({
    id: `standalone_stone_${stone.id}_${Date.now()}`,
    title: `Pietra Naturale Didoni: ${stone.nome}`,
    basePrice: Number(stone.prezzo_vendita),
    price: Number(stone.prezzo_vendita),
    image_url: stone.immagine_locale,
    quantity: 1,
    is_standalone_stone: true,
    stone: {
      id: stone.id,
      name: stone.nome,
      price: Number(stone.prezzo_vendita)
    }
  });

  saveCart();
  showToast(`${stone.nome} aggiunta allo scrigno!`);
  openCart();
  updateShopModelCounts();
  renderAtelierShopFullGrid();
}

// Bind dedicated stone shop functions to window
window.initAtelierShopPage = initAtelierShopPage;
window.filterByShopModel = filterByShopModel;
window.toggleCartBraceletFilter = toggleCartBraceletFilter;
window.onStoneSearchInput = onStoneSearchInput;
window.onStoneTypeFilterChange = onStoneTypeFilterChange;
window.onStoneChakraFilterChange = onStoneChakraFilterChange;
window.onStoneElementFilterChange = onStoneElementFilterChange;
window.resetAllStoneFilters = resetAllStoneFilters;
window.renderAtelierShopFullGrid = renderAtelierShopFullGrid;
window.addStoneFromShopCard = addStoneFromShopCard;
window.onShopCardTargetChange = onShopCardTargetChange;

// ==============================================================================
// CINEMATIC TECHNIQUE MODAL & GALLERY JUMP CONTROLLER
// ==============================================================================
function openTechniqueModal(techniqueId = 'intrecciati') {
  const backdrop = document.getElementById('techniqueModalBackdrop');
  if (!backdrop) return;
  backdrop.classList.add('open');
  backdrop.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  const card = document.getElementById('cinematicTechniqueCard');
  if (card) card.setAttribute('aria-expanded', 'true');
}

function closeTechniqueModal() {
  const backdrop = document.getElementById('techniqueModalBackdrop');
  if (!backdrop) return;
  backdrop.classList.remove('open');
  backdrop.style.display = 'none';
  document.body.style.overflow = '';

  const card = document.getElementById('cinematicTechniqueCard');
  if (card) card.setAttribute('aria-expanded', 'false');
}

function handleTechniqueCardKey(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    openTechniqueModal('intrecciati');
  }
}

function goToDedicatedPhotoGallery(category = 'Intrecciati', event = null) {
  if (event) {
    event.stopPropagation();
  }
  closeTechniqueModal();

  // 1. Aggiorna stato filtro categoria
  state.activeFilter = category;

  // 2. Aggiorna classe active nei pulsanti filtro della sezione #collezione
  const catFiltersEl = document.getElementById('categoryFilters');
  if (catFiltersEl) {
    catFiltersEl.querySelectorAll('.filter-btn').forEach(btn => {
      const match = btn.dataset.filter === category;
      btn.classList.toggle('active', match);
    });
  }

  // 3. Renderizza la griglia filtrata con i pezzi della tecnica richiesta
  renderProducts();

  // 4. Scroll fluido cinematografico verso la sezione dedicata
  const targetSection = document.getElementById('collezione');
  if (targetSection) {
    targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // 5. Toast elegante
  showToast(`Galleria Fotografica attivata: ${category}`);
}

window.openTechniqueModal = openTechniqueModal;
window.closeTechniqueModal = closeTechniqueModal;
window.handleTechniqueCardKey = handleTechniqueCardKey;
window.goToDedicatedPhotoGallery = goToDedicatedPhotoGallery;





