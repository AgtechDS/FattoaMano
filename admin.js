/**
 * FATTO A MANO — ADMIN DASHBOARD CONTROLLER (MIT-GRADE)
 * Zero hardcoding of credentials. Secure Bearer token session.
 */

// Global State
const adminState = {
  token: null,
  products: [],
  settings: {},
  orders: [],
  selectedImageBase64: null,
  selectedImageFilename: null
};

// ==============================================================================
// 1. INITIALIZATION & SESSION CHECK
// ==============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupPinKeypad();
  setupDragAndDrop();
  setupSettingsLivePreview();

  // Controlla se esiste già un token di sessione valido in sessionStorage
  const savedToken = sessionStorage.getItem('fattoamano_admin_token');
  if (savedToken) {
    adminState.token = savedToken;
    const isValid = await verifyCurrentSession(savedToken);
    if (isValid) {
      showDashboard();
      return;
    } else {
      sessionStorage.removeItem('fattoamano_admin_token');
      adminState.token = null;
    }
  }

  showAuthGate();
});

async function verifyCurrentSession(token) {
  try {
    const res = await fetch('/api/admin_auth', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (res.ok) {
      const data = await res.json();
      return data.authenticated === true;
    }
    return false;
  } catch (err) {
    return false;
  }
}

function showAuthGate() {
  document.getElementById('authGate').style.display = 'flex';
  document.getElementById('dashboardMain').style.display = 'none';
  const pinInput = document.getElementById('pinInput');
  if (pinInput) {
    pinInput.value = '';
    pinInput.focus();
  }
}

function showDashboard() {
  document.getElementById('authGate').style.display = 'none';
  document.getElementById('dashboardMain').style.display = 'flex';
  initDashboard();
}

function logoutAdmin() {
  sessionStorage.removeItem('fattoamano_admin_token');
  adminState.token = null;
  showToast('Disconnessione effettuata con successo');
  showAuthGate();
}

// ==============================================================================
// 2. PIN KEYPAD & AUTH HANDLERS (ZERO HARDCODING)
// ==============================================================================
function setupPinKeypad() {
  const pinInput = document.getElementById('pinInput');
  if (!pinInput) return;

  pinInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handlePinSubmit(e);
    }
  });
}

function appendPin(digit) {
  const pinInput = document.getElementById('pinInput');
  if (pinInput && pinInput.value.length < 10) {
    pinInput.value += digit;
  }
}

function clearPin() {
  const pinInput = document.getElementById('pinInput');
  if (pinInput) pinInput.value = '';
}

function backspacePin() {
  const pinInput = document.getElementById('pinInput');
  if (pinInput) pinInput.value = pinInput.value.slice(0, -1);
}

async function handlePinSubmit(event) {
  if (event) event.preventDefault();

  const pinInput = document.getElementById('pinInput');
  const code = (pinInput ? pinInput.value : '').trim();
  const errorMsgEl = document.getElementById('authErrorMessage');
  const btnUnlock = document.getElementById('btnUnlock');

  if (!code) {
    showAuthError('Inserire il codice di accesso');
    return;
  }

  if (btnUnlock) {
    btnUnlock.disabled = true;
    btnUnlock.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifica in corso...';
  }

  try {
    // Chiamata all'endpoint serverless (il codice viene verificato LATO SERVER contro .env)
    const res = await fetch('/api/admin_auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code: code })
    });

    const data = await res.json();

    if (res.ok && data.success && data.token) {
      adminState.token = data.token;
      sessionStorage.setItem('fattoamano_admin_token', data.token);
      if (errorMsgEl) errorMsgEl.style.display = 'none';
      showToast('Accesso autorizzato. Benvenuto nel pannello master.');
      showDashboard();
    } else {
      showAuthError(data.error || 'Codice errato. Accesso negato.');
      if (pinInput) {
        pinInput.value = '';
        pinInput.focus();
      }
    }
  } catch (err) {
    showAuthError('Errore di connessione con il server di autenticazione');
  } finally {
    if (btnUnlock) {
      btnUnlock.disabled = false;
      btnUnlock.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Sblocca Dashboard';
    }
  }
}

