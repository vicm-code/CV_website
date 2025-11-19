/* ===================================================================
   script.js — merged & optimized (behavior preserved)
   - Active nav
   - Image sets per page (schetsen / illustraties)
   - Desktop (masonry-like) and mobile grid generation
   - Lazy loading with IntersectionObserver (clean reconnect on regen)
   - Lightbox (open/close, prev/next, keyboard, background click)
   - Project detail view (projects page)
   - Contact form submit (fetch to FormSubmit.co)
   - Mobile menu toggle
   - Sidebar logo redirect
   - Scroll-hide sidebar on mobile
   - Artwork protection (right-click, drag, save shortcuts, CSS)
   =================================================================== */

/* -------------------------
   Active navigation helper
   ------------------------- */
function setActiveNav() {
    const file = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        const li = link.parentElement;
        if (!li) return;
        li.classList.toggle('active', link.getAttribute('href') === file);
    });
}

/* -------------------------
   Choose images for page
   ------------------------- */
let images = [];
const currentPage = window.location.pathname.split('/').pop();

if (currentPage === 'schetsen.html') {
    images = [
        'images/schetsen/2025_IMG_9626_2025.jpg',
        'images/schetsen/2025_IMG_9623_2025.jpg',
        'images/schetsen/2025_IMG_9622_2025.jpg',
        'images/schetsen/2025_IMG_9577_2025.jpg',
        'images/schetsen/2025_IMG_9576_2025.jpg',
        'images/schetsen/2025_IMG_9575_2025.jpg',
        'images/schetsen/2025_IMG_9571_2025.jpg',
        'images/schetsen/2025_IMG_20250902_0020.jpg',
        'images/schetsen/2025_IMG_20250902_0019.jpg',
        'images/schetsen/2025_IMG_20250902_0018.jpg',
        'images/schetsen/2025_IMG_20250902_0017.jpg',
        'images/schetsen/2025_IMG_20250902_0015.jpg',
        'images/schetsen/2025_IMG_20250902_0003.jpg',
        'images/schetsen/2025_IMG_20250902_0003 copy.jpg',
        'images/schetsen/2025_IMG_20250902_0002.jpg',
        'images/schetsen/2025_IMG_20250902_0001.jpg',
        'images/schetsen/2025_IMG_20250902_0001 copy.jpg',
        'images/schetsen/2025_IMG_20250902_0001 copy 4.jpg',
        'images/schetsen/2023_05.jpg',
        'images/schetsen/2023_04.jpg',
        'images/schetsen/2023_03.jpg',
        'images/schetsen/2023_02.jpg',
        'images/schetsen/2023_01.jpg',
        'images/schetsen/2022_07.jpg',
        'images/schetsen/2022_06.jpg',
        'images/schetsen/2022_05.jpg',
        'images/schetsen/2022_04.jpg',
        'images/schetsen/2022_03.jpg',
        'images/schetsen/2022_02.jpg',
        'images/schetsen/2022_01jpg.jpg',
        'images/schetsen/2022.10.23_zee.jpg',
        'images/schetsen/2021_02.jpg',
        'images/schetsen/2021_01.jpg',
        'images/schetsen/2020_blind tekenen7.jpg',
        'images/schetsen/2020_blind tekenen6.jpg',
        'images/schetsen/2020_blind tekenen2.jpg',
        'images/schetsen/2020_blind tekenen1.jpg',
        'images/schetsen/2020_12.jpg',
        'images/schetsen/2020_11.jpg',
        'images/schetsen/2020_10.jpg',
        'images/schetsen/2020_09.jpg',
        'images/schetsen/2020_08.jpg',
        'images/schetsen/2020_07.jpg',
        'images/schetsen/2020_06.jpg',
        'images/schetsen/2020_05.jpg',
        'images/schetsen/2020_04.jpg',
        'images/schetsen/2020_03.jpg',
        'images/schetsen/2020_02.jpg',
        'images/schetsen/2020_01.jpg',
        'images/schetsen/2019_06.jpg',
        'images/schetsen/2019_05.jpg',
        'images/schetsen/2019_04.jpg',
        'images/schetsen/2019_03.jpg',
        'images/schetsen/2019_02.jpg',
        'images/schetsen/2019_01.jpg'
    ];
} else {
    images = [
        'images/illustraties/2025_parkwandeling_02.jpg',
        'images/illustraties/2025_Nooit alleen.jpg',
        'images/illustraties/2025_Meisje-met-vos_REEL.gif',
        'images/illustraties/2025_losse tekening_De Koninklijke Kat.jpg',
        'images/illustraties/2025_DeKoninklijkeKat.jpg',
        'images/illustraties/2025_Dansend in de lucht_02.jpg',
        'images/illustraties/2025_Als een vis in het water.jpg',
        'images/illustraties/2024_Geboortekaarte zonder tekst.jpg',
        'images/illustraties/2024_Dino_ingezoomd.jpg',
        'images/illustraties/2023_Vos en kip_tekening.jpg',
        'images/illustraties/2023_Monsters in het zwembad_vingezoomd.jpg',
        'images/illustraties/2023_Halloween_tekening.jpg',
        'images/illustraties/2023_Draaien en draaien.gif',
        'images/illustraties/2023_Dit is vakantie_ingezoomd.jpg',
        'images/illustraties/2023_APaperADay.jpg',
        'images/illustraties/2022_Copy of KULeuven mural_03_2022.jpg',
        'images/illustraties/2022_Aan zee_ingezoomd.jpg',
        'images/illustraties/2021_Zeewier_02.jpg',
        'images/illustraties/2021_Zeewier_01.jpg',
        'images/illustraties/2021_Testpagina (RGB).jpg',
        'images/illustraties/2021_02.jpg',
        'images/illustraties/2021_01.jpg',
        'images/illustraties/2020_Leporello.jpg',
        'images/illustraties/2019_Nieuwjaarskaart2022_Gezin_zonder naam.jpg',
        'images/illustraties/2019_Nieuwjaarskaart2020_Oma&Opa_zonder naam.jpg',
        'images/illustraties/2019_Down The Dinghy.jpg',
        'images/illustraties/2018_Nieuwjaarskaart2019_ingezoomd_Oma&Opa_Binnenkant.jpg'
    ];
}

