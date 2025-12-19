// ---------- helpers ----------
const CATEGORY_LABELS = {
    tshirt: 'Футболки',
    hoodie: 'Худи',
    shorts: 'Шорты',
    longsleeve: 'Лонгсливы',
    certificate: 'Сертификат'
};

function formatRub(amount) {
    if (typeof amount !== 'number') return '';
    return amount.toLocaleString('ru-RU');
}

function guessLocalFromRemote(remoteUrl) {
    try {
        const u = new URL(remoteUrl);
        const base = u.pathname.split('/').filter(Boolean).pop();
        if (!base) return null;
        return `images/${base}`;
    } catch {
        return null;
    }
}

function imageTag(remoteUrl, className, alt) {
    if (!remoteUrl) return '';
    const local = guessLocalFromRemote(remoteUrl);
    const safeAlt = (alt || '').replace(/\"/g, '');
    if (!local) {
        return `<img class="${className}" src="${remoteUrl}" alt="${safeAlt}" loading="lazy">`;
    }
    return `<img class="${className}" src="${local}" data-fallback="${remoteUrl}" alt="${safeAlt}" loading="lazy" onerror="this.onerror=null;this.src=this.dataset.fallback;">`;
}

// ---------- navigation ----------
const menuToggle = document.getElementById('menuToggle');
const navMenu = document.getElementById('navMenu');

menuToggle?.addEventListener('click', () => navMenu?.classList.toggle('active'));
document.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', () => navMenu?.classList.remove('active')));

// Smooth scroll with offset for navbar
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (!href || href === '#') return;
        const target = document.querySelector(href);
        if (!target) return;
        e.preventDefault();
        const offsetTop = target.getBoundingClientRect().top + window.pageYOffset - 90;
        window.scrollTo({ top: offsetTop, behavior: 'smooth' });
    });
});

// ---------- hero stats ----------
function animateCounter(element, target, duration = 1200) {
    const startValue = 0;
    const startTime = performance.now();
    const to = Math.max(0, Number(target || 0));

    function tick(now) {
        const t = Math.min(1, (now - startTime) / duration);
        const eased = 1 - Math.pow(1 - t, 3);
        const val = Math.floor(startValue + (to - startValue) * eased);
        element.textContent = String(val);
        if (t < 1) requestAnimationFrame(tick);
        else element.textContent = String(to);
    }

    requestAnimationFrame(tick);
}

function setHeroStats({ totalProducts, totalCategories }) {
    const stats = document.querySelectorAll('.hero-stats .stat-number');
    if (stats.length >= 1) stats[0].setAttribute('data-target', String(totalProducts));
    if (stats.length >= 2) stats[1].setAttribute('data-target', String(totalCategories));
    if (stats.length >= 3) stats[2].setAttribute('data-target', '100');

    stats.forEach(stat => {
        const target = parseInt(stat.getAttribute('data-target') || '0', 10);
        stat.textContent = '0';
        animateCounter(stat, target);
    });
}

// ---------- catalog ----------
let CATALOG = [];
let ACTIVE_FILTER = 'all';

function isCertificate(p) {
    const title = (p?.title || '').toLowerCase();
    const sku = (p?.sku || '').toLowerCase();
    return p?.category === 'certificate' || sku === 'gift' || title.includes('сертификат');
}

async function loadCatalog() {
    try {
        // Try absolute path first (for Vercel), then relative
        const paths = ['/catalog.json', './catalog.json', 'catalog.json'];
        let lastError = null;
        
        for (const path of paths) {
            try {
                const res = await fetch(path, { cache: 'no-store' });
                if (!res.ok) {
                    lastError = new Error(`Failed to load ${path}: ${res.status} ${res.statusText}`);
                    continue;
                }
                const data = await res.json();
                if (!Array.isArray(data)) {
                    lastError = new Error(`${path} is not an array`);
                    continue;
                }
                console.log(`Loaded ${data.length} products from ${path}`);
                return data;
            } catch (e) {
                lastError = e;
                continue;
            }
        }
        throw lastError || new Error('Failed to load catalog from all paths');
    } catch (e) {
        console.error('Catalog load error:', e);
        throw e;
    }
}

function buildFilters(items) {
    // По просьбе: вместо "Футболки" делаем "Сертификат" (фильтр),
    // а футболки остаются только в "Весь каталог".
    const order = ['certificate', 'hoodie', 'shorts', 'longsleeve'];
    const cats = Array.from(new Set(items.map(p => p.category).filter(Boolean)));
    // Сертификат показываем как фильтр, даже если он размечен как tshirt в данных
    const normalizedCats = new Set(cats);
    if (items.some(isCertificate)) normalizedCats.add('certificate');
    const sortedCats = order.filter(c => normalizedCats.has(c));
    const filterButtons = document.getElementById('filterButtons');
    if (!filterButtons) return;

    const buttons = [
        { id: 'all', label: 'Весь каталог' },
        ...sortedCats.map(c => ({ id: c, label: CATEGORY_LABELS[c] || c }))
    ];

    filterButtons.innerHTML = buttons.map(b => `
        <button class="filter-btn ${b.id === 'all' ? 'active' : ''}" data-filter="${b.id}">
            <span>${b.label}</span>
            <div class="btn-bg"></div>
        </button>
    `).join('');

    filterButtons.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            ACTIVE_FILTER = btn.getAttribute('data-filter') || 'all';
            renderProducts();
        });
    });
}

