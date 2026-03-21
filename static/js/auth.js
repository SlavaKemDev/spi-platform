/**
 * UniSphere Auth Helper
 *
 * Hybrid auth: tries real API (/api/users/me) first, falls back to sessionStorage.
 * sessionStorage key: 'us_user' → { id, first_name, last_name, email, is_demo? }
 *
 * To replace with real Django auth later:
 *  - Keep the API calls as-is — they already point to the real backend.
 *  - Remove the demo-fallback catch blocks in auth.html.
 *  - Optionally add @login_required to views that need server-side protection.
 */
(function () {
  'use strict';

  var KEY = 'us_user';

  var Auth = {

    getUser: function () {
      try { return JSON.parse(sessionStorage.getItem(KEY)) || null; }
      catch (e) { return null; }
    },

    setUser: function (u) {
      sessionStorage.setItem(KEY, JSON.stringify(u));
    },

    clearUser: function () {
      sessionStorage.removeItem(KEY);
    },

    /* Build display initials from user object */
    initials: function (u) {
      var s = (u.first_name ? u.first_name[0].toUpperCase() : '')
            + (u.last_name  ? u.last_name[0].toUpperCase()  : '');
      return s || (u.email ? u.email[0].toUpperCase() : '?');
    },

    /* Apply logged-in state to the #accountBtn element */
    _applyBtn: function (btn, user) {
      btn.textContent = Auth.initials(user);
      btn.title = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email || '';
      btn.href = '/profile/';
    },

    /* Call once per page to update #accountBtn */
    initBtn: function () {
      var btn = document.getElementById('accountBtn');
      if (!btn) return;

      /* 1. Fast path: sessionStorage */
      var user = Auth.getUser();
      if (user) { Auth._applyBtn(btn, user); return; }

      /* 2. Real API check */
      fetch('/api/users/me')
        .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
        .then(function (d) {
          if (d && d.id) { Auth.setUser(d); Auth._applyBtn(btn, d); }
        })
        .catch(function () { /* not logged in — keep door icon */ });
    }
  };

  window.UniSphereAuth = Auth;

  /* Auto-init on every page that loads this script */
  document.addEventListener('DOMContentLoaded', Auth.initBtn);

}());