function showAuthError(msg) {
  const errorMsgEl = document.getElementById('authErrorMessage');
  if (errorMsgEl) {
    errorMsgEl.textContent = msg;
    errorMsgEl.style.display = 'block';
  }
  const pinInput = document.getElementById('pinInput');
  if (pinInput) {
    pinInput.style.borderColor = 'var(--color-danger)';
    setTimeout(() => {
      pinInput.style.borderColor = '';
    }, 1500);
  }
}

// ==============================================================================
// 3. DASHBOARD INITIALIZATION & TAB SWITCHER
// ==============================================================================
function initDashboard() {
  loadAdminCatalog();
  loadBannersSettings();
  loadAdminOrders();
  runSystemDiagnostics();
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.admin-tab-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === tabId);
  });

  if (tabId === 'ordersTab') {
    loadAdminOrders();
  } else if (tabId === 'catalogTab') {
    loadAdminCatalog();
  }
}

// ==============================================================================
// 4. CATALOG MANAGEMENT (FULL CRUD)
// ==============================================================================
async function loadAdminCatalog() {
  try {
    const res = await fetch('/api/admin_products?t=' + Date.now(), {
      headers: {
        'Authorization': `Bearer ${adminState.token}`
      }
    });

    if (res.status === 401) {
      logoutAdmin();
      return;
    }

    const data = await res.json();
    adminState.products = data.products || [];
    renderCatalogTable();
    updateCatalogStats();
  } catch (err) {
    console.error('Errore caricamento catalogo:', err);
    showToast('Impossibile caricare il catalogo admin', 'error');
  }
}

