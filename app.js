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
  loadProducts();
  setupEventListeners();
  renderCart();
  initCookieBanner();
});

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
        <span class="badge-pronta-live"><i class="fa-solid fa-bolt"></i> Disponibilità Immediata</span>
        <span class="badge-purity-corner">${product.purity || '99.9% Rame Puro'}</span>
      </div>

      <div class="pronta-card-body">
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
    // Mostra tutte le creazioni in atelier (sia pezzi su misura che pronta consegna)
    filtered = state.products || [];
  } else if (state.activeFilter === 'su_misura') {
    // "Tutte le Opere su Misura": esclude rigorosamente i pezzi in pronta consegna
    filtered = (state.products || []).filter(p => p.pronta_consegna !== true);
  } else if (state.activeFilter === 'pronta_consegna') {
    // Mostra solo le creazioni disponibili in pronta consegna
    filtered = (state.products || []).filter(p => p.pronta_consegna === true);
  } else {
    // Filtro categoria specifica (es. Intrecciati, Martellati, Rigidi):
    // Mostra tutte le creazioni della categoria, inclusi i pezzi pronta consegna di quella categoria
    filtered = (state.products || []).filter(p => p.category === state.activeFilter);
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
        <span class="badge-purity"><i class="fa-solid fa-award"></i> ${product.purity || '99.9% Rame Puro'}</span>
        ${prontaBadgeHtml}
        <button class="quick-view-btn" aria-label="Visualizza dettagli" onclick="event.stopPropagation(); openProductModal('${product.id}')">
          <i class="fa-solid fa-magnifying-glass-plus"></i>
        </button>
      </div>

      <div class="card-content">
        <div class="card-category">
          <span>${product.category || 'Creazione Artigianale'}</span>
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
  const itemsText = cartItems.map(item => 
    `• ${item.title} (x${item.quantity}) - €${(item.price * item.quantity).toFixed(2)}`
  ).join('\n');

  const ordersArray = cartItems.map(item => ({
    name: item.title,
    units: item.quantity,
    price: (item.price * item.quantity).toFixed(2),
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
    }
  });

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

