// ============================================================
// Biblioteka — Frontend Application
// ============================================================

const API = '';

// Global configuration
let CONFIG = {
    currency: "RSD",
    language: "sr",
    currencies: {},
    languages: {},
    translations: {},
    library_name: "Biblioteka",
};

// Session timeout configuration (in minutes)
let SESSION_TIMEOUT_MINUTES = 30;
let SESSION_WARNING_MINUTES = 5;
let sessionTimeoutId;
let sessionWarningId;

// Load all public configuration from server
async function loadPublicConfig() {
    try {
        const res = await fetch(API + '/settings/public/config');
        if (res.ok) {
            const newConfig = await res.json();
            
            // Keep user's selected language from localStorage, don't override
            const savedLanguage = localStorage.getItem('selected_language');
            if (savedLanguage && savedLanguage !== newConfig.language) {
                newConfig.language = savedLanguage;
            }
            
            CONFIG = newConfig;
            
            // Save language selection for persistence
            if (!savedLanguage) {
                localStorage.setItem('selected_language', CONFIG.language);
            }
        }
        // Apply translations to all elements
        initI18n();
    } catch (e) {
        console.log('Could not load config, using defaults');
    }
}

// Load session configuration from server
async function loadSessionConfig() {
    try {
        const res = await fetch(API + '/auth/config');
        if (res.ok) {
            const config = await res.json();
            SESSION_TIMEOUT_MINUTES = config.session_timeout_minutes;
            SESSION_WARNING_MINUTES = config.session_warning_minutes;
        }
    } catch (e) {
        console.log('Could not load session config, using defaults');
    }
}

// Helper function to get translated text
function t(key) {
    if (!CONFIG.translations || !CONFIG.translations[key]) {
        return key;
    }
    return CONFIG.translations[key];
}

// Initialize i18n - replace all data-i18n elements with translated text
function initI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = t(key);
        
        if (el.tagName === 'INPUT') {
            if (el.type === 'button' || el.type === 'submit') {
                el.value = translated;
            }
        } else if (el.tagName === 'BUTTON' || el.tagName === 'A') {
            el.textContent = translated;
        } else {
            el.textContent = translated;
        }
    });
    
    // Handle placeholder translations
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });
}

// --- Session Management ---
function resetSessionTimer() {
    clearTimeout(sessionTimeoutId);
    clearTimeout(sessionWarningId);
    
    if (!getToken()) return;
    
    // Warning at 5 minutes before timeout
    sessionWarningId = setTimeout(() => {
        showSessionWarning();
    }, (SESSION_TIMEOUT_MINUTES - SESSION_WARNING_MINUTES) * 60 * 1000);
    
    // Logout after timeout
    sessionTimeoutId = setTimeout(() => {
        logout();
        showToast(t('session_expired'), 'warning');
    }, SESSION_TIMEOUT_MINUTES * 60 * 1000);
}

function showSessionWarning() {
    const warning = document.createElement('div');
    warning.id = 'session-warning';
    warning.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 4px;
        padding: 15px 20px;
        z-index: 9999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        max-width: 400px;
    `;
    warning.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 10px;">${t('session_expires_in')}: ${SESSION_WARNING_MINUTES} ${t('minutes')}</div>
        <p style="margin: 0 0 10px 0; font-size: 14px;">${t('session_inactive')}</p>
        <button onclick="resetSessionTimer(); document.getElementById('session-warning').remove();" style="padding: 8px 16px; background: #ffc107; border: none; border-radius: 3px; cursor: pointer; font-weight: 600;">${t('continue_session')}</button>
    `;
    document.body.appendChild(warning);
}