/* -------------------------
   Grid generation helpers
   ------------------------- */
function createImageItem(src, index) {
    const item = document.createElement('div');
    item.className = 'image-item';
    item.dataset.index = index;

    const img = document.createElement('img');
    img.src = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';
    img.dataset.src = src;
    img.alt = 'Portfolio image';
    img.className = 'lazy';

    item.appendChild(img);
    return item;
}

function generateDesktopGrid() {
    const gridContainer = document.getElementById('image-grid-container');
    if (!gridContainer) return;
    gridContainer.innerHTML = '';

    const numColumns = 3;
    const columns = [];
    for (let i = 0; i < numColumns; i++) {
        const col = document.createElement('div');
        col.className = 'image-column';
        columns.push(col);
    }

    images.forEach((src, idx) => {
        const item = createImageItem(src, idx);
        columns[idx % numColumns].appendChild(item);
    });

    columns.forEach(col => gridContainer.appendChild(col));
}

function generateMobileGrid() {
    const gridContainer = document.getElementById('image-grid-container');
    if (!gridContainer) return;
    gridContainer.innerHTML = '';

    const col = document.createElement('div');
    col.className = 'image-column';

    images.forEach((src, idx) => {
        const item = createImageItem(src, idx);
        col.appendChild(item);
    });

    gridContainer.appendChild(col);
}

/* -------------------------
   Lazy loading (IntersectionObserver)
   ------------------------- */
function lazyLoadImages() {
    const lazyImages = document.querySelectorAll('img.lazy');
    if (lazyImages.length === 0) return;

    if (window.imageObserver) {
        try { window.imageObserver.disconnect(); } catch (e) { /* ignore */ }
    }

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            obs.unobserve(img);
        });
    }, { rootMargin: '200px 0px' });

    lazyImages.forEach(img => observer.observe(img));
    window.imageObserver = observer;
}