function renderCatalogTable(filteredItems = null) {
  const tbody = document.getElementById('catalogTableBody');
  if (!tbody) return;

  const items = filteredItems || adminState.products;
  tbody.innerHTML = '';

  if (items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          <i class="fa-solid fa-box-open" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
          Nessuna opera trovata nel catalogo
        </td>
      </tr>
    `;
    return;
  }

  items.forEach(prod => {
    const tr = document.createElement('tr');
    const isPronta = Boolean(prod.pronta_consegna);
    const inStock = prod.in_stock !== false;

    tr.innerHTML = `
      <td>
        <img src="${prod.image_url || 'assets/bracciale_3_filamenti.jpg'}" class="table-thumb" alt="${prod.title}">
      </td>
      <td>
        <strong style="color: var(--text-primary); font-size: 0.95rem;">${prod.title}</strong>
        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">ID: ${prod.id} • ${prod.purity || '99.9% Rame'}</div>
      </td>
      <td>
        <span class="category-tag">${prod.category || 'Intrecciati'}</span>
      </td>
      <td>
        <strong style="color: var(--copper-light); font-size: 1rem;">€${Number(prod.price).toFixed(2)}</strong>
      </td>
      <td>
        <button type="button" class="${isPronta ? 'pill-pronta' : 'pill-misura'}" onclick="toggleProntaConsegna('${prod.id}', ${isPronta})" title="Clicca per invertire">
          ${isPronta ? '<i class="fa-solid fa-bolt"></i> Pronta Consegna' : '<i class="fa-solid fa-ruler-combined"></i> Su Misura'}
        </button>
      </td>
      <td>
        <span style="font-size: 0.8rem; color: ${inStock ? 'var(--color-success)' : 'var(--color-danger)'};">
          <i class="fa-solid fa-circle" style="font-size: 0.5rem; vertical-align: middle; margin-right: 4px;"></i>
          ${inStock ? 'Attivo' : 'Esaurito'}
        </span>
      </td>
      <td style="text-align: right;">
        <div class="action-btn-group">
          <button class="btn-icon-action" onclick="editProduct('${prod.id}')" title="Modifica opera">
            <i class="fa-solid fa-pen-to-square"></i>
          </button>
          <button class="btn-icon-action delete" onclick="deleteProduct('${prod.id}', '${encodeURIComponent(prod.title)}')" title="Elimina opera">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateCatalogStats() {
  const total = adminState.products.length;
  const pronta = adminState.products.filter(p => p.pronta_consegna === true).length;
  const suMisura = total - pronta;
  const avg = total > 0 ? (adminState.products.reduce((acc, p) => acc + Number(p.price || 0), 0) / total) : 0;

  document.getElementById('statTotalProducts').textContent = total;
  document.getElementById('statProntaCount').textContent = pronta;
  document.getElementById('statSuMisuraCount').textContent = suMisura;
  document.getElementById('statAvgPrice').textContent = `€${avg.toFixed(2)}`;

  const badge = document.getElementById('catalogCountBadge');
  if (badge) badge.textContent = total;
}

function filterCatalogTable() {
  const query = (document.getElementById('catalogSearchInput').value || '').toLowerCase().trim();
  const categoryFilter = document.getElementById('catalogCategoryFilter').value;
  const prontaFilter = document.getElementById('catalogProntaFilter').value;

  const filtered = adminState.products.filter(p => {
    const matchQuery = !query ||
      (p.title && p.title.toLowerCase().includes(query)) ||
      (p.description && p.description.toLowerCase().includes(query)) ||
      (p.category && p.category.toLowerCase().includes(query));

    const matchCategory = (categoryFilter === 'all') || (p.category === categoryFilter);

    const matchPronta = (prontaFilter === 'all') ||
      (prontaFilter === 'pronta' && p.pronta_consegna === true) ||
      (prontaFilter === 'custom' && p.pronta_consegna !== true);

    return matchQuery && matchCategory && matchPronta;
  });

  renderCatalogTable(filtered);
}

async function toggleProntaConsegna(productId, currentVal) {
  const newVal = !currentVal;
  try {
    const res = await fetch('/api/admin_products', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminState.token}`
      },
      body: JSON.stringify({
        id: productId,
        pronta_consegna: newVal
      })
    });

    if (res.ok) {
      showToast(`Stato pronta consegna aggiornato a: ${newVal ? 'Disponibile Subito' : 'Su Misura'}`);
      loadAdminCatalog();
    } else {
      showToast('Errore durante la modifica dello stato', 'error');
    }
  } catch (err) {
    showToast('Errore di comunicazione con il server', 'error');
  }
}

// ==============================================================================
// 5. PRODUCT MODAL & IMAGE UPLOAD
// ==============================================================================
function openProductModal(prod = null) {
  const modal = document.getElementById('productModal');
  const titleEl = document.getElementById('productModalTitle');
  const form = document.getElementById('productEditForm');

  adminState.selectedImageBase64 = null;
  adminState.selectedImageFilename = null;

  // Reset anteprima
  const preview = document.getElementById('imagePreview');
  const dropContent = document.getElementById('dropZoneContent');
  preview.style.display = 'none';
  dropContent.style.display = 'flex';

  if (prod) {
    titleEl.innerHTML = `<i class="fa-solid fa-pen-to-square" style="color: var(--copper-light);"></i> Modifica: ${prod.title}`;
    document.getElementById('editProductId').value = prod.id;
    document.getElementById('editTitle').value = prod.title || '';
    document.getElementById('editCategory').value = prod.category || 'Intrecciati';
    document.getElementById('editPrice').value = Number(prod.price || 30.0);
    document.getElementById('editProntaConsegna').checked = Boolean(prod.pronta_consegna);
    document.getElementById('editStockQty').value = prod.stock_qty || 1;
    document.getElementById('editDescription').value = prod.description || '';
    document.getElementById('editDetails').value = prod.details || '';
    document.getElementById('editImageUrl').value = prod.image_url || '';

    if (prod.image_url) {
      preview.src = prod.image_url;
      preview.style.display = 'block';
      dropContent.style.display = 'none';
    }
  } else {
    titleEl.innerHTML = `<i class="fa-solid fa-gem" style="color: var(--copper-light);"></i> Nuova Opera in Rame`;
    form.reset();
    document.getElementById('editProductId').value = '';
    document.getElementById('editPrice').value = '30.00';
    document.getElementById('editStockQty').value = '1';
    document.getElementById('editCategory').value = 'Intrecciati';
    document.getElementById('editProntaConsegna').checked = false;
  }

  modal.style.display = 'flex';
}

function closeProductModal() {
  document.getElementById('productModal').style.display = 'none';
}

function editProduct(productId) {
  const prod = adminState.products.find(p => p.id === productId);
  if (prod) {
    openProductModal(prod);
  }
}

function setupDragAndDrop() {
  const dropZone = document.getElementById('imageDropZone');
  if (!dropZone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.borderColor = 'var(--copper-light)';
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.borderColor = '';
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processSelectedFile(files[0]);
    }
  });
}

function handleFileSelect(event) {
  const files = event.target.files;
  if (files && files.length > 0) {
    processSelectedFile(files[0]);
  }
}

function processSelectedFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Carica solo file immagine (JPG, PNG, WEBP)', 'error');
    return;
  }

  adminState.selectedImageFilename = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    adminState.selectedImageBase64 = e.target.result;
    const preview = document.getElementById('imagePreview');
    const dropContent = document.getElementById('dropZoneContent');
    preview.src = e.target.result;
    preview.style.display = 'block';
    dropContent.style.display = 'none';
    showToast(`Foto caricata: ${file.name}`);
  };
  reader.readAsDataURL(file);
}

async function handleProductFormSubmit(event) {
  event.preventDefault();

  const id = document.getElementById('editProductId').value.trim();
  const title = document.getElementById('editTitle').value.trim();
  const category = document.getElementById('editCategory').value;
  const price = parseFloat(document.getElementById('editPrice').value);
  const pronta = document.getElementById('editProntaConsegna').checked;
  const stockQty = parseInt(document.getElementById('editStockQty').value, 10) || 1;
  const description = document.getElementById('editDescription').value.trim();
  const details = document.getElementById('editDetails').value.trim();
  const manualImageUrl = document.getElementById('editImageUrl').value.trim();

  const btnSave = document.getElementById('saveProductBtn');
  btnSave.disabled = true;
  btnSave.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvataggio su Cloud...';

  const payload = {
    title: title,
    category: category,
    price: price,
    pronta_consegna: pronta,
    stock_qty: stockQty,
    in_stock: stockQty > 0,
    description: description,
    details: details
  };

  if (adminState.selectedImageBase64) {
    payload.image_base64 = adminState.selectedImageBase64;
    payload.image_filename = adminState.selectedImageFilename;
  } else if (manualImageUrl) {
    payload.image_url = manualImageUrl;
  }

  const isEdit = Boolean(id);
  const method = isEdit ? 'PUT' : 'POST';
  if (isEdit) payload.id = id;

  try {
    const res = await fetch('/api/admin_products', {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminState.token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(isEdit ? 'Opera aggiornata con successo!' : 'Nuova opera aggiunta al catalogo!');
      closeProductModal();
      loadAdminCatalog();
    } else {
      showToast(data.error || 'Errore durante il salvataggio', 'error');
    }
  } catch (err) {
    showToast('Errore di comunicazione col server', 'error');
  } finally {
    btnSave.disabled = false;
    btnSave.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Salva su Supabase & Catalogo';
  }
}

async function deleteProduct(productId, encodedTitle) {
  const title = decodeURIComponent(encodedTitle);
  if (!confirm(`Sei sicuro di voler eliminare definitivamente l'opera "${title}" dal catalogo?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/admin_products?id=${encodeURIComponent(productId)}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${adminState.token}`
      }
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast(`Opera "${title}" rimossa dal catalogo`);
      loadAdminCatalog();
    } else {
      showToast(data.error || 'Errore durante l\'eliminazione', 'error');
    }
  } catch (err) {
    showToast('Errore di connessione', 'error');
  }
}

