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

  // Mobile: slide-in / offcanvas sidebar
  function setNavOpen(open) {
    if (!portal) return;
    portal.classList.toggle('nav-open', open);
    if (toggle) toggle.setAttribute('aria-expanded', String(open));
  }
  function closeNav() { setNavOpen(false); }

  // Desktop/tablet: collapse sidebar to icon-only rail
  function setSidebarCollapsed(collapsed) {
    if (!portal) return;
    portal.classList.toggle('sidebar-collapsed', collapsed);
    if (toggle) toggle.setAttribute('aria-expanded', String(!collapsed));
  }

  if (toggle) {
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (mobileQuery.matches) {
        setNavOpen(!portal.classList.contains('nav-open'));
      } else {
        setSidebarCollapsed(!portal.classList.contains('sidebar-collapsed'));
      }
    });
  }

  // Click outside (the scrim) closes the mobile offcanvas menu
  if (scrim) scrim.addEventListener('click', closeNav);

  // Esc closes the mobile offcanvas menu
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeNav();
  });

  // Reset both sidebar states when crossing the mobile/desktop breakpoint,
  // so resizing the window never leaves the sidebar in a stuck state.
  function handleBreakpointChange() {
    if (!portal) return;
    portal.classList.remove('nav-open');
    portal.classList.remove('sidebar-collapsed');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
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