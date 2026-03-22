/**
 * UniSphere Auth Helper
 *
 * Real auth only: checks /api/users/me via Django session.
 * No sessionStorage, no demo fallback.
 */
(function () {
  'use strict';

  var Auth = {

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

      fetch('/api/users/me')
        .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
        .then(function (d) {
          if (d && d.id) { Auth._applyBtn(btn, d); }
        })
        .catch(function () { /* not logged in — keep door icon */ });
    }
  };

  /* Read Django's csrftoken cookie */
  Auth.csrfToken = function () {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
  };

  /* Convenience POST with CSRF header pre-set */
  Auth.post = function (url, body) {
    return fetch(url, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': Auth.csrfToken() },
      body:    JSON.stringify(body),
    });
  };

  window.UniSphereAuth = Auth;

  /* Auto-init on every page that loads this script */
  document.addEventListener('DOMContentLoaded', Auth.initBtn);

}());