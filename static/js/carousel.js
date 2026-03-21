(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const track    = document.querySelector('.carousel-track');
    const btnPrev  = document.querySelector('.carousel-arrow.prev');
    const btnNext  = document.querySelector('.carousel-arrow.next');

    if (!track || !btnPrev || !btnNext) return;

    const cards        = Array.from(track.children);
    const VISIBLE      = 3;
    const GAP_PX       = 24;
    let   currentIndex = 0;

    function cardWidth() {
      return cards[0].getBoundingClientRect().width;
    }

    function maxIndex() {
      return Math.max(0, cards.length - VISIBLE);
    }

    function updateTrack() {
      const offset = currentIndex * (cardWidth() + GAP_PX);
      track.style.transform = `translateX(-${offset}px)`;
    }

    function updateButtons() {
      btnPrev.style.opacity = currentIndex === 0 ? '0.3' : '1';
      btnPrev.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
      btnNext.style.opacity = currentIndex >= maxIndex() ? '0.3' : '1';
      btnNext.style.pointerEvents = currentIndex >= maxIndex() ? 'none' : 'auto';
    }

    btnPrev.addEventListener('click', function () {
      if (currentIndex > 0) { currentIndex--; update(); }
    });

    btnNext.addEventListener('click', function () {
      if (currentIndex < maxIndex()) { currentIndex++; update(); }
    });

    function update() {
      updateTrack();
      updateButtons();
    }

    // Recalculate on resize
    window.addEventListener('resize', function () { updateTrack(); });

    update();
  });
}());