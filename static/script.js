// Fire Under Ice - small enhancements. The page works without this file;
// everything here only adds polish. No libraries.
(function () {
  'use strict';

  // 'js' class is also set inline in <head>; repeated here as a safety net.
  document.documentElement.classList.add('js');

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;

  // 1. Reveal sections as they scroll into view.
  var reveals = document.querySelectorAll('.reveal');
  if (!hasIO || reduceMotion) {
    reveals.forEach(function (el) { el.classList.add('visible'); });
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target); // only animate once
        }
      });
    }, { threshold: 0.08 });
    reveals.forEach(function (el) { revealObserver.observe(el); });
  }

  // 2. Hero parallax: the image moves at 0.3x scroll speed (transform only).
  var hero = document.querySelector('.hero');
  var heroImg = document.querySelector('.hero-img');
  if (hero && heroImg && hasIO && !reduceMotion) {
    var heroVisible = true;
    var ticking = false;
    var update = function () {
      heroImg.style.transform = 'translate3d(0,' + (window.scrollY * 0.3).toFixed(1) + 'px,0)';
      ticking = false;
    };
    new IntersectionObserver(function (entries) {
      heroVisible = entries[0].isIntersecting;
    }).observe(hero);
    window.addEventListener('scroll', function () {
      if (heroVisible && !ticking) {
        ticking = true;
        requestAnimationFrame(update); // at most one update per frame
      }
    }, { passive: true });
  }

  // 3. Mark the nav link of the section currently in view.
  var links = document.querySelectorAll('.site-header li a');
  if (hasIO && links.length) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        links.forEach(function (a) {
          if (a.getAttribute('href') === '#' + entry.target.id) {
            a.setAttribute('aria-current', 'true');
          } else {
            a.removeAttribute('aria-current');
          }
        });
      });
    }, { rootMargin: '-40% 0px -55% 0px' }); // a thin band near the viewport middle
    document.querySelectorAll('main > section[id]').forEach(function (s) {
      navObserver.observe(s);
    });
  }

  // 4. Before/after slider: the (hidden without JS) range input drives --pos.
  document.querySelectorAll('.compare').forEach(function (compare) {
    var input = compare.querySelector('input[type="range"]');
    if (!input) return;
    input.hidden = false;
    var setPos = function () { compare.style.setProperty('--pos', input.value + '%'); };
    input.addEventListener('input', setPos); // keyboard arrows work natively
    setPos();
  });

  // 5. Click-to-load video: no YouTube request until the visitor asks for it.
  document.querySelectorAll('.video[data-youtube]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      var iframe = document.createElement('iframe');
      iframe.src = 'https://www.youtube-nocookie.com/embed/' +
        encodeURIComponent(link.dataset.youtube) + '?autoplay=1';
      iframe.title = 'Kverkfjöll over time (YouTube video)';
      iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
      iframe.allowFullscreen = true;
      // Wrap it in a div with the same class so the 16:9 box is kept.
      var box = document.createElement('div');
      box.className = 'video';
      box.appendChild(iframe);
      link.replaceWith(box);
      iframe.focus();
    });
  });
})();