/* -------------------------
   Lightbox
   ------------------------- */
const lightbox = document.getElementById('lightbox');
const lightboxImage = document.querySelector('.lightbox-image');
const prevButton = document.querySelector('.lightbox-prev');
const nextButton = document.querySelector('.lightbox-next');
const closeButton = document.querySelector('.lightbox-close');

let currentIndex = 0;

function openLightbox(index) {
    if (!lightbox || !lightboxImage) return;
    currentIndex = typeof index === 'number' ? index : 0;
    lightbox.classList.add('active');
    lightboxImage.src = images[currentIndex];
}

function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('active');
}

function showNextImage() {
    if (!lightboxImage) return;
    currentIndex = (currentIndex + 1) % images.length;
    lightboxImage.src = images[currentIndex];
}

function showPrevImage() {
    if (!lightboxImage) return;
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    lightboxImage.src = images[currentIndex];
}

/* -------------------------
   Scroll-reveal sidebar (mobile)
   ------------------------- */
const sidebar = document.querySelector('.sidebar');
let lastScrollTop = 0;
const scrollThreshold = 50;

function handleScrollReveal() {
    if (!sidebar) return;
    if (window.innerWidth > 768) {
        sidebar.classList.remove('hidden');
        return;
    }
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
        sidebar.classList.add('hidden');
    } else if (scrollTop < lastScrollTop) {
        sidebar.classList.remove('hidden');
    }
    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
}

/* -------------------------
   Contact form handling
   ------------------------- */
function setupContactForm() {
    const contactForm = document.querySelector('.contact-form');
    if (!contactForm) return;

    const sendingMsg = document.getElementById('form-sending');
    const successMsg = document.getElementById('form-success');

    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (sendingMsg) sendingMsg.style.display = 'block';
        if (successMsg) successMsg.style.display = 'none';

        fetch(contactForm.action, {
            method: 'POST',
            body: new FormData(contactForm),
            headers: { 'Accept': 'application/json' }
        })
            .then(response => {
                if (sendingMsg) sendingMsg.style.display = 'none';
                if (response.ok) {
                    contactForm.reset();
                    if (successMsg) successMsg.style.display = 'block';
                } else {
                    alert('Er ging iets mis. Probeer opnieuw.');
                }
            })
            .catch(err => {
                if (sendingMsg) sendingMsg.style.display = 'none';
                alert('Er ging iets mis: ' + err.message);
            });
    });
}

/* -------------------------
   Projects detail view
   ------------------------- */
function setupProjectDetails() {
    const projectItems = document.querySelectorAll('.project-item');
    if (!projectItems.length) return;

    const detailContainer = document.getElementById('project-detail');
    const introBlock = document.getElementById('projects-intro');
    const grid = document.querySelector('.projects-grid');

    projectItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            if (!detailContainer || !grid || !introBlock) return;

            const title = item.dataset.title || '';
            const text = item.dataset.text || '';
            const imgs = (item.dataset.images || '').split(',').map(s => s.trim()).filter(Boolean);

            const imgsHtml = imgs.map(src => `<img src="${src}" alt="${escapeHtml(title)}">`).join('');
            const html = `
                <h2>${escapeHtml(title)}</h2>
                <p>${escapeHtml(text)}</p>
                <div class="project-images">${imgsHtml}</div>
                <button id="back-to-projects" class="back-button">← Terug naar projecten</button>
            `;

            detailContainer.innerHTML = html;
            detailContainer.style.display = 'block';
            grid.style.display = 'none';
            introBlock.style.display = 'none';

            const backBtn = document.getElementById('back-to-projects');
            if (backBtn) {
                backBtn.addEventListener('click', () => {
                    detailContainer.style.display = 'none';
                    grid.style.display = 'grid';
                    introBlock.style.display = 'block';
                    // optional: scroll into view
                    grid.scrollIntoView({ behavior: 'smooth' });
                });
            }
        });
    });
}

/* -------------------------
   Utility: escape HTML
   ------------------------- */
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }[m]));
}

