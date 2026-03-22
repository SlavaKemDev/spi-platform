(function () {
  'use strict';

  /* ── Theme toggle (runs immediately, before DOMContentLoaded) ── */
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

  /* ── Carousel ──────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    var track   = document.querySelector('.carousel-track');
    var btnPrev = document.querySelector('.carousel-arrow.prev');
    var btnNext = document.querySelector('.carousel-arrow.next');
    var clip    = document.querySelector('.carousel-clip');

    if (!track || !btnPrev || !btnNext || !clip) return;

    var cards   = Array.from(track.children);
    var GAP_PX  = 24;
    var pixelOffset = 0;

    function cardWidth() {
      return cards[0] ? cards[0].getBoundingClientRect().width : 0;
    }

    function maxOffset() {
      var cw = cardWidth();
      if (!cw) return 0;
      // Account for clip's horizontal padding: the track starts at paddingLeft offset,
      // so the effective viewport shifts. Add both paddings back to allow full scroll.
      var cs = window.getComputedStyle(clip);
      var padH = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
      return Math.max(0, cards.length * (cw + GAP_PX) - GAP_PX - clip.offsetWidth + padH);
    }

    function applyOffset(offset, withTransition) {
      pixelOffset = Math.max(0, Math.min(offset, maxOffset()));
      track.style.transition = withTransition
        ? 'transform .4s cubic-bezier(.4,0,.2,1)'
        : 'none';
      track.style.transform = 'translateX(-' + pixelOffset + 'px)';
      updateArrows();
    }

    function updateArrows() {
      var atStart = pixelOffset <= 1;
      var atEnd   = pixelOffset >= maxOffset() - 1;
      btnPrev.style.opacity       = atStart ? '0.3' : '1';
      btnPrev.style.pointerEvents = atStart ? 'none' : 'auto';
      btnNext.style.opacity       = atEnd   ? '0.3' : '1';
      btnNext.style.pointerEvents = atEnd   ? 'none' : 'auto';
    }

    /* Arrow buttons: snap by one card with smooth transition */
    btnPrev.addEventListener('click', function () {
      var cw  = cardWidth() + GAP_PX;
      var idx = Math.round(pixelOffset / cw);
      applyOffset((idx - 1) * cw, true);
    });

    btnNext.addEventListener('click', function () {
      var cw  = cardWidth() + GAP_PX;
      var idx = Math.round(pixelOffset / cw);
      applyOffset((idx + 1) * cw, true);
    });

    /* ── Wheel / trackpad: continuous smooth pixel scroll ────── */
    clip.addEventListener('wheel', function (e) {
      var dx = e.deltaX;
      var dy = e.deltaY;

      // Use whichever axis has larger magnitude; vertical wheel → horizontal scroll
      var delta = Math.abs(dx) >= Math.abs(dy) ? dx : dy;

      if (delta === 0) return;

      e.preventDefault(); // stop page scroll while over carousel

      // deltaMode 0 = pixels (trackpad), 1 = lines (~20px), 2 = pages (~200px)
      var px = delta * (e.deltaMode === 0 ? 1 : e.deltaMode === 1 ? 20 : 200);

      // Apply directly, no CSS transition → immediate / native-feeling movement
      applyOffset(pixelOffset + px, false);
    }, { passive: false });

    /* ── Touch swipe ──────────────────────────────────────────── */
    var touchStartX = 0;
    var touchStartY = 0;
    var touchStartOffset = 0;
    var isHorizSwipe = null;

    clip.addEventListener('touchstart', function (e) {
      touchStartX      = e.touches[0].clientX;
      touchStartY      = e.touches[0].clientY;
      touchStartOffset = pixelOffset;
      isHorizSwipe     = null;
      track.style.transition = 'none';
    }, { passive: true });

    clip.addEventListener('touchmove', function (e) {
      var dx = touchStartX - e.touches[0].clientX;
      var dy = touchStartY - e.touches[0].clientY;

      if (isHorizSwipe === null) {
        isHorizSwipe = Math.abs(dx) > Math.abs(dy);
      }
      if (!isHorizSwipe) return;

      e.preventDefault();
      applyOffset(touchStartOffset + dx, false);
    }, { passive: false });

    clip.addEventListener('touchend', function (e) {
      if (!isHorizSwipe) return;
      var dx   = touchStartX - e.changedTouches[0].clientX;
      var cw   = cardWidth() + GAP_PX;
      var idx  = Math.round((touchStartOffset + dx) / cw);
      applyOffset(idx * cw, true);
    }, { passive: true });

    /* Recalculate on resize */
    window.addEventListener('resize', function () {
      applyOffset(pixelOffset, false);
    });

    applyOffset(0, false);
  });

}());