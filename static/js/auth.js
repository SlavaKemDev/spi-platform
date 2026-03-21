/**
 * UniSphere Auth Helper
 *
 * Uses real Django session auth. No localStorage/sessionStorage mocks.
 * Auth state is determined solely by GET /api/users/me.
 *
 * Endpoints (Django Ninja, session-based, no CSRF required for API):
 *   POST /api/users/login     { email, password }
 *   POST /api/users/register  { email, password, first_name, last_name, patronymic, birth_date }
 *   POST /api/users/logout
 *   GET  /api/users/me        → { id, email, first_name, last_name, patronymic, birth_date }
 */
(function () {
  'use strict';

  var Auth = {

    /* Update #accountBtn based on real session state */
    initBtn: function () {
      var btn = document.getElementById('accountBtn');
      if (!btn) return;

      fetch('/api/users/me')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d && d.id) {
            var ini = (d.first_name ? d.first_name[0].toUpperCase() : '')
                    + (d.last_name  ? d.last_name[0].toUpperCase()  : '');
            btn.textContent = ini || (d.email ? d.email[0].toUpperCase() : '?');
            btn.title = [d.first_name, d.last_name].filter(Boolean).join(' ') || d.email;
            btn.href = '/profile/';
          }
          /* else: not authenticated — keep door icon, href stays /auth/ */
        })
        .catch(function () { /* network error — keep door icon */ });
    }

  };

  window.UniSphereAuth = Auth;

  document.addEventListener('DOMContentLoaded', Auth.initBtn);

}());