// --- Auth helpers ---
function getToken() {
    return localStorage.getItem('token');
}
function setToken(token) {
    localStorage.setItem('token', token);
}
function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}
function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}
function logout() {
    clearTimeout(sessionTimeoutId);
    clearTimeout(sessionWarningId);
    apiFetch('/auth/logout', { method: 'POST' }).finally(() => {
        localStorage.clear();
        window.location.href = '/login';
    });
}
function requireAuth() {
    if (!getToken()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Track user activity (only when logged in)
function setupActivityTracking() {
    document.addEventListener('mousemove', resetSessionTimer, true);
    document.addEventListener('keypress', resetSessionTimer, true);
    document.addEventListener('click', resetSessionTimer, true);
    document.addEventListener('scroll', resetSessionTimer, true);
}


// --- API Fetch wrapper ---
async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = { ...(options.headers || {}) };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(API + url, { ...options, headers });
    if (res.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
        return;
    }
    return res;
}

// --- Toast notifications ---
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// --- Modal helpers ---
function openModal(id) {
    document.getElementById(id).classList.add('active');
}
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// --- Format helpers ---
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('sr-Latn', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
function formatDateTime(dtStr) {
    if (!dtStr) return '-';
    const d = new Date(dtStr);
    return d.toLocaleDateString('sr-Latn', { day: '2-digit', month: '2-digit', year: 'numeric' }) +
        ' ' + d.toLocaleTimeString('sr-Latn', { hour: '2-digit', minute: '2-digit' });
}
function statusBadge(status) {
    return `<span class="badge badge-${status}">${status}</span>`;
}
function memberTypeName(type) {
    return t(type) || type;
}
function formatMoney(amount) {
    return `${amount} ${CONFIG.currency}`;
}

// --- Init sidebar ---
function initSidebar() {
    const user = getUser();
    if (!user) return;
    const nameEl = document.getElementById('sidebar-user-name');
    if (nameEl) nameEl.textContent = user.full_name;
    const roleEl = document.getElementById('sidebar-user-role');
    if (roleEl) roleEl.textContent = user.is_admin ? t('administrator') : t('librarian');

    // Active nav
    const path = window.location.pathname;
    document.querySelectorAll('.sidebar-nav a').forEach(a => {
        if (a.getAttribute('href') === path) a.classList.add('active');
    });

    // Load library name/logo
    apiFetch('/settings').then(r => r.json()).then(s => {
        const libName = document.getElementById('lib-name');
        if (libName && s.library_name) libName.textContent = s.library_name;
        const libLogo = document.getElementById('lib-logo');
        if (libLogo && s.library_logo_path) {
            libLogo.onload = () => { libLogo.style.display = ''; };
            libLogo.onerror = () => { libLogo.style.display = 'none'; };
            libLogo.src = s.library_logo_path + '?v=' + Date.now();
        }
    }).catch(() => {});
}

// ============================================================
// LOGIN PAGE
// ============================================================
function initLoginPage() {
    const form = document.getElementById('login-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const btn = form.querySelector('button');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>';

        try {
            const res = await fetch(API + '/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });
            const data = await res.json();
            if (res.ok) {
                setToken(data.access_token);
                setUser({ id: data.user_id, username: data.username, full_name: data.full_name, is_admin: data.is_admin });
                window.location.href = '/dashboard';
            } else {
                showToast(data.detail || t('login_error'), 'error');
            }
        } catch (err) {
            showToast(t('network_error'), 'error');
        }
        btn.disabled = false;
        btn.textContent = t('login_button');
    });
}

// ============================================================
// DASHBOARD PAGE
// ============================================================
async function initDashboard() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations
    initSidebar();

    try {
        const res = await apiFetch('/reports/dashboard');
        const data = await res.json();
        document.getElementById('stat-loans').textContent = data.active_loans || 0;
        document.getElementById('stat-expired').textContent = data.expired_memberships || 0;
        document.getElementById('stat-reservations').textContent = data.waiting_reservations || 0;
        document.getElementById('stat-books').textContent = data.total_copies || 0;
    } catch (e) {}

    try {
        const res = await apiFetch('/reports/activity?limit=30');
        const data = await res.json();
        const feed = document.getElementById('activity-feed');
        if (feed) {
            feed.innerHTML = data.map(a => `
                <li class="activity-item">
                    <div class="activity-dot"></div>
                    <div>
                        <div><strong>${a.user}</strong> — ${a.action} ${a.entity} ${a.new_values ? ': ' + truncate(a.new_values, 80) : ''}</div>
                        <div class="activity-time">${formatDateTime(a.created_at)}</div>
                    </div>
                </li>
            `).join('');
        }
    } catch (e) {}
}

function truncate(str, len) {
    if (!str) return '';
    if (typeof str !== 'string') str = JSON.stringify(str);
    return str.length > len ? str.slice(0, len) + '...' : str;
}

// ============================================================
// BOOKS PAGE
// ============================================================
let booksPage = 1;

async function initBooksPage() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations
    initSidebar();
    loadBooks();

    document.getElementById('book-search')?.addEventListener('input', debounce(() => {
        booksPage = 1;
        loadBooks();
    }, 300));

    document.getElementById('genre-filter')?.addEventListener('change', () => {
        booksPage = 1;
        loadBooks();
    });

    // Load genres for filter
    try {
        const res = await apiFetch('/books/genres');
        const genres = await res.json();
        const sel = document.getElementById('genre-filter');
        if (sel) {
            genres.forEach(g => {
                const opt = document.createElement('option');
                opt.value = g; opt.textContent = g;
                sel.appendChild(opt);
            });
        }
    } catch (e) {}
}

