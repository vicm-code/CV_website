/* ===================================================================
   script.js
   - Active nav & dynamic footer year
   - Masonry grid (3 columns desktop / 1 column mobile) + lazy loading
   - Lightbox (desktop) + accessibility (aria attributes)
   - Projects detail view
   - Mobile menu, scroll-hide sidebar, clickable logo, body scroll-lock
   - Artwork protection (right-click, drag, save shortcut, printscreen)
   =================================================================== */

const mobileQuery = window.matchMedia('(max-width: 768px)');
const PLACEHOLDER = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';
const DESKTOP_COLUMNS = 3;

let images = [];
let currentIndex = 0;

/* -------------------------
   Helpers
   ------------------------- */
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
}

function generateAltText(src) {
    if (!src) return 'Portfolio Artwork';
    const filename = src.split('/').pop().split('.')[0];
    return filename.replace(/^\d{4}_/, '').replace(/[_-]/g, ' ');
}

/* -------------------------
   Active navigation
   ------------------------- */
function setActiveNav() {
    if (window.location.protocol === 'file:') return;

    const normalizePath = path => {
        const normalized = `/${(path || '').split('/').filter(Boolean).join('/')}`;
        return normalized === '/' ? normalized : `${normalized}/`;
    };
    const current = normalizePath(window.location.pathname);
    const target = current.startsWith('/projecten/') && current !== '/projecten/'
        ? '/projecten/'
        : current;

    document.querySelectorAll('.nav-links li').forEach(li => {
        const link = li.querySelector('a');
        const linkPath = link ? normalizePath(new URL(link.href, window.location.origin).pathname) : '';
        li.classList.toggle('active', !!link && linkPath === target);
    });
}

/* -------------------------
   Lazy loading
   ------------------------- */
const lazyObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const img = entry.target;
        const done = () => img.classList.remove('lazy');
        img.addEventListener('load', done, { once: true });
        img.addEventListener('error', done, { once: true });
        img.src = img.dataset.src;
        observer.unobserve(img);
    });
}, { rootMargin: '200px 0px' });

function lazyLoadImages() {
    document.querySelectorAll('img.lazy').forEach(img => lazyObserver.observe(img));
}

/* -------------------------
   Lightbox
   ------------------------- */
const lightbox = document.getElementById('lightbox');
const lightboxImage = document.querySelector('.lightbox-image');

function showLightboxImage() {
    if (!lightboxImage || images.length === 0) return;
    const src = images[currentIndex];
    lightboxImage.src = src;
    lightboxImage.alt = generateAltText(src);
}

function openLightbox(index = 0) {
    if (!lightbox || !lightboxImage || lightbox.open) return;
    currentIndex = index;
    showLightboxImage();
    lightbox.showModal();
}

function closeLightbox() {
    if (lightbox?.open) lightbox.close();
}

function stepLightbox(direction) {
    if (images.length === 0) return;
    currentIndex = (currentIndex + direction + images.length) % images.length;
    showLightboxImage();
}

function initLightbox() {
    if (!lightbox || !lightboxImage || typeof lightbox.showModal !== 'function') return;

    lightbox.querySelector('.lightbox-close')?.addEventListener('click', closeLightbox);
    lightbox.querySelector('.lightbox-prev')?.addEventListener('click', () => stepLightbox(-1));
    lightbox.querySelector('.lightbox-next')?.addEventListener('click', () => stepLightbox(1));

    lightbox.addEventListener('click', e => {
        if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', e => {
        if (!lightbox.open) return;
        if (e.key === 'Escape') {
            closeLightbox();
            return;
        }
        if (e.key === 'ArrowRight') stepLightbox(1);
        if (e.key === 'ArrowLeft') stepLightbox(-1);
    });
}

function bindLightboxClicks(container) {
    if (!container) return;
    container.addEventListener('click', e => {
        const item = e.target.closest('.image-item');
        if (item && !mobileQuery.matches) openLightbox(Number(item.dataset.index));
    });
}

/* -------------------------
   Image grid (3 columns desktop / 1 column mobile)
   ------------------------- */
function createImageItem(src, index) {
    const item = document.createElement('div');
    item.className = 'image-item';
    item.dataset.index = index;

    const img = document.createElement('img');
    img.className = 'lazy';
    img.src = PLACEHOLDER;
    img.dataset.src = src;
    img.alt = generateAltText(src);

    item.appendChild(img);
    return item;
}

