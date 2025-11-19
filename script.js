// Function to handle the active navigation link
function setActiveNav() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            // Check the parent li to add the active class
            link.parentElement.classList.add('active');
        } else {
            link.parentElement.classList.remove('active');
        }
    });
}

// Decide which image set to load based on the current page
let images = [];

const currentPage = window.location.pathname.split('/').pop();

if (currentPage === "schetsen.html") {
    // Images for schetsen page
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
        'images/schetsen/2019_01.jpg',
    ];
} else {
    // Default images for index.html (work)
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
        'images/illustraties/2018_Nieuwjaarskaart2019_ingezoomd_Oma&Opa_Binnenkant.jpg',
    ];
}

// Function to dynamically generate the image grid for desktop (masonry-like)
function generateDesktopGrid() {
    const gridContainer = document.getElementById('image-grid-container');
    if (!gridContainer) return;

    // Clear existing content to avoid duplicates on resize
    gridContainer.innerHTML = '';

    const numColumns = 3;
    const columns = Array.from({
        length: numColumns
    }, () => {
        const column = document.createElement('div');
        column.classList.add('image-column');
        return column;
    });

    images.forEach((src, index) => {
        const item = document.createElement('div');
        item.classList.add('image-item');
        item.dataset.index = index;

        const img = document.createElement('img');
        img.src = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';
        img.dataset.src = src;
        img.alt = 'Portfolio image';
        img.classList.add('lazy');

        item.appendChild(img);
        columns[index % numColumns].appendChild(item);
    });

    columns.forEach(column => gridContainer.appendChild(column));
}

// Function to dynamically generate the image grid for mobile (sequential)
function generateMobileGrid() {
    const gridContainer = document.getElementById('image-grid-container');
    if (!gridContainer) return;

    // Clear existing content to avoid duplicates on resize
    gridContainer.innerHTML = '';

    // Create a single column wrapper for consistency with desktop column class, 
    // even though it functions as a single stack in mobile CSS
    const column = document.createElement('div');
    column.classList.add('image-column');

    images.forEach((src, index) => {
        const item = document.createElement('div');
        item.classList.add('image-item');
        item.dataset.index = index;

        const img = document.createElement('img');
        img.src = 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';
        img.dataset.src = src;
        img.alt = 'Portfolio image';
        img.classList.add('lazy');

        item.appendChild(img);
        column.appendChild(item);
    });

    // Append the single column to the grid container
    gridContainer.appendChild(column);
}


// Function to implement lazy loading
function lazyLoadImages() {
    const lazyImages = document.querySelectorAll('.lazy');
    if (lazyImages.length === 0) return;

    // Disconnect old observer if it exists
    if (window.imageObserver) {
        window.imageObserver.disconnect();
    }

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    lazyImages.forEach(img => {
        observer.observe(img);
    });

    // Store the observer globally to disconnect it later on regeneration
    window.imageObserver = observer;
}

// Lightbox functionality
const lightbox = document.getElementById('lightbox');
const lightboxImage = document.querySelector('.lightbox-image');
const prevButton = document.querySelector('.lightbox-prev');
const nextButton = document.querySelector('.lightbox-next');
const closeButton = document.querySelector('.lightbox-close');

let currentIndex = 0;

function openLightbox(index) {
    currentIndex = index;
    lightbox.classList.add('active');
    // The lightbox can handle GIFs simply by setting the src.
    lightboxImage.src = images[currentIndex];
}

function closeLightbox() {
    lightbox.classList.remove('active');
}

function showNextImage() {
    currentIndex = (currentIndex + 1) % images.length;
    lightboxImage.src = images[currentIndex];
}

function showPrevImage() {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    lightboxImage.src = images[currentIndex];
}


// --- Scroll Reveal Header Logic (NEW) ---
const sidebar = document.querySelector('.sidebar');
let lastScrollTop = 0;
const scrollThreshold = 50; // Distance in pixels before hiding

// Function executed on scroll or resize
function handleScrollReveal() {
    // Only run this logic on mobile viewports (<= 768px)
    if (window.innerWidth > 768) {
        if (sidebar) sidebar.classList.remove('hidden'); // Ensure it's visible on desktop
        return;
    }

    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    // Scrolling down and past the threshold
    if (scrollTop > lastScrollTop && scrollTop > scrollThreshold) {
        if (sidebar) sidebar.classList.add('hidden');
    }
    // Scrolling up
    else if (scrollTop < lastScrollTop) {
        if (sidebar) sidebar.classList.remove('hidden');
    }

    // Update last scroll position
    lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
}

// Attach the scroll listener once on load if the sidebar element exists
if (sidebar) {
    window.addEventListener('scroll', handleScrollReveal, { passive: true });
}
// --- END Scroll Reveal Header Logic ---