/* -------------------------
   Artwork protection
   ------------------------- */
function enableArtworkProtection() {
    // disable right-click & drag
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('dragstart', e => e.preventDefault());

    // block common save shortcuts (Ctrl/Cmd+S), try to block PrintScreen (best-effort)
    document.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
            e.preventDefault();
        }
        if (e.key === 'PrintScreen') {
            try { navigator.clipboard.writeText(''); } catch (err) { /* ignore */ }
            // avoid annoying alert on every PrintScreen; keep it commented or optional
            // alert('Screenshots are disabled.');
        }
    });

    // add CSS to make saving harder
    const css = `
        img { pointer-events: none; -webkit-user-drag: none; user-select: none; }
    `;
    const style = document.createElement('style');
    style.innerHTML = css;
    document.head.appendChild(style);
}

/* -------------------------
   Initialization & event wiring
   ------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    // active nav
    setActiveNav();

    // protection + contact
    enableArtworkProtection();
    setupContactForm();

    // project details (if any)
    setupProjectDetails();

    // image grid init
    const gridContainer = document.getElementById('image-grid-container');
    if (gridContainer) {
        if (window.innerWidth > 768) {
            generateDesktopGrid();
            gridContainer.classList.remove('mobile-view');
        } else {
            generateMobileGrid();
            gridContainer.classList.add('mobile-view');
        }
        lazyLoadImages();

        // delegate click to open lightbox on desktop only
        gridContainer.addEventListener('click', (e) => {
            const item = e.target.closest('.image-item');
            if (item && window.innerWidth > 768) {
                openLightbox(Number(item.dataset.index));
            }
        });
    }

    // wire lightbox controls (defensive)
    if (lightbox && lightboxImage) {
        if (closeButton) closeButton.addEventListener('click', closeLightbox);
        if (prevButton) prevButton.addEventListener('click', (e) => { e.stopPropagation(); showPrevImage(); });
        if (nextButton) nextButton.addEventListener('click', (e) => { e.stopPropagation(); showNextImage(); });

        // keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!lightbox.classList.contains('active')) return;
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') showNextImage();
            if (e.key === 'ArrowLeft') showPrevImage();
        });

        // background click to close (if clicking outside content)
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) closeLightbox();
        });

        // prevent inner clicks from bubbling (if elements exist)
        if (lightboxImage) lightboxImage.addEventListener('click', e => e.stopPropagation());
        if (prevButton) prevButton.addEventListener('click', e => e.stopPropagation());
        if (nextButton) nextButton.addEventListener('click', e => e.stopPropagation());
    }

    // clickable logo
    const sidebarLogo = document.querySelector('.sidebar-logo');
    if (sidebarLogo) {
        sidebarLogo.style.cursor = 'pointer';
        sidebarLogo.addEventListener('click', () => { window.location.href = 'index.html'; });
    }

    // mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinksMobile = document.querySelector('.nav-links');
    if (menuToggle && navLinksMobile) {
        menuToggle.addEventListener('click', () => {
            navLinksMobile.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
    }

    // scroll reveal
    window.addEventListener('scroll', handleScrollReveal, { passive: true });

    // resize handler (debounced) — regenerate grid and re-init lazy loader
    let resizeTimer = null;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const grid = document.getElementById('image-grid-container');
            if (grid) {
                const isMobile = window.innerWidth <= 768;
                const isCurrentlyMobile = grid.classList.contains('mobile-view');

                if (isMobile && !isCurrentlyMobile) {
                    generateMobileGrid();
                    grid.classList.add('mobile-view');
                    lazyLoadImages();
                } else if (!isMobile && isCurrentlyMobile) {
                    generateDesktopGrid();
                    grid.classList.remove('mobile-view');
                    lazyLoadImages();
                }
            }
            handleScrollReveal();
        }, 200);
    });

    // Prevent memory leaks: cleanup when page unloads
    window.addEventListener('beforeunload', () => {
        if (window.imageObserver) {
            try { window.imageObserver.disconnect(); } catch (e) { }
        }
    });
});