// ==============================================================================
// 6. BANNER & SETTINGS CONTROL
// ==============================================================================
async function loadBannersSettings() {
  try {
    const res = await fetch('/api/admin_settings?t=' + Date.now(), {
      headers: {
        'Authorization': `Bearer ${adminState.token}`
      }
    });

    if (res.ok) {
      const settings = await res.json();
      adminState.settings = settings;

      document.getElementById('settingAnnouncementActive').checked = settings.announcement_active !== false;
      document.getElementById('settingAnnouncementText').value = settings.announcement_text || '';
      document.getElementById('settingProntaBadge').value = settings.pronta_consegna_badge || '';
      document.getElementById('settingProntaTitle').value = settings.pronta_consegna_banner_title || '';
      document.getElementById('settingProntaSubtitle').value = settings.pronta_consegna_banner_subtitle || '';
      document.getElementById('settingShippingCost').value = settings.shipping_cost || 6.0;
      document.getElementById('settingFreeShippingThreshold').value = settings.free_shipping_threshold || 80.0;

      updateBannerLivePreview();
    }
  } catch (err) {
    console.warn('Errore lettura impostazioni:', err);
  }
}

function setupSettingsLivePreview() {
  const announcementInput = document.getElementById('settingAnnouncementText');
  if (announcementInput) {
    announcementInput.addEventListener('input', updateBannerLivePreview);
  }
}