// Contact form handler with success message
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(contactForm);

        fetch(contactForm.action, {
            method: "POST",
            body: formData,
            headers: {
                "Accept": "application/json"
            }
        })
            .then(response => {
                if (response.ok) {
                    contactForm.reset();
                    document.getElementById("form-success").style.display = "block";
                } else {
                    alert("Er ging iets mis. Probeer opnieuw.");
                }
            })
            .catch(error => {
                alert("Er ging iets mis: " + error.message);
            });
    });
}



// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    setActiveNav();

    // Only run image grid functions on pages with the grid container
    if (document.getElementById('image-grid-container')) {
        const gridContainer = document.getElementById('image-grid-container');

        // Initial grid generation
        if (window.innerWidth > 768) {
            generateDesktopGrid();
            gridContainer.classList.remove('mobile-view');
        } else {
            generateMobileGrid();
            gridContainer.classList.add('mobile-view');
        }
        lazyLoadImages();

        // Event delegation for the image grid
        document.getElementById('image-grid-container').addEventListener('click', (e) => {
            const item = e.target.closest('.image-item');
            // Only open the lightbox if the screen width is greater than 768px
            if (item && window.innerWidth > 768) {
                const index = parseInt(item.dataset.index);
                openLightbox(index);
            }
        });
    }

    // Only set up lightbox event listeners if the lightbox exists
    if (lightbox && prevButton && nextButton && closeButton) {
        closeButton.addEventListener('click', closeLightbox);
        prevButton.addEventListener('click', showPrevImage);
        nextButton.addEventListener('click', showNextImage);

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (lightbox.classList.contains('active')) {
                if (e.key === 'Escape') {
                    closeLightbox();
                } else if (e.key === 'ArrowRight') {
                    showNextImage();
                } else if (e.key === 'ArrowLeft') {
                    showPrevImage();
                }
            }
        });
    }

    // Close lightbox when clicking on background (but not the image or arrows)
    lightbox.addEventListener('click', (e) => {
        if (
            e.target === lightbox ||             // click directly on background
            e.target.classList.contains('lightbox-content') // if you wrap image in content div
        ) {
            closeLightbox();
        }
    });

    // Prevent clicks on the image or arrows from closing the lightbox
    lightboxImage.addEventListener('click', (e) => e.stopPropagation());
    prevButton.addEventListener('click', (e) => e.stopPropagation());
    nextButton.addEventListener('click', (e) => e.stopPropagation());



    // Event listener for the sidebar logo to redirect to the home page
    const sidebarLogo = document.querySelector('.sidebar-logo');
    if (sidebarLogo) {
        sidebarLogo.style.cursor = 'pointer'; // Make it look clickable
        sidebarLogo.addEventListener('click', () => {
            window.location.href = 'index.html';
        });
    }

    // Handle screen resize to regenerate the correct grid
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const gridContainer = document.getElementById('image-grid-container');
            if (gridContainer) {
                const isMobile = window.innerWidth <= 768;
                const isCurrentlyMobileView = gridContainer.classList.contains('mobile-view');

                if (isMobile && !isCurrentlyMobileView) {
                    generateMobileGrid();
                    gridContainer.classList.add('mobile-view');
                    lazyLoadImages();
                } else if (!isMobile && isCurrentlyMobileView) {
                    generateDesktopGrid();
                    gridContainer.classList.remove('mobile-view');
                    lazyLoadImages();
                }
            }

            // Re-run the scroll handler logic on resize to check/reset desktop visibility
            handleScrollReveal();
        }, 250); // Debounce delay
    });
});

// Mobile menu toggle
const menuToggle = document.querySelector('.menu-toggle');
const navLinksMobile = document.querySelector('.nav-links');
menuToggle.addEventListener('click', () => {
    navLinksMobile.classList.toggle('active');
    menuToggle.classList.toggle('active');
});
document.addEventListener("DOMContentLoaded", () => {
    const projectItems = document.querySelectorAll(".project-item");
    const detailContainer = document.getElementById("project-detail");
    const introBlock = document.getElementById("projects-intro");
    const grid = document.querySelector(".projects-grid");

    projectItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();

            const title = item.dataset.title;
            const text = item.dataset.text;
            const images = item.dataset.images.split(",");

            // Build detail content
            let html = `
                <h2>${title}</h2>
                <p>${text}</p>
                <div class="project-images">
                    ${images.map(src => `<img src="${src}" alt="${title}" />`).join("")}
                </div>
                <button id="back-to-projects" class="back-button">← Terug naar projecten</button>
            `;

            detailContainer.innerHTML = html;
            detailContainer.style.display = "block";

            // Hide grid + intro
            grid.style.display = "none";
            introBlock.style.display = "none";

            // Handle back button
            document.getElementById("back-to-projects").addEventListener("click", () => {
                detailContainer.style.display = "none";
                grid.style.display = "grid";
                introBlock.style.display = "block";
            });
        });
    });
});
