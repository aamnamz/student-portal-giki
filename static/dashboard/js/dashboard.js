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

  // Mobile: slide-in / offcanvas sidebar
  function setNavOpen(open) {
    if (!portal) return;
    portal.classList.toggle('nav-open', open);
    if (toggle) toggle.setAttribute('aria-expanded', String(open));
  }
  function closeNav() { setNavOpen(false); }

  // Desktop/tablet: collapse sidebar to icon-only rail.
  // `persist` is only true when the user explicitly clicks the toggle —
  // restoring the saved state on load/resize must never overwrite it.
  function setSidebarCollapsed(collapsed, persist) {
    if (!portal) return;
    portal.classList.toggle('sidebar-collapsed', collapsed);
    if (toggle) toggle.setAttribute('aria-expanded', String(!collapsed));
    if (persist) saveCollapsed(collapsed);
  }

  // Restore the user's last choice on every page load (desktop/tablet only —
  // mobile always shows the full-width offcanvas sidebar regardless of this).
  if (!mobileQuery.matches) {
    setSidebarCollapsed(getSavedCollapsed(), false);
  }

  // Browser back/forward can restore a page from bfcache without re-running
  // this script from scratch — re-apply the saved state in that case too.
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

  // Click outside (the scrim) closes the mobile offcanvas menu
  if (scrim) scrim.addEventListener('click', closeNav);

  // Esc closes the mobile offcanvas menu
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeNav();
  });

  // Crossing the mobile/desktop breakpoint only affects layout, never the
  // user's saved collapse preference: close the offcanvas menu on mobile,
  // and re-apply whatever was last saved when back on desktop/tablet.
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

  // Icon-rail tooltips: rendered as a single fixed-position element appended
  // to <body>, positioned via JS from each item's bounding box. This keeps
  // the tooltip completely outside the sidebar's own box, so it can never
  // widen or horizontally scroll the collapsed rail the way a CSS ::after
  // positioned inside the scrollable nav would.
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
  // Any of these mean the tooltip's position is no longer valid — drop it.
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

  // Animate progress ring + bar from 0 to their data-percent value
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

  // Animate the number inside the ring counting up
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
});