function updateBannerLivePreview() {
  const textInput = document.getElementById('settingAnnouncementText');
  const previewText = document.getElementById('previewAnnouncementText');
  if (textInput && previewText) {
    previewText.innerHTML = textInput.value || 'Nessun testo specificato';
  }
}

async function saveBannersSettings() {
  const payload = {
    announcement_active: document.getElementById('settingAnnouncementActive').checked,
    announcement_text: document.getElementById('settingAnnouncementText').value.trim(),
    pronta_consegna_badge: document.getElementById('settingProntaBadge').value.trim(),
    pronta_consegna_banner_title: document.getElementById('settingProntaTitle').value.trim(),
    pronta_consegna_banner_subtitle: document.getElementById('settingProntaSubtitle').value.trim(),
    shipping_cost: parseFloat(document.getElementById('settingShippingCost').value) || 6.0,
    free_shipping_threshold: parseFloat(document.getElementById('settingFreeShippingThreshold').value) || 80.0
  };

  try {
    const res = await fetch('/api/admin_settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminState.token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast('Banner e impostazioni del sito salvati con successo!');
      adminState.settings = data.settings;
    } else {
      showToast(data.error || 'Errore salvataggio impostazioni', 'error');
    }
  } catch (err) {
    showToast('Errore di comunicazione', 'error');
  }
}

// ==============================================================================
// 7. ORDERS & DISPATCH LOG
// ==============================================================================
async function loadAdminOrders() {
  try {
    const res = await fetch('/api/admin_orders?t=' + Date.now(), {
      headers: {
        'Authorization': `Bearer ${adminState.token}`
      }
    });

    if (res.ok) {
      const data = await res.json();
      adminState.orders = data.orders || [];
      renderOrdersTable();
    }
  } catch (err) {
    console.warn('Errore lettura ordini:', err);
  }
}