async function loadBooks() {
    const q = document.getElementById('book-search')?.value || '';
    const genre = document.getElementById('genre-filter')?.value || '';
    let url = `/books?page=${booksPage}&per_page=50`;
    if (q) url += `&q=${encodeURIComponent(q)}`;
    if (genre) url += `&genre=${encodeURIComponent(genre)}`;

    try {
        const res = await apiFetch(url);
        const books = await res.json();
        const tbody = document.getElementById('books-tbody');
        if (!tbody) return;
        tbody.innerHTML = books.map(b => `
            <tr onclick="openBookDetail(${b.id})">
                <td>${b.title}</td>
                <td>${b.author}</td>
                <td>${b.genre || '-'}</td>
                <td>${b.year_published || '-'}</td>
                <td style="text-align:center"><span style="color:${b.available_copies > 0 ? 'var(--success)' : 'var(--danger)'};font-weight:600">${b.available_copies}</span>/${b.total_copies}</td>
            </tr>
        `).join('');
        if (books.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-state">${t('no_results')}</td></tr>`;
        }
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function openBookDetail(bookId) {
    try {
        const res = await apiFetch(`/books/${bookId}`);
        const book = await res.json();

        document.getElementById('detail-book-title').textContent = book.title;
        document.getElementById('detail-book-author-sub').textContent = book.author || '-';
        document.getElementById('detail-book-publisher').textContent = book.publisher || '-';
        document.getElementById('detail-book-year').textContent = book.year_published || '-';
        document.getElementById('detail-book-genre').textContent = book.genre || '-';
        document.getElementById('detail-book-lang').textContent = book.language || '-';
        document.getElementById('detail-book-desc').textContent = book.description || '-';
        document.getElementById('detail-book-id').value = bookId;

        const copiesTbody = document.getElementById('copies-tbody');
        copiesTbody.innerHTML = book.copies.map(c => `
            <tr>
                <td>${c.library_number}</td>
                <td>${statusBadge(c.status)}</td>
                <td>${c.shelf_location || '-'}</td>
                <td>${c.condition}</td>
                <td>
                    ${c.status === 'available' ? `<button class="btn btn-primary btn-sm" onclick="openLoanModal(${c.id}, '${book.title}')">${t('issue')}</button>` : ''}
                </td>
            </tr>
        `).join('');

        openModal('book-detail-modal');
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function saveNewBook(e) {
    e.preventDefault();
    const data = {
        title: document.getElementById('new-book-title').value,
        author: document.getElementById('new-book-author').value,
        publisher: document.getElementById('new-book-publisher').value || null,
        year_published: parseInt(document.getElementById('new-book-year').value) || null,
        genre: document.getElementById('new-book-genre').value || null,
        language: document.getElementById('new-book-language').value || 'srpski',
        description: document.getElementById('new-book-desc').value || null,
    };
    try {
        const res = await apiFetch('/books', { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('book_added'));
            closeModal('new-book-modal');
            loadBooks();
            e.target.reset();
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

async function saveNewCopy(e) {
    e.preventDefault();
    const bookId = document.getElementById('detail-book-id').value;
    const data = {
        library_number: document.getElementById('new-copy-number').value,
        shelf_location: document.getElementById('new-copy-shelf').value || null,
        condition: document.getElementById('new-copy-condition').value,
        acquisition_type: document.getElementById('new-copy-acquisition').value,
    };
    try {
        const res = await apiFetch(`/books/${bookId}/copies`, { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('copy_added'));
            closeModal('new-copy-modal');
            openBookDetail(parseInt(bookId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

// --- Edit / Delete book ---
function openEditBookModal() {
    const bookId = document.getElementById('detail-book-id').value;
    const clean = id => { const v = document.getElementById(id).textContent; return v === '-' ? '' : v; };

    document.getElementById('edit-book-id').value = bookId;
    document.getElementById('edit-book-title').value = document.getElementById('detail-book-title').textContent;
    document.getElementById('edit-book-author').value = clean('detail-book-author-sub');
    document.getElementById('edit-book-publisher').value = clean('detail-book-publisher');
    document.getElementById('edit-book-year').value = clean('detail-book-year');
    document.getElementById('edit-book-genre').value = clean('detail-book-genre');
    document.getElementById('edit-book-lang').value = clean('detail-book-lang');
    document.getElementById('edit-book-desc').value = clean('detail-book-desc');

    closeModal('book-detail-modal');
    openModal('edit-book-modal');
}

async function saveEditBook(e) {
    e.preventDefault();
    const bookId = document.getElementById('edit-book-id').value;
    const data = {
        title: document.getElementById('edit-book-title').value,
        author: document.getElementById('edit-book-author').value,
        publisher: document.getElementById('edit-book-publisher').value || null,
        year_published: parseInt(document.getElementById('edit-book-year').value) || null,
        genre: document.getElementById('edit-book-genre').value || null,
        language: document.getElementById('edit-book-lang').value || 'srpski',
        description: document.getElementById('edit-book-desc').value || null,
    };
    try {
        const res = await apiFetch(`/books/${bookId}`, { method: 'PUT', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('book_saved') || 'Knjiga sačuvana');
            closeModal('edit-book-modal');
            loadBooks();
            openBookDetail(parseInt(bookId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

async function deleteBook() {
    const bookId = document.getElementById('edit-book-id').value;
    if (!confirm(t('confirm_delete'))) return;
    try {
        const res = await apiFetch(`/books/${bookId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast(t('book_deleted') || 'Knjiga obrisana');
            closeModal('edit-book-modal');
            loadBooks();
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

// --- Loan from book ---
async function openLoanModal(copyId, bookTitle) {
    document.getElementById('loan-copy-id').value = copyId;
    document.getElementById('loan-book-title').textContent = bookTitle;
    document.getElementById('loan-member-search').value = '';
    document.getElementById('loan-member-results').innerHTML = '';
    closeModal('book-detail-modal');
    openModal('loan-modal');
}

async function searchMembersForLoan() {
    const q = document.getElementById('loan-member-search').value;
    if (q.length < 2) return;
    const res = await apiFetch(`/members?q=${encodeURIComponent(q)}&per_page=10`);
    const members = await res.json();
    const div = document.getElementById('loan-member-results');
    div.innerHTML = members.map(m => `
        <div style="padding:8px;cursor:pointer;border-bottom:1px solid var(--border);"
             onclick="selectLoanMember(${m.id}, '${m.first_name} ${m.last_name}', '${m.member_number}')">
            <strong>${m.first_name} ${m.last_name}</strong> (${m.member_number})
        </div>
    `).join('');
}

function selectLoanMember(id, name, number) {
    document.getElementById('loan-member-id').value = id;
    document.getElementById('loan-member-search').value = `${name} (${number})`;
    document.getElementById('loan-member-results').innerHTML = '';
}

async function confirmLoan(e) {
    e.preventDefault();
    const copyId = parseInt(document.getElementById('loan-copy-id').value);
    const memberId = parseInt(document.getElementById('loan-member-id').value);
    if (!memberId) { showToast(t('select_member'), 'warning'); return; }
    try {
        const res = await apiFetch('/loans', {
            method: 'POST',
            body: JSON.stringify({ copy_id: copyId, member_id: memberId }),
        });
        if (res.ok) {
            const data = await res.json();
            showToast(`${t('issue_book')} — ${t('due_date')}: ${formatDate(data.due_date)}`);
            closeModal('loan-modal');
            loadBooks();
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

// ============================================================
// MEMBERS PAGE
// ============================================================
async function initMembersPage() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations
    initSidebar();
    loadMembers();

    document.getElementById('member-search')?.addEventListener('input', debounce(loadMembers, 300));
}

async function loadMembers() {
    const q = document.getElementById('member-search')?.value || '';
    let url = `/members?per_page=100`;
    if (q) url += `&q=${encodeURIComponent(q)}`;

    try {
        const res = await apiFetch(url);
        const members = await res.json();
        const tbody = document.getElementById('members-tbody');
        if (!tbody) return;
        tbody.innerHTML = members.map(m => {
            let statusBadgeHtml = '';
            let rowClass = '';
            
            if (m.is_blocked) {
                statusBadgeHtml = statusBadge('overdue');
            } else if (!m.last_membership) {
                statusBadgeHtml = statusBadge('not_paid');
            } else {
                const today = new Date();
                const validUntil = new Date(m.last_membership.valid_until);
                if (validUntil < today) {
                    statusBadgeHtml = statusBadge('expired');
                } else {
                    statusBadgeHtml = statusBadge('paid');
                    rowClass = 'style="background-color:rgba(76,175,80,0.1)"';
                }
            }
            return `
            <tr onclick="openMemberDetail(${m.id})" ${rowClass}>
                <td>${m.member_number}</td>
                <td>${m.first_name} ${m.last_name}</td>
                <td>${memberTypeName(m.member_type)}</td>
                <td>${m.email || '-'}</td>
                <td>${m.phone || '-'}</td>
                <td>${statusBadgeHtml}</td>
            </tr>
        `}).join('');
        if (members.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${t('no_results')}</td></tr>`;
        }
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function openMemberDetail(memberId) {
    try {
        const res = await apiFetch(`/members/${memberId}`);
        const m = await res.json();

        document.getElementById('detail-member-name').textContent = `${m.first_name} ${m.last_name}`;
        document.getElementById('detail-member-number').textContent = m.member_number;
        document.getElementById('detail-member-type').textContent = memberTypeName(m.member_type);
        document.getElementById('detail-member-email').textContent = m.email || '-';
        document.getElementById('detail-member-phone').textContent = m.phone || '-';
        document.getElementById('detail-member-address').textContent = m.address || '-';
        document.getElementById('detail-member-dob').textContent = formatDate(m.date_of_birth);
        document.getElementById('detail-member-status').innerHTML = m.is_blocked ?
            `<span class="badge badge-overdue">${t('blocked')}</span>` : `<span class="badge badge-active">${t('active')}</span>`;
        document.getElementById('detail-member-id').value = memberId;
        document.getElementById('detail-member-notifications').checked = m.allow_notifications;

        // Load loans - split into active and archive
        const loansRes = await apiFetch(`/members/${memberId}/loans`);
        const loans = await loansRes.json();
        const activeLoans = loans.filter(l => l.status === 'active' || l.status === 'overdue');
        const archivedLoans = loans.filter(l => l.status !== 'active' && l.status !== 'overdue');

        const loansTbody = document.getElementById('member-loans-tbody');
        loansTbody.innerHTML = activeLoans.length ? activeLoans.map(l => `
            <tr>
                <td>${l.book_title || '-'}</td>
                <td>${l.library_number || '-'}</td>
                <td>${formatDate(l.due_date)}</td>
                <td>${statusBadge(l.status)}</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="returnBook(${l.id})">${t('return')}</button>
                    <button class="btn btn-sm btn-secondary" onclick="extendLoan(${l.id})">${t('extend')}</button>
                </td>
            </tr>
        `).join('') : `<tr><td colspan="5" class="empty-state">${t('no_active_loans') || 'Nema aktivnih pozajmica'}</td></tr>`;

        const archiveTbody = document.getElementById('member-archive-tbody');
        archiveTbody.innerHTML = archivedLoans.length ? archivedLoans.map(l => `
            <tr>
                <td>${l.book_title || '-'}</td>
                <td>${l.library_number || '-'}</td>
                <td>${formatDate(l.loaned_at)}</td>
                <td>${formatDate(l.returned_at)}</td>
                <td>${statusBadge(l.status)}</td>
            </tr>
        `).join('') : `<tr><td colspan="5" class="empty-state">${t('no_results')}</td></tr>`;

        // Load memberships
        const memRes = await apiFetch(`/members/${memberId}/memberships`);
        const memberships = await memRes.json();
        const memTbody = document.getElementById('member-memberships-tbody');
        memTbody.innerHTML = memberships.length ? memberships.map(ms => `
            <tr>
                <td>${formatMoney(ms.amount_paid)}</td>
                <td>${formatDate(ms.paid_at)}</td>
                <td>${formatDate(ms.valid_from)}</td>
                <td>${formatDate(ms.valid_until)}</td>
            </tr>
        `).join('') : `<tr><td colspan="4" class="empty-state">${t('no_results')}</td></tr>`;

        openModal('member-detail-modal');
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function returnBook(loanId) {
    if (!confirm(t('confirm_delete'))) return;
    try {
        const res = await apiFetch(`/loans/${loanId}/return`, { method: 'POST' });
        if (res.ok) {
            showToast(t('loan_returned'));
            const memberId = document.getElementById('detail-member-id').value;
            openMemberDetail(parseInt(memberId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

async function extendLoan(loanId) {
    if (!confirm(t('confirm_delete'))) return;
    try {
        const res = await apiFetch(`/loans/${loanId}/extend`, { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            showToast(`${t('loan_extended')} — ${formatDate(data.new_due_date)}`);
            const memberId = document.getElementById('detail-member-id').value;
            openMemberDetail(parseInt(memberId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

async function saveNewMember(e) {
    e.preventDefault();
    const data = {
        member_number: parseInt(document.getElementById('new-member-number').value),
        first_name: document.getElementById('new-member-fname').value,
        last_name: document.getElementById('new-member-lname').value,
        date_of_birth: document.getElementById('new-member-dob').value || null,
        email: document.getElementById('new-member-email').value || null,
        phone: document.getElementById('new-member-phone').value || null,
        address: document.getElementById('new-member-address').value || null,
        member_type: document.getElementById('new-member-type').value,
        allow_notifications: document.getElementById('new-member-notifications').checked,
    };
    try {
        const res = await apiFetch('/members', { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('member_saved'));
            closeModal('new-member-modal');
            loadMembers();
            e.target.reset();
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

function calcMembershipDates() {
    const paidAt = document.getElementById('membership-paid-at').value;
    if (!paidAt) return;
    const d = new Date(paidAt);
    const validFrom = paidAt;
    let validUntil;
    if (CONFIG.membership_type === 'rolling') {
        const end = new Date(d);
        end.setDate(end.getDate() + 365);
        validUntil = end.toISOString().split('T')[0];
    } else {
        validUntil = `${d.getFullYear()}-12-31`;
    }
    document.getElementById('membership-valid-from').value = validFrom;
    document.getElementById('membership-valid-until').value = validUntil;
}

function openMembershipModal() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('membership-paid-at').value = today;
    document.getElementById('membership-amount').value = '';
    calcMembershipDates();
    openModal('membership-modal');
}

async function saveMembership(e) {
    e.preventDefault();
    const memberId = document.getElementById('detail-member-id').value;
    const paidAt = document.getElementById('membership-paid-at').value;
    const validFrom = document.getElementById('membership-valid-from').value;
    const validUntil = document.getElementById('membership-valid-until').value;

    if (!validFrom || !validUntil) {
        showToast(t('error'), 'error');
        return;
    }

    const data = {
        year: new Date(paidAt).getFullYear(),
        amount_paid: parseFloat(document.getElementById('membership-amount').value),
        paid_at: paidAt,
        valid_from: validFrom,
        valid_until: validUntil,
    };
    try {
        const res = await apiFetch(`/members/${memberId}/membership`, { method: 'POST', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('membership_saved'));
            closeModal('membership-modal');
            openMemberDetail(parseInt(memberId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

function openEditMemberModal() {
    const memberId = document.getElementById('detail-member-id').value;
    const memberNumber = document.getElementById('detail-member-number').textContent;
    const [fname, ...rest] = document.getElementById('detail-member-name').textContent.split(' ');
    const clean = id => { const v = document.getElementById(id).textContent; return v === '-' ? '' : v; };

    document.getElementById('edit-member-id').value = memberId;
    document.getElementById('edit-member-number').value = memberNumber.replace(/^Broj člana: /, '');
    document.getElementById('edit-member-fname').value = fname || '';
    document.getElementById('edit-member-lname').value = rest.join(' ') || '';
    document.getElementById('edit-member-dob').value = clean('detail-member-dob');
    document.getElementById('edit-member-type').value = document.getElementById('detail-member-type').textContent.toLowerCase();
    document.getElementById('edit-member-email').value = clean('detail-member-email');
    document.getElementById('edit-member-phone').value = clean('detail-member-phone');
    document.getElementById('edit-member-address').value = clean('detail-member-address');
    document.getElementById('edit-member-notifications').checked = document.getElementById('detail-member-notifications').checked;

    closeModal('member-detail-modal');
    openModal('edit-member-modal');
}

async function deleteMember() {
    const memberId = document.getElementById('edit-member-id').value;
    if (!confirm(t('confirm_delete'))) return;
    try {
        const res = await apiFetch(`/members/${memberId}`, { method: 'DELETE' });
        if (res.ok) {
            showToast(t('member_deleted') || 'Član obrisan');
            closeModal('edit-member-modal');
            loadMembers();
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

async function saveEditMember(e) {
    e.preventDefault();
    const memberId = document.getElementById('edit-member-id').value;
    const data = {
        member_number: parseInt(document.getElementById('edit-member-number').value),
        first_name: document.getElementById('edit-member-fname').value,
        last_name: document.getElementById('edit-member-lname').value,
        date_of_birth: document.getElementById('edit-member-dob').value || null,
        email: document.getElementById('edit-member-email').value || null,
        phone: document.getElementById('edit-member-phone').value || null,
        address: document.getElementById('edit-member-address').value || null,
        member_type: document.getElementById('edit-member-type').value,
        allow_notifications: document.getElementById('edit-member-notifications').checked,
    };
    try {
        const res = await apiFetch(`/members/${memberId}`, { method: 'PUT', body: JSON.stringify(data) });
        if (res.ok) {
            showToast(t('member_saved'));
            closeModal('edit-member-modal');
            loadMembers();
            openMemberDetail(parseInt(memberId));
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    } catch (e) {
        showToast(t('network_error'), 'error');
    }
}

// ============================================================
// RESERVATIONS PAGE
// ============================================================
async function initReservationsPage() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations
    initSidebar();
    loadReservations('active');
}

async function loadReservations(status = 'active') {
    // 'active' is frontend shorthand for waiting+notified combined
    let url = '/reservations';
    if (status && status !== 'active') url += `?status=${status}`;
    try {
        const res = await apiFetch(url);
        if (!res) return;
        const data = await res.json();
        const rows = status === 'active'
            ? data.filter(r => r.status === 'waiting' || r.status === 'notified')
            : data;
        const tbody = document.getElementById('reservations-tbody');
        if (!tbody) return;
        tbody.innerHTML = rows.map(r => `
            <tr>
                <td>${r.book_title || '-'}</td>
                <td>${r.member_name || '-'} (${r.member_number || ''})</td>
                <td>${r.queue_position}</td>
                <td>${statusBadge(r.status)}</td>
                <td>${formatDateTime(r.reserved_at)}</td>
                <td>
                    ${r.status === 'waiting' || r.status === 'notified' ?
                        `<button class="btn btn-sm btn-danger" onclick="cancelReservation(${r.id})">${t('cancel_reservation')}</button>` : ''}
                    ${r.status === 'notified' ?
                        `<button class="btn btn-sm btn-success" onclick="fulfillReservation(${r.id})">${t('fulfill_reservation')}</button>` : ''}
                </td>
            </tr>
        `).join('');
        if (rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${t('no_results')}</td></tr>`;
        }
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function cancelReservation(id) {
    if (!confirm(t('confirm_delete'))) return;
    const res = await apiFetch(`/reservations/${id}/cancel`, { method: 'POST' });
    const currentFilter = document.getElementById('reservation-filter')?.value || 'active';
    if (res && res.ok) { showToast(t('reservation_cancelled')); loadReservations(currentFilter); }
    else if (res) { const e = await res.json(); showToast(e.detail, 'error'); }
}

async function fulfillReservation(id) {
    const res = await apiFetch(`/reservations/${id}/fulfill`, { method: 'POST' });
    const currentFilter = document.getElementById('reservation-filter')?.value || 'active';
    if (res && res.ok) { showToast(t('reservation_fulfilled')); loadReservations(currentFilter); }
    else if (res) { const e = await res.json(); showToast(e.detail, 'error'); }
}

async function saveNewReservation(e) {
    e.preventDefault();
    const data = {
        book_id: parseInt(document.getElementById('res-book-id').value),
        member_id: parseInt(document.getElementById('res-member-id').value),
    };
    if (!data.book_id || !data.member_id) { showToast(t('select_member'), 'warning'); return; }
    const res = await apiFetch('/reservations', { method: 'POST', body: JSON.stringify(data) });
    if (res.ok) {
        showToast(t('reservation_created'));
        closeModal('new-reservation-modal');
        loadReservations();
    } else {
        const err = await res.json();
        showToast(err.detail, 'error');
    }
}

// ============================================================
// REPORTS PAGE
// ============================================================
async function initReportsPage() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations
    initSidebar();
    loadOverdueReport();
}

async function loadOverdueReport() {
    const res = await apiFetch('/reports/overdue');
    const data = await res.json();
    const tbody = document.getElementById('overdue-tbody');
    if (!tbody) return;
    tbody.innerHTML = data.map(r => `
        <tr>
            <td>${r.book_title || '-'}</td>
            <td>${r.library_number || '-'}</td>
            <td>${r.member_name || '-'}</td>
            <td>${r.member_number || '-'}</td>
            <td>${r.due_date}</td>
            <td><strong style="color:var(--danger)">${r.days_late} ${t('days')}</strong></td>
        </tr>
    `).join('');
    if (data.length === 0) tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${t('no_results')}</td></tr>`;
}

async function loadMembershipReport() {
    const year = document.getElementById('report-year')?.value || '';
    let url = '/reports/memberships';
    if (year) url += `?year=${year}`;
    const res = await apiFetch(url);
    const data = await res.json();
    const tbody = document.getElementById('membership-report-tbody');
    if (!tbody) return;
    document.getElementById('membership-total').textContent = `${formatMoney(data.total_amount)} (${data.count} ${t('payments')})`;
    tbody.innerHTML = data.memberships.map(m => `
        <tr>
            <td>${m.member_name || '-'}</td>
            <td>${m.member_number || '-'}</td>
            <td>${memberTypeName(m.member_type)}</td>
            <td>${formatMoney(m.amount_paid)}</td>
            <td>${m.paid_at}</td>
        </tr>
    `).join('');
}

async function loadPopularBooks() {
    const res = await apiFetch('/reports/popular-books?limit=20');
    const data = await res.json();
    const tbody = document.getElementById('popular-tbody');
    if (!tbody) return;
    tbody.innerHTML = data.map((b, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${b.title}</td>
            <td>${b.author}</td>
            <td><strong>${b.loan_count}</strong></td>
        </tr>
    `).join('');
}

async function loadExpiredMemberships() {
    const res = await apiFetch('/reports/expired-memberships');
    const data = await res.json();
    const tbody = document.getElementById('expired-tbody');
    if (!tbody) return;
    tbody.innerHTML = data.map(m => `
        <tr>
            <td>${m.member_name}</td>
            <td>${m.member_number}</td>
            <td>${memberTypeName(m.member_type)}</td>
            <td>${m.email || '-'}</td>
            <td>${m.last_valid_until}</td>
        </tr>
    `).join('');
}

function switchReportTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tab}"]`)?.classList.add('active');
    document.getElementById(`tab-${tab}`)?.classList.add('active');

    if (tab === 'overdue') loadOverdueReport();
    if (tab === 'memberships') loadMembershipReport();
    if (tab === 'popular') loadPopularBooks();
    if (tab === 'expired') loadExpiredMemberships();
}

async function exportReport(type) {
    let url = '';
    if (type === 'books') url = '/export/books';
    else if (type === 'members') url = '/export/members';
    else return;

    const res = await apiFetch(url);
    if (res.ok) {
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = type === 'books' ? 'knjige.xlsx' : 'clanovi.xlsx';
        a.click();
        showToast(t('success'));
    }
}

// ============================================================
// SETTINGS PAGE
// ============================================================
async function initSettingsPage() {
    if (!requireAuth()) return;
    await loadPublicConfig();  // Load language/config before rendering
    initI18n();  // Apply translations to page
    initSidebar();
    
    // Hide admin-only tabs for non-admin users
    const user = getUser();
    if (!user || !user.is_admin) {
        // Hide admin-only tabs
        const tabs = ['prices', 'import', 'backup', 'permissions'];
        tabs.forEach(tab => {
            const btn = document.querySelector(`[onclick="switchSettingsTab('${tab}')"]`);
            const div = document.getElementById(`stab-${tab}`);
            if (btn) btn.style.display = 'none';
            if (div) div.style.display = 'none';
        });
    }
    
    loadSettings();
    loadStaffList();
}

async function loadSettings() {
    const res = await apiFetch('/settings');
    const data = await res.json();

    document.getElementById('setting-library-name').value = data.library_name || '';
    document.getElementById('setting-loan-days').value = data.loan_duration_days || '30';
    document.getElementById('setting-currency').value = data.currency || 'RSD';
    document.getElementById('setting-language').value = data.language || 'sr';
    const membershipType = data.membership_type || 'calendar';
    const mtRadio = document.querySelector(`input[name="membership-type"][value="${membershipType}"]`);
    if (mtRadio) mtRadio.checked = true;
    
    // Update prices title with currency
    const pricesTitle = document.getElementById('prices-title');
    if (pricesTitle) {
        pricesTitle.textContent = `${t('membership_prices')} (${data.currency || 'RSD'})`;
    }
    
    document.getElementById('setting-email-host').value = data.email_smtp_host || '';
    document.getElementById('setting-email-port').value = data.email_smtp_port || '587';
    document.getElementById('setting-email-user').value = data.email_smtp_user || '';
    document.getElementById('setting-email-password').value = '';
    document.getElementById('setting-email-sender').value = data.email_sender_name || '';
    document.getElementById('setting-email-enabled').checked = data.email_enabled === 'true';

    // Membership prices
    try {
        const prices = JSON.parse(data.membership_prices || '{}');
        document.getElementById('price-djak').value = prices.djak || '';
        document.getElementById('price-student').value = prices.student || '';
        document.getElementById('price-odrasli').value = prices.odrasli || '';
        document.getElementById('price-penzioner').value = prices.penzioner || '';
        document.getElementById('price-institucija').value = prices.institucija || '';
    } catch (e) {}
}

async function saveSetting(key, value) {
    const res = await apiFetch('/settings', {
        method: 'PUT',
        body: JSON.stringify({ key, value }),
    });
    if (res.ok) showToast(t('saved'));
    else showToast(t('error'), 'error');
}

async function saveGeneralSettings() {
    await saveSetting('library_name', document.getElementById('setting-library-name').value);
    await saveSetting('loan_duration_days', document.getElementById('setting-loan-days').value);
    await saveSetting('currency', document.getElementById('setting-currency').value);
    const newLanguage = document.getElementById('setting-language').value;
    await saveSetting('language', newLanguage);
    const membershipType = document.querySelector('input[name="membership-type"]:checked')?.value || 'calendar';
    await saveSetting('membership_type', membershipType);
    
    // Save language selection to localStorage so it persists
    localStorage.setItem('selected_language', newLanguage);
    
    // Reload config from server to get new currency/settings
    await loadPublicConfig();
    
    // Apply new translations to all elements
    initI18n();
    
    // Show success message with translated text
    showToast(t('saved'), 'success');
}

async function saveEmailSettings() {
    await saveSetting('email_smtp_host', document.getElementById('setting-email-host').value);
    await saveSetting('email_smtp_port', document.getElementById('setting-email-port').value);
    await saveSetting('email_smtp_user', document.getElementById('setting-email-user').value);
    const pwd = document.getElementById('setting-email-password').value;
    if (pwd) await saveSetting('email_smtp_password', pwd);
    await saveSetting('email_sender_name', document.getElementById('setting-email-sender').value);
    await saveSetting('email_enabled', document.getElementById('setting-email-enabled').checked ? 'true' : 'false');
}

async function savePriceSettings() {
    const prices = {
        djak: parseInt(document.getElementById('price-djak').value) || 0,
        student: parseInt(document.getElementById('price-student').value) || 0,
        odrasli: parseInt(document.getElementById('price-odrasli').value) || 0,
        penzioner: parseInt(document.getElementById('price-penzioner').value) || 0,
        institucija: parseInt(document.getElementById('price-institucija').value) || 0,
    };
    await saveSetting('membership_prices', JSON.stringify(prices));
}

async function testEmail() {
    const email = prompt(t('email_address') + ':');
    if (!email) return;
    try {
        const res = await apiFetch('/settings/email/test', {
            method: 'POST',
            body: JSON.stringify({ to_email: email }),
        });
        if (res.ok) showToast(t('test_email_sent'));
        else { const e = await res.json(); showToast(e.detail, 'error'); }
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function uploadLogo() {
    const input = document.getElementById('logo-upload');
    if (!input.files[0]) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    const res = await apiFetch('/settings/logo', { method: 'POST', body: formData, headers: {} });
    if (res.ok) {
        showToast(t('saved'));
        location.reload();
    } else {
        showToast(t('error'), 'error');
    }
}

async function loadStaffList() {
    const res = await apiFetch('/auth/staff');
    if (!res.ok) {
        showToast(t('error'), 'error');
        return;
    }
    const staff = await res.json();
    const tbody = document.getElementById('staff-tbody');
    if (!tbody) return;
    
    if (!staff || staff.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">' + t('no_results') + '</td></tr>';
        return;
    }
    
    // Store for edit modal
    window._staffCache = {};
    staff.forEach(s => { window._staffCache[s.id] = s; });

    tbody.innerHTML = staff.map(s => `
        <tr>
            <td>${s.username}</td>
            <td>${s.full_name}</td>
            <td>${s.is_admin ? t('administrator') : t('librarian')}</td>
            <td>${s.is_active ? statusBadge('active') : statusBadge('inactive')}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="editStaff(${s.id})">${t('edit')}</button>
                <button class="btn btn-sm btn-danger" onclick="deleteStaff(${s.id})">${t('delete')}</button>
            </td>
        </tr>
    `).join('');
}

async function saveNewStaff(e) {
    e.preventDefault();
    const data = {
        username: document.getElementById('new-staff-username').value,
        full_name: document.getElementById('new-staff-name').value,
        password: document.getElementById('new-staff-password').value,
        is_admin: document.getElementById('new-staff-admin').checked,
    };
    const res = await apiFetch('/auth/staff', { method: 'POST', body: JSON.stringify(data) });
    if (res.ok) {
        showToast(t('user_created'));
        closeModal('new-staff-modal');
        loadStaffList();
    } else {
        const err = await res.json();
        showToast(err.detail, 'error');
    }
}

function editStaff(staffId) {
    const s = window._staffCache?.[staffId];
    if (!s) return;
    document.getElementById('edit-staff-id').value = s.id;
    document.getElementById('edit-staff-username').value = s.username;
    document.getElementById('edit-staff-name').value = s.full_name;
    document.getElementById('edit-staff-password').value = '';
    document.getElementById('edit-staff-admin').checked = s.is_admin;
    document.getElementById('edit-staff-active').checked = s.is_active;
    openModal('edit-staff-modal');
}

async function saveEditStaff(e) {
    e.preventDefault();
    const staffId = document.getElementById('edit-staff-id').value;
    const data = {
        full_name: document.getElementById('edit-staff-name').value,
        is_admin: document.getElementById('edit-staff-admin').checked,
        is_active: document.getElementById('edit-staff-active').checked,
    };
    const pwd = document.getElementById('edit-staff-password').value;
    if (pwd) data.password = pwd;

    const res = await apiFetch(`/auth/staff/${staffId}`, { method: 'PUT', body: JSON.stringify(data) });
    if (res && res.ok) {
        showToast(t('saved'));
        closeModal('edit-staff-modal');
        loadStaffList();
    } else if (res) {
        const err = await res.json();
        showToast(err.detail || t('error'), 'error');
    }
}

function deleteStaff(staffId) {
    const s = window._staffCache?.[staffId];
    const name = s ? s.full_name : '';
    if (confirm(`${t('confirm_delete')} — ${name}?`)) {
        // Soft delete: deactivate the account
        apiFetch(`/auth/staff/${staffId}`, {
            method: 'PUT',
            body: JSON.stringify({ is_active: false }),
        }).then(res => {
            if (res && res.ok) {
                showToast(t('success'));
                loadStaffList();
            } else {
                showToast(t('error'), 'error');
            }
        });
    }
}

// --- Permissions management ---
const MODULE_NAMES = {
    books: 'Knjige',
    members: 'Članovi',
    reservations: 'Rezervacije',
    reports: 'Izveštaji',
    settings: 'Podešavanja',
    finance: 'Finansije',
};

async function loadPermissionsTab() {
    const container = document.getElementById('permissions-staff-list');
    if (!container) return;
    try {
        const res = await apiFetch('/auth/staff');
        const staff = await res.json();
        const nonAdmins = staff.filter(s => !s.is_admin);
        if (nonAdmins.length === 0) {
            container.innerHTML = '<p style="color:var(--text-secondary)">Nema bibliotekara za podešavanje dozvola. Dodajte korisnika bez administratorske uloge.</p>';
            return;
        }
        container.innerHTML = nonAdmins.map(s => `
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px">
                <div>
                    <strong>${s.full_name}</strong>
                    <span style="color:var(--text-secondary);margin-left:8px">@${s.username}</span>
                    ${!s.is_active ? '<span class="badge badge-inactive" style="margin-left:8px">Neaktivan</span>' : ''}
                </div>
                <button class="btn btn-secondary btn-sm" onclick="openPermissionsModal(${s.id}, '${s.full_name.replace(/'/g, "\\'")}', '@${s.username}')">Dozvole</button>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p style="color:var(--danger)">Greška pri učitavanju.</p>';
    }
}

async function openPermissionsModal(userId, fullName, username) {
    document.getElementById('perm-user-id').value = userId;
    document.getElementById('perm-modal-title').textContent = fullName;
    document.getElementById('perm-modal-username').textContent = username;

    try {
        const res = await apiFetch(`/settings/permissions/${userId}`);
        const perms = await res.json();
        const permMap = {};
        perms.forEach(p => { permMap[p.module] = p; });

        document.getElementById('perm-tbody').innerHTML = Object.entries(MODULE_NAMES).map(([mod, name]) => {
            const p = permMap[mod] || { can_read: false, can_write: false };
            return `
            <tr>
                <td>${name}</td>
                <td style="text-align:center"><input type="checkbox" data-module="${mod}" data-ptype="read" ${p.can_read ? 'checked' : ''}></td>
                <td style="text-align:center"><input type="checkbox" data-module="${mod}" data-ptype="write" ${p.can_write ? 'checked' : ''}></td>
            </tr>`;
        }).join('');

        openModal('permissions-modal');
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function savePermissions() {
    const userId = parseInt(document.getElementById('perm-user-id').value);
    const rows = document.querySelectorAll('#perm-tbody tr');
    try {
        await Promise.all(Array.from(rows).map(row => {
            const mod = row.querySelector('[data-ptype="read"]').getAttribute('data-module');
            const canRead = row.querySelector('[data-ptype="read"]').checked;
            const canWrite = row.querySelector('[data-ptype="write"]').checked;
            return apiFetch('/settings/permissions', {
                method: 'PUT',
                body: JSON.stringify({ user_id: userId, module: mod, can_read: canRead, can_write: canWrite }),
            });
        }));
        showToast(t('saved'));
        closeModal('permissions-modal');
    } catch (e) {
        showToast(t('error'), 'error');
    }
}

async function backupNow() {
    const res = await apiFetch('/backup/now', { method: 'POST' });
    if (res.ok) showToast(t('backup_created'));
    else showToast(t('error'), 'error');
}

async function exportFullDB() {
    const res = await apiFetch('/backup/export-full', { method: 'POST' });
    if (res.ok) {
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'biblioteka_export.zip';
        a.click();
        showToast(t('success'));
    }
}

async function importFile(type) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx';
    input.onchange = async () => {
        const file = input.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        const res = await apiFetch(`/import/${type}`, { method: 'POST', body: formData, headers: {} });
        if (res.ok) {
            const data = await res.json();
            showToast(`${t('import_success')}: ${data.imported}`);
            if (data.errors?.length > 0) {
                console.log('Import errors:', data.errors);
            }
        } else {
            const err = await res.json();
            showToast(err.detail || t('error'), 'error');
        }
    };
    input.click();
}

async function downloadTemplate(type) {
    const res = await apiFetch(`/export/template/${type}`);
    if (res.ok) {
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `sablon_${type}.xlsx`;
        a.click();
    }
}

// --- Utility ---
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}
