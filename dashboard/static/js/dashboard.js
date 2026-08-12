document.addEventListener('DOMContentLoaded', function () {
  var portal = document.getElementById('portal');
  var toggle = document.getElementById('sidebarToggle');
  var scrim = document.getElementById('sidebarScrim');

  function closeNav() { portal.classList.remove('nav-open'); }
  if (toggle) toggle.addEventListener('click', function () { portal.classList.toggle('nav-open'); });
  if (scrim) scrim.addEventListener('click', closeNav);

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