function filteredCatalog() {
    if (ACTIVE_FILTER === 'all') return CATALOG;
    // Сертификат должен быть виден во всех категориях
    const certs = CATALOG.filter(isCertificate);
    if (ACTIVE_FILTER === 'certificate') return certs;

    const filtered = CATALOG.filter(p => p.category === ACTIVE_FILTER);
    const byId = new Map();
    for (const p of [...filtered, ...certs]) {
        if (p?.id) byId.set(p.id, p);
    }
    return Array.from(byId.values());
}

function renderProducts() {
    const grid = document.getElementById('productsGrid');
    if (!grid) return;
    const items = filteredCatalog();
    grid.innerHTML = '';

    items.forEach((p, idx) => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.animationDelay = `${idx * 0.03}s`;

        const title = p.title || p.sku || 'Товар';
        const categoryLabel = CATEGORY_LABELS[p.category] || p.category || '';
        const cur = typeof p.price_current === 'number' ? p.price_current : null;
        const old = typeof p.price_old === 'number' ? p.price_old : null;

        const front = p.images?.front || null;
        const back = p.images?.back || null;
        const badge = p.badge ? `<div class="product-badge">${p.badge}</div>` : '';
        const hasBack = Boolean(back);

        const priceHtml = `
            <div class="product-prices">
                <div class="price-current">${cur ? `${formatRub(cur)} р.` : ''}</div>
                ${old ? `<div class="price-old">${formatRub(old)} р.</div>` : ''}
            </div>
        `;

        if (hasBack) card.classList.add('has-back');
        card.innerHTML = `
            <div class="product-media">
                ${badge}
                ${imageTag(front, 'product-image product-image-front', title)}
                ${back ? imageTag(back, 'product-image product-image-back', title) : ''}
            </div>
            <div class="product-info">
                <h3 class="product-title">${title}</h3>
                <p class="product-category">${categoryLabel}</p>
                ${priceHtml}
            </div>
        `;

        card.addEventListener('click', () => openModal(p));
        grid.appendChild(card);
    });

    // animate on scroll
    document.querySelectorAll('.product-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        scrollObserver.observe(el);
    });
}

// ---------- modal ----------
const modal = document.getElementById('productModal');
const modalImage = document.getElementById('modalImage');
const modalTitle = document.getElementById('modalTitle');
const modalDescription = document.getElementById('modalDescription');
const modalClose = document.querySelector('.modal-close');

function openModal(p) {
    if (!modal) return;
    const title = p.title || p.sku || 'Товар';
    const categoryLabel = CATEGORY_LABELS[p.category] || p.category || '';
    const cur = typeof p.price_current === 'number' ? p.price_current : null;
    const old = typeof p.price_old === 'number' ? p.price_old : null;
    const front = p.images?.front || null;

    modalTitle.textContent = title;
    modalDescription.innerHTML = `
        <div class="modal-meta">${categoryLabel}</div>
        <div class="modal-prices">
            <div class="price-current">${cur ? `${formatRub(cur)} р.` : ''}</div>
            ${old ? `<div class="price-old">${formatRub(old)} р.</div>` : ''}
        </div>
    `;

    // set modal image with local->remote fallback
    if (modalImage) {
        if (!front) {
            modalImage.removeAttribute('src');
        } else {
            const local = guessLocalFromRemote(front);
            if (!local) {
                modalImage.src = front;
            } else {
                modalImage.src = local;
                modalImage.onerror = () => {
                    modalImage.onerror = null;
                    modalImage.src = front;
                };
            }
        }
    }

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    if (!modal) return;
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

modalClose?.addEventListener('click', closeModal);
modal?.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

// ---------- navbar scroll effect ----------
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (!navbar) return;
    const y = window.pageYOffset;
    navbar.style.boxShadow = y <= 0 ? 'none' : '0 10px 30px rgba(0, 0, 0, 0.8)';
    navbar.style.background = y <= 0 ? 'rgba(0, 0, 0, 0.8)' : 'rgba(0, 0, 0, 0.95)';
});

// ---------- intersection observer for scroll animations ----------
const scrollObserverOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        scrollObserver.unobserve(entry.target);
    });
}, scrollObserverOptions);

// ---------- init ----------
document.addEventListener('DOMContentLoaded', async () => {
    try {
        CATALOG = await loadCatalog();
        buildFilters(CATALOG);
        renderProducts();

        const uniqueCategories = new Set(CATALOG.map(p => p.category).filter(Boolean));
        setHeroStats({ totalProducts: CATALOG.length, totalCategories: uniqueCategories.size });
    } catch (e) {
        console.error('Failed to load catalog:', e);
        setHeroStats({ totalProducts: 0, totalCategories: 0 });
    }
});