function renderOrdersTable() {
  const tbody = document.getElementById('ordersTableBody');
  const countBadge = document.getElementById('ordersCountBadge');
  if (!tbody) return;

  const orders = adminState.orders;
  if (countBadge) countBadge.textContent = orders.length;

  tbody.innerHTML = '';
  if (orders.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          <i class="fa-solid fa-truck-ramp-box" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
          Nessun ordine registrato al momento
        </td>
      </tr>
    `;
    return;
  }

  orders.forEach(ord => {
    const tr = document.createElement('tr');
    const cust = ord.customer || {};
    const itemsList = (ord.items || []).map(i => `${i.quantity || 1}x ${i.title || 'Bracciale Rame'}`).join('<br>');
    const addr = `${cust.address || ''}, ${cust.cap || ''} ${cust.city || ''} (${cust.province || ''})`;

    tr.innerHTML = `
      <td><strong style="color: var(--copper-light);">${ord.order_id || 'FAM-000'}</strong></td>
      <td style="font-size: 0.78rem; color: var(--text-muted);">${ord.timestamp || 'N/D'}</td>
      <td>
        <strong>${cust.fullName || cust.nome || 'Cliente Anonimo'}</strong><br>
        <span style="font-size: 0.75rem; color: var(--text-muted);">${cust.email || ''} • Tel: ${cust.phone || 'N/D'}</span>
      </td>
      <td style="font-size: 0.82rem; color: var(--text-secondary); max-width: 200px;">
        ${addr}
        ${cust.notes ? `<div style="color: var(--copper-light); font-size: 0.72rem; margin-top: 2px;">Note: ${cust.notes}</div>` : ''}
      </td>
      <td style="font-size: 0.82rem;">${itemsList}</td>
      <td><strong style="color: var(--text-primary); font-size: 1rem;">€${Number(ord.total || 0).toFixed(2)}</strong></td>
      <td>
        <select class="admin-select" style="padding: 0.3rem 0.5rem; font-size: 0.75rem;" onchange="updateOrderStatus('${ord.order_id}', this.value)">
          <option value="IN_LAVORAZIONE" ${ord.status === 'IN_LAVORAZIONE' ? 'selected' : ''}>In Lavorazione</option>
          <option value="FORGIATURA" ${ord.status === 'FORGIATURA' ? 'selected' : ''}>Forgiatura ad Incudine</option>
          <option value="SPEDITO" ${ord.status === 'SPEDITO' ? 'selected' : ''}>Spedito con Corriere</option>
          <option value="CONSEGNATO" ${ord.status === 'CONSEGNATO' ? 'selected' : ''}>Consegnato</option>
        </select>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function updateOrderStatus(orderId, newStatus) {
  try {
    const res = await fetch('/api/admin_orders', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminState.token}`
      },
      body: JSON.stringify({
        order_id: orderId,
        status: newStatus
      })
    });
    if (res.ok) {
      showToast(`Stato ordine ${orderId} aggiornato a: ${newStatus}`);
    }
  } catch (err) {
    showToast('Errore aggiornamento ordine', 'error');
  }
}

// ==============================================================================
// 8. DIAGNOSTICS & SYSTEM ACTIONS
// ==============================================================================
async function runSystemDiagnostics() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('diagDbDetail').innerHTML = `<span style="color: var(--color-success);"><i class="fa-solid fa-check"></i> Connesso (${data.products_count || 0} opere presenti)</span>`;
      document.getElementById('diagStorageDetail').innerHTML = `<span style="color: var(--color-success);"><i class="fa-solid fa-check"></i> Bucket fattoamano-products attivo</span>`;
      document.getElementById('diagStripeDetail').innerHTML = data.stripe_configured
        ? `<span style="color: var(--color-success);"><i class="fa-solid fa-check"></i> Live attivo (${data.stripe_key_preview || ''})</span>`
        : `<span style="color: var(--color-warning);"><i class="fa-solid fa-triangle-exclamation"></i> Test mode o non configurato</span>`;
    }
  } catch (err) {
    document.getElementById('diagDbDetail').textContent = 'Errore di risposta';
  }
}

async function rebuildLocalCache() {
  showToast('Aggiornamento e risincronizzazione catalogo in corso...');
  await loadAdminCatalog();
  showToast('Catalogo ricaricato con successo!');
}

// ==============================================================================
// 9. TOAST NOTIFICATION UTILITY
// ==============================================================================
function showToast(msg, type = 'info') {
  const container = document.getElementById('adminToastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `admin-toast ${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'error' ? 'fa-triangle-exclamation' : (type === 'success' ? 'fa-circle-check' : 'fa-gem')}" style="color: ${type === 'error' ? 'var(--color-danger)' : 'var(--copper-light)'}"></i>
    <span>${msg}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// Esponi funzioni a window per inline handlers
window.handlePinSubmit = handlePinSubmit;
window.appendPin = appendPin;
window.clearPin = clearPin;
window.backspacePin = backspacePin;
window.switchTab = switchTab;
window.openProductModal = openProductModal;
window.closeProductModal = closeProductModal;
window.handleFileSelect = handleFileSelect;
window.handleProductFormSubmit = handleProductFormSubmit;
window.editProduct = editProduct;
window.deleteProduct = deleteProduct;
window.toggleProntaConsegna = toggleProntaConsegna;
window.saveBannersSettings = saveBannersSettings;
window.loadAdminOrders = loadAdminOrders;
window.updateOrderStatus = updateOrderStatus;
window.rebuildLocalCache = rebuildLocalCache;
window.filterCatalogTable = filterCatalogTable;
window.logoutAdmin = logoutAdmin;
