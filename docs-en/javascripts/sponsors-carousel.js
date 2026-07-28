function initSponsorsCarousel() {
  const container = document.querySelector(".bcp-sponsors-swiper");
  if (!container || typeof Swiper === "undefined") return;
  if (container.swiper) return;

  // Carrossel de cards: um patrocinador por vez, com setas e paginação.
  new Swiper(container, {
    slidesPerView: 1,
    spaceBetween: 20,
    loop: true,
    grabCursor: true,
    autoHeight: false,
    autoplay: {
      delay: 4500,
      disableOnInteraction: false,
      pauseOnMouseEnter: true,
    },
    pagination: {
      el: container.querySelector(".swiper-pagination"),
      clickable: true,
    },
    navigation: {
      nextEl: container.querySelector(".swiper-button-next"),
      prevEl: container.querySelector(".swiper-button-prev"),
    },
    // mobile: 1 card por vez; a partir de 768px (web): 2 por vez
    breakpoints: {
      768: { slidesPerView: 2, spaceBetween: 24 },
    },
  });
}

if (typeof document$ !== "undefined") {
  document$.subscribe(initSponsorsCarousel);
} else {
  document.addEventListener("DOMContentLoaded", initSponsorsCarousel);
}
