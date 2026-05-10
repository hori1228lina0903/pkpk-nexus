// events-carousel.js
let ongoingSwiper = null;
let upcomingSwiper = null;

function initEventCarousels() {
  setTimeout(function() {
    // Ongoing Events カルーセル
    const ongoingCarousel = document.querySelector('.ongoing-swiper');
    if (ongoingCarousel && !ongoingSwiper) {
      const savedIndex = sessionStorage.getItem('ongoingSwiperIndex');
      
      ongoingSwiper = new Swiper('.ongoing-swiper', {
        slidesPerView: 'auto',
        spaceBetween: 10,
        centeredSlides: true,
        pagination: {
          el: '.swiper-pagination',
          clickable: true,
        },
        on: {
          slideChange: function() {
            sessionStorage.setItem('ongoingSwiperIndex', this.activeIndex);
          }
        }
      });
      
      if (savedIndex !== null) {
        ongoingSwiper.slideTo(parseInt(savedIndex), 0);
      }
    }
    
    // Upcoming Events カルーセル（追加）
    const upcomingCarousel = document.querySelector('.upcoming-swiper');
    if (upcomingCarousel && !upcomingSwiper) {
      upcomingSwiper = new Swiper('.upcoming-swiper', {
        slidesPerView: 'auto',
        spaceBetween: 10,
        centeredSlides: true,
        pagination: {
          el: '.swiper-pagination',
          clickable: true,
        },
      });
    }
  }, 300);
}

setTimeout(initEventCarousels, 500);
document.addEventListener('DOMContentLoaded', initEventCarousels);