function buildGrid(container) {
    const isMobile = mobileQuery.matches;
    const numColumns = isMobile ? 1 : DESKTOP_COLUMNS;

    const columns = Array.from({ length: numColumns }, () => {
        const col = document.createElement('div');
        col.className = 'image-column';
        return col;
    });
    images.forEach((src, i) => columns[i % numColumns].appendChild(createImageItem(src, i)));

    lazyObserver.disconnect();
    container.replaceChildren(...columns);
    container.classList.toggle('mobile-view', isMobile);
    lazyLoadImages();
}

function initGrid() {
    const container = document.getElementById('image-grid-container');
    if (!container) return;

    images = Array.from(container.querySelectorAll('[data-src]'), el => el.dataset.src);

    buildGrid(container);
    bindLightboxClicks(container);
    mobileQuery.addEventListener('change', () => buildGrid(container));
}

/* -------------------------
   Projects detail view
   ------------------------- */
function setupProjectDetails() {
    const projectItems = document.querySelectorAll('.project-item');
    const detail = document.getElementById('project-detail');
    const intro = document.getElementById('projects-intro');
    const grid = document.querySelector('.projects-grid');
    if (!projectItems.length || !detail || !intro || !grid) return;

    projectItems.forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();

            const title = item.dataset.title || '';
            const text = item.dataset.text || '';
            images = (item.dataset.images || '').split(',').map(s => s.trim()).filter(Boolean);

            const imgsHtml = images.map((src, idx) => `
                <div class="image-item" data-index="${idx}">
                    <img class="lazy" data-src="${escapeHtml(src)}" alt="${escapeHtml(title)} - ${idx + 1}">
                </div>
            `).join('');

            detail.innerHTML = `
                <h2>${escapeHtml(title)}</h2>
                <p>${escapeHtml(text)}</p>
                <div class="image-grid project-images" id="project-detail-grid">${imgsHtml}</div>
                <button id="back-to-projects" class="back-button">← Terug naar projecten</button>
            `;
            detail.style.display = 'block';
            grid.style.display = 'none';
            intro.style.display = 'none';

            lazyLoadImages();
            bindLightboxClicks(detail.querySelector('#project-detail-grid'));

            detail.querySelector('#back-to-projects').addEventListener('click', () => {
                images = [];
                detail.style.display = 'none';
                grid.style.display = 'grid';
                intro.style.display = 'block';
                grid.scrollIntoView({ behavior: 'smooth' });
            });
        });
    });
}

/* -------------------------
   Sidebar: Menu toggle, logo, scroll-hide (Mobile)
   ------------------------- */
function setupSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.menu-toggle');
    const links = document.querySelector('.nav-links');

    // Mobile menu toggle & Body Scroll Lock
    if (toggle && links) {
        toggle.addEventListener('click', () => {
            const isOpen = links.classList.toggle('active');
            toggle.classList.toggle('active', isOpen);
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

            // Lock body scroll when mobile menu is open
            document.body.classList.toggle('menu-open', isOpen);
        });

        // Close menu when clicking a navigation link
        links.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                links.classList.remove('active');
                toggle.classList.remove('active');
                toggle.setAttribute('aria-expanded', 'false');
                document.body.classList.remove('menu-open');
            });
        });
    }

    if (!sidebar) return;

    // Scroll-Hide Sidebar behavior (Mobile only)
    const scrollThreshold = 50;
    let lastScrollTop = 0;

    const handleScroll = () => {
        // Do not hide header if mobile menu is actively open
        if (!mobileQuery.matches || links?.classList.contains('active')) {
            sidebar.classList.remove('hidden');
            return;
        }

        const scrollTop = window.scrollY || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
            sidebar.classList.add('hidden');
        } else if (scrollTop < lastScrollTop) {
            sidebar.classList.remove('hidden');
        }

        lastScrollTop = Math.max(scrollTop, 0);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    mobileQuery.addEventListener('change', () => {
        if (!mobileQuery.matches) {
            document.body.classList.remove('menu-open');
            sidebar.classList.remove('hidden');
        }
    });
}

function setupLocalDirectoryLinks() {
    if (window.location.protocol !== 'file:') return;

    document.querySelectorAll('a[href]').forEach(link => {
        const target = new URL(link.href, document.baseURI);
        if (target.protocol !== 'file:' || !target.pathname.endsWith('/')) return;

        target.pathname += 'index.html';
        link.href = target.href;
    });
}

/* -------------------------
   Artwork protection
   ------------------------- */
function enableArtworkProtection() {
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('dragstart', e => e.preventDefault());
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') e.preventDefault();
        if (e.key === 'PrintScreen') navigator.clipboard?.writeText('').catch(() => { });
    });
}

/* -------------------------
   Init
   ------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    const yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    setupLocalDirectoryLinks();
    setActiveNav();
    initGrid();
    initLightbox();
    setupProjectDetails();
    setupSidebar();
    enableArtworkProtection();
});