(function () {
  'use strict';

  /* ── Theme toggle ──────────────────────────────────────── */
  var themeBtn = document.getElementById('themeToggle');
  if (themeBtn) {
    var saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    themeBtn.textContent = saved === 'dark' ? '☀️' : '🌙';

    themeBtn.addEventListener('click', function () {
      var cur  = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
      themeBtn.textContent = next === 'dark' ? '☀️' : '🌙';
    });
  }

  /* ── Carousel ──────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    var track   = document.querySelector('.carousel-track');
    var btnPrev = document.querySelector('.carousel-arrow.prev');
    var btnNext = document.querySelector('.carousel-arrow.next');
    var clip    = document.querySelector('.carousel-clip');

    if (!track || !btnPrev || !btnNext) return;

    var cards        = Array.from(track.children);
    var VISIBLE      = 3;
    var GAP_PX       = 24;
    var currentIndex = 0;

    function cardWidth() {
      return cards[0].getBoundingClientRect().width;
    }

    function maxIndex() {
      return Math.max(0, cards.length - VISIBLE);
    }

    function updateTrack(animated) {
      if (animated === false) {
        track.style.transition = 'none';
      } else {
        track.style.transition = 'transform .4s cubic-bezier(.4,0,.2,1)';
      }
      var offset = currentIndex * (cardWidth() + GAP_PX);
      track.style.transform = 'translateX(-' + offset + 'px)';
    }

    function updateButtons() {
      btnPrev.style.opacity       = currentIndex === 0 ? '0.3' : '1';
      btnPrev.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
      btnNext.style.opacity       = currentIndex >= maxIndex() ? '0.3' : '1';
      btnNext.style.pointerEvents = currentIndex >= maxIndex() ? 'none' : 'auto';
    }

    function goTo(index) {
      currentIndex = Math.max(0, Math.min(index, maxIndex()));
      updateTrack();
      updateButtons();
    }

    btnPrev.addEventListener('click', function () { goTo(currentIndex - 1); });
    btnNext.addEventListener('click', function () { goTo(currentIndex + 1); });

    /* ── Wheel / trackpad scroll ─────────────────────────── */
    var wheelDebounce = null;

    if (clip) {
      clip.addEventListener('wheel', function (e) {
        // Only intercept when the scroll is more horizontal than vertical,
        // OR user is scrolling vertically directly over the carousel.
        var absX = Math.abs(e.deltaX);
        var absY = Math.abs(e.deltaY);

        // For a vertical wheel over the carousel, take over horizontally.
        if (absY > 0 || absX > 0) {
          e.preventDefault();

          clearTimeout(wheelDebounce);
          wheelDebounce = setTimeout(function () {
            var delta = absX >= absY ? e.deltaX : e.deltaY;
            if (delta > 0) {
              goTo(currentIndex + 1);
            } else if (delta < 0) {
              goTo(currentIndex - 1);
            }
          }, 50);
        }
      }, { passive: false });
    }

    /* ── Resize ──────────────────────────────────────────── */
    window.addEventListener('resize', function () { updateTrack(false); });

    goTo(0);
  });
}());