const carouselItems = document.querySelectorAll('.carousel-item');
let currentItem = 0;

function showNextItem() {
    carouselItems[currentItem].classList.remove('active');
    currentItem = (currentItem + 1) % carouselItems.length;
    carouselItems[currentItem].classList.add('active');
}

setInterval(showNextItem, 5000);

const nav = document.querySelector('nav');
const hamburgerMenu = document.querySelector('.mobile-menu-icon');
hamburgerMenu.addEventListener('click', () => {
    nav.classList.toggle('open');
});

// Gestion des dropdowns sur mobile
const dropdowns = document.querySelectorAll('.dropdown');
dropdowns.forEach(dropdown => {
    dropdown.addEventListener('click', (e) => {
        if (window.innerWidth <= 890) {
            e.preventDefault();
            dropdown.classList.toggle('active');
        }
    });
});





// Services Carousel
const servicesCarousel = document.querySelector('.services-carousel');
const serviceItems = document.querySelectorAll('.service-item');
const dotsContainer = document.querySelector('.carousel-dots');

let currentIndex = 0;

// Create dots
serviceItems.forEach((_, index) => {
    const dot = document.createElement('div');
    dot.classList.add('carousel-dot');
    if (index === 0) dot.classList.add('active');
    dot.addEventListener('click', () => goToSlide(index));
    dotsContainer.appendChild(dot);
});

const dots = document.querySelectorAll('.carousel-dot');

function goToSlide(index) {
    servicesCarousel.scrollTo({
        left: serviceItems[index].offsetLeft,
        behavior: 'smooth'
    });
    currentIndex = index;
    updateDots();
}

function updateDots() {
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentIndex);
    });
}

servicesCarousel.addEventListener('scroll', () => {
    const index = Math.round(servicesCarousel.scrollLeft / serviceItems[0].offsetWidth);
    if (index !== currentIndex) {
        currentIndex = index;
        updateDots();
    }
});