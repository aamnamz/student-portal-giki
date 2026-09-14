document.addEventListener('DOMContentLoaded', function () {
  var pageLoader = document.getElementById('pageLoader');
  function showPageLoader() {
    if (pageLoader) pageLoader.hidden = false;
  }
  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', showPageLoader);
  });
  document.querySelectorAll('a[href]').forEach(function (link) {
    link.addEventListener('click', function () {
      if (!link.target && !link.hasAttribute('download') && !link.getAttribute('href').startsWith('#')) showPageLoader();
    });
  });

  var portal = document.getElementById('portal');
  var toggle = document.getElementById('sidebarToggle');
  var scrim = document.getElementById('sidebarScrim');
  var mobileQuery = window.matchMedia('(max-width: 860px)');
  var COLLAPSE_KEY = 'giki_sidebar_collapsed';

  function getSavedCollapsed() {
    try { return localStorage.getItem(COLLAPSE_KEY) === '1'; } catch (e) { return false; }
  }
  function saveCollapsed(collapsed) {
    try { localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0'); } catch (e) {}
  }

  function setNavOpen(open) {
    if (!portal) return;
    portal.classList.toggle('nav-open', open);
    if (toggle) toggle.setAttribute('aria-expanded', String(open));
  }
  function closeNav() { setNavOpen(false); }

  function setSidebarCollapsed(collapsed, persist) {
    if (!portal) return;
    portal.classList.toggle('sidebar-collapsed', collapsed);
    if (toggle) toggle.setAttribute('aria-expanded', String(!collapsed));
    if (persist) saveCollapsed(collapsed);
  }

  if (!mobileQuery.matches) {
    setSidebarCollapsed(getSavedCollapsed(), false);
  }

  window.addEventListener('pageshow', function (event) {
    if (event.persisted && !mobileQuery.matches) {
      setSidebarCollapsed(getSavedCollapsed(), false);
    }
  });

  if (toggle) {
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (mobileQuery.matches) {
        setNavOpen(!portal.classList.contains('nav-open'));
      } else {
        setSidebarCollapsed(!portal.classList.contains('sidebar-collapsed'), true);
      }
    });
  }

  if (scrim) scrim.addEventListener('click', closeNav);

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeNav();
  });

  function handleBreakpointChange() {
    if (!portal) return;
    portal.classList.remove('nav-open');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
    if (mobileQuery.matches) {
      portal.classList.remove('sidebar-collapsed');
    } else {
      setSidebarCollapsed(getSavedCollapsed(), false);
    }
  }
  if (typeof mobileQuery.addEventListener === 'function') {
    mobileQuery.addEventListener('change', handleBreakpointChange);
  } else if (typeof mobileQuery.addListener === 'function') {
    mobileQuery.addListener(handleBreakpointChange);
  }

  var applicationToggle = document.querySelector('.application-toggle');
  var applicationSubnav = document.getElementById('applicationSubnav');
  if (applicationToggle && applicationSubnav) {
    applicationToggle.addEventListener('click', function () {
      var isOpen = applicationSubnav.classList.toggle('open');
      applicationToggle.setAttribute('aria-expanded', String(isOpen));
    });
  }

  var railTooltip = document.createElement('div');
  railTooltip.className = 'rail-tooltip';
  document.body.appendChild(railTooltip);

  function hideRailTooltip() {
    railTooltip.classList.remove('visible');
  }

  document.querySelectorAll('.nav-item[data-tooltip], .subnav-item[data-tooltip]').forEach(function (item) {
    item.addEventListener('mouseenter', function () {
      if (!portal || !portal.classList.contains('sidebar-collapsed') || mobileQuery.matches) return;
      var rect = item.getBoundingClientRect();
      railTooltip.textContent = item.getAttribute('data-tooltip');
      railTooltip.style.left = (rect.right + 10) + 'px';
      railTooltip.style.top = (rect.top + rect.height / 2) + 'px';
      railTooltip.classList.add('visible');
    });
    item.addEventListener('mouseleave', hideRailTooltip);
    item.addEventListener('blur', hideRailTooltip);
  });
  document.addEventListener('scroll', hideRailTooltip, true);
  window.addEventListener('resize', hideRailTooltip);
  if (toggle) toggle.addEventListener('click', hideRailTooltip);

  // Profile dropdown
  var trigger = document.getElementById('profileTrigger');
  var dropdown = document.getElementById('profileDropdown');
  if (trigger && dropdown) {
    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdown.classList.toggle('open');
    });
    document.addEventListener('click', function () { dropdown.classList.remove('open'); });
  }

  function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    return parts.length === 2 ? parts.pop().split(';').shift() : '';
  }
  // Exposed so fcm-handler.js's refreshNotificationBell() can reuse the
  // exact same cookie-reading logic instead of duplicating it.
  window.getCsrfCookie = getCookie;

  // ---- Notification dropdown: toggle + delegated click handling ----
  // Delegated (bound to the container, not individual buttons) so it keeps
  // working after fcm-handler.js's renderNotificationBell() replaces the
  // dropdown's innerHTML on a real-time push — direct per-button listeners
  // would be lost the moment the markup gets swapped out.
  var notificationTrigger = document.getElementById('notificationTrigger');
  var notificationDropdown = document.getElementById('notificationDropdown');
  if (notificationTrigger && notificationDropdown) {
    notificationTrigger.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = notificationDropdown.classList.toggle('open');
      notificationTrigger.setAttribute('aria-expanded', String(isOpen));
    });
    document.addEventListener('click', function () {
      notificationDropdown.classList.remove('open');
      notificationTrigger.setAttribute('aria-expanded', 'false');
    });

    notificationDropdown.addEventListener('click', function (e) {
      e.stopPropagation();

      var readButton = e.target.closest('.notification-read[data-read-url]');
      if (readButton) {
        e.preventDefault();
        fetch(readButton.getAttribute('data-read-url'), {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (response) { return response.json(); }).then(function (data) {
          if (!data.ok) return;
          var row = readButton.closest('.notification-row');
          if (row) row.classList.remove('unread');
          readButton.remove();
          var badge = document.querySelector('#notificationTrigger .badge-dot');
          if (badge) {
            var count = Math.max(0, (parseInt(badge.textContent, 10) || 1) - 1);
            if (count) badge.textContent = count; else badge.remove();
          }
        });
        return;
      }

      var clearButton = e.target.closest('#clearAllNotifications');
      if (clearButton) {
        fetch(clearButton.dataset.clearUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        }).then(function (response) {
          if (response.ok) {
            notificationDropdown.innerHTML = '<div class="notification-empty">No new notifications</div>';
            document.querySelector('.badge-dot')?.remove();
          }
        });
      }
    });
  }

  var helpButton = document.getElementById('stepHelpButton');
  var helpPopover = document.getElementById('stepHelpPopover');

  if (helpButton && helpPopover) {
    function closeStepHelp() {
      helpPopover.classList.remove('open');
      helpPopover.setAttribute('aria-hidden', 'true');
      helpButton.setAttribute('aria-expanded', 'false');
    }

    helpButton.addEventListener('click', function (event) {
      event.stopPropagation();

      var isOpen = helpPopover.classList.contains('open');

      if (isOpen) {
        closeStepHelp();
      } else {
        helpPopover.classList.add('open');
        helpPopover.setAttribute('aria-hidden', 'false');
        helpButton.setAttribute('aria-expanded', 'true');
      }
    });

    helpPopover.querySelectorAll('[data-step-help-close]').forEach(function (control) {
      control.addEventListener('click', closeStepHelp);
    });

    document.addEventListener('click', function (event) {
      if (
        helpPopover.classList.contains('open') &&
        !helpPopover.contains(event.target) &&
        !helpButton.contains(event.target)
      ) {
        closeStepHelp();
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && helpPopover.classList.contains('open')) {
        closeStepHelp();
        helpButton.focus();
      }
    });
  }

  document.querySelectorAll('[data-percent]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-percent'), 10) || 0;
    requestAnimationFrame(function () {
      if (el.classList.contains('ring')) {
        el.style.setProperty('--pct', target);
      } else {
        el.style.width = target + '%';
      }
    });
  });

  document.querySelectorAll('[data-count-to]').forEach(function (el) {
    var target = parseInt(el.getAttribute('data-count-to'), 10) || 0;
    var current = 0;
    var step = Math.max(1, Math.round(target / 30));
    var timer = setInterval(function () {
      current = Math.min(target, current + step);
      el.textContent = current + '%';
      if (current >= target) clearInterval(timer);
    }, 20);
  });

  var SECTION_KEY_PREFIX = 'giki_sec_';
  var sectionPanels = document.querySelectorAll('.sidebar-nav .application-subnav[id]');

  function isSectionCollapseActive() {
    return !mobileQuery.matches;
  }

  sectionPanels.forEach(function (panel) {
    var id = panel.id;
    try {
      var saved = localStorage.getItem(SECTION_KEY_PREFIX + id);
      if (saved === '0' && isSectionCollapseActive()) {
        panel.classList.remove('show');
        var btn = document.querySelector('[data-bs-target="#' + id + '"]');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }
    } catch (e) {}
  });

  sectionPanels.forEach(function (panel) {
    panel.addEventListener('hide.bs.collapse', function () {
      if (!isSectionCollapseActive()) return;
      try { localStorage.setItem(SECTION_KEY_PREFIX + panel.id, '0'); } catch (e) {}
    });
    panel.addEventListener('show.bs.collapse', function () {
      try { localStorage.setItem(SECTION_KEY_PREFIX + panel.id, '1'); } catch (e) {}
    });
  });

  var prevBreakpointMobile = mobileQuery.matches;
  function handleSectionBreakpointChange() {
    var nowMobile = mobileQuery.matches;
    if (nowMobile === prevBreakpointMobile) return;
    prevBreakpointMobile = nowMobile;
    sectionPanels.forEach(function (panel) {
      var id = panel.id;
      var btn = document.querySelector('[data-bs-target="#' + id + '"]');
      if (nowMobile) {
        panel.classList.add('show');
        if (btn) btn.setAttribute('aria-expanded', 'true');
      } else {
        try {
          var saved = localStorage.getItem(SECTION_KEY_PREFIX + id);
          var shouldShow = saved !== '0';
          if (shouldShow) {
            panel.classList.add('show');
            if (btn) btn.setAttribute('aria-expanded', 'true');
          } else {
            panel.classList.remove('show');
            if (btn) btn.setAttribute('aria-expanded', 'false');
          }
        } catch (e) {}
      }
    });
  }
  if (typeof mobileQuery.addEventListener === 'function') {
    mobileQuery.addEventListener('change', handleSectionBreakpointChange);
  } else if (typeof mobileQuery.addListener === 'function') {
    mobileQuery.addListener(handleSectionBreakpointChange);
  }

  // ---- Toast Notification Utility ----
  window.showSuccessToast = function (message) {
    message = message || 'Saved successfully';
    var container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container position-fixed top-0 end-0 p-3';
      container.style.zIndex = '1090';
      container.setAttribute('aria-live', 'polite');
      container.setAttribute('aria-atomic', 'true');
      document.body.appendChild(container);
    }

    var toastEl = document.createElement('div');
    toastEl.className = 'toast custom-success-toast align-items-center mb-2';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'polite');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.setAttribute('data-bs-autohide', 'true');
    toastEl.setAttribute('data-bs-delay', '3500');

    toastEl.innerHTML =
      '<div class="d-flex align-items-center justify-content-between p-3">' +
        '<div class="d-flex align-items-center gap-2">' +
          '<svg class="toast-check-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
            '<polyline points="20 6 9 17 4 12"></polyline>' +
          '</svg>' +
          '<span class="toast-message">' + message + '</span>' +
        '</div>' +
        '<button type="button" class="btn-close ms-3" data-bs-dismiss="toast" aria-label="Close"></button>' +
      '</div>';

    container.appendChild(toastEl);

    if (window.bootstrap && window.bootstrap.Toast) {
      var bsToast = window.bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3500, autohide: true });
      bsToast.show();
    } else {
      toastEl.classList.add('show');
      setTimeout(function () {
        toastEl.remove();
      }, 3500);
    }

    toastEl.addEventListener('hidden.bs.toast', function () {
      toastEl.remove();
    });
  };

  document.querySelectorAll('#toastContainer .toast').forEach(function (toastEl) {
    if (window.bootstrap && window.bootstrap.Toast) {
      var bsToast = window.bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3500, autohide: true });
      bsToast.show();
    } else {
      toastEl.classList.add('show');
    }
    toastEl.addEventListener('hidden.bs.toast', function () {
      toastEl.remove();
    });
  });

  try {
    var pendingMsg = sessionStorage.getItem('pending_success_toast');
    if (pendingMsg) {
      sessionStorage.removeItem('pending_success_toast');
      window.showSuccessToast(pendingMsg);
    }
  } catch (e) {}
});