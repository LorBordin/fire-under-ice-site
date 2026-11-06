// Fire Under Ice - small enhancements. The page works without this file;
// everything here only adds polish. No libraries.
(function () {
  'use strict';

  // Only this file adds the 'js' class: if it fails to load, CSS never hides anything.
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
      iframe.title = (link.dataset.title || 'Video') + ' (YouTube video)';
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

  // 6. 3D model: nothing heavy loads until the visitor clicks "Explore in 3D".
  // The viewer (<model-viewer>, self-hosted) needs WebGL; without it the
  // button stays hidden and the still image remains.
  var canDraw3D = (function () {
    try {
      var c = document.createElement('canvas');
      return !!(window.customElements && (c.getContext('webgl2') || c.getContext('webgl')));
    } catch (e) { return false; }
  })();
  var VIEWER = 'static/vendor/model-viewer-4.0.0.min.js';
  document.querySelectorAll('figure[data-model]').forEach(function (fig) {
    var button = fig.querySelector('.model-load');
    var img = fig.querySelector('img');
    if (!button || !img || !canDraw3D) return;
    button.hidden = false;
    button.addEventListener('click', function () {
      button.disabled = true;
      button.textContent = 'Loading 3D model…';
      if (!document.querySelector('script[src="' + VIEWER + '"]')) {
        var s = document.createElement('script');
        s.type = 'module';
        s.src = VIEWER;
        document.head.appendChild(s);
      }
      var mv = document.createElement('model-viewer');
      mv.className = 'model-view';
      mv.setAttribute('src', fig.dataset.model);
      mv.setAttribute('alt', fig.dataset.modelAlt || '3D model');
      mv.setAttribute('poster', img.currentSrc || img.src); // same picture until the model is ready
      mv.setAttribute('camera-controls', '');
      mv.setAttribute('touch-action', 'pan-y');          // vertical swipes still scroll the page
      mv.setAttribute('interaction-prompt', 'none');
      var narrow = window.matchMedia('(max-width: 47.99rem)').matches; // square box on phones: start further out
      mv.setAttribute('camera-orbit', '180deg 62deg ' + (narrow ? '80%' : '55%')); // from the north, lake in front, as in the picture
      mv.setAttribute('min-camera-orbit', 'auto 0deg auto');
      mv.setAttribute('max-camera-orbit', 'auto 88deg auto'); // never below the ground
      mv.setAttribute('loading', 'eager');
      mv.setAttribute('reveal', 'auto');
      if (!reduceMotion) {
        mv.setAttribute('auto-rotate', '');
        mv.setAttribute('rotation-per-second', '8deg');
      }
      if (fig.dataset.modelMarker) {
        // Same orange ring as in the picture, pinned to the cave in 3D.
        var ring = document.createElement('div');
        ring.className = 'model-ring';
        ring.slot = 'hotspot-cave';
        ring.dataset.position = fig.dataset.modelMarker;
        ring.dataset.normal = '0m 1m 0m';
        ring.setAttribute('aria-label', 'The cave');
        mv.appendChild(ring);
      }
      mv.addEventListener('load', function () {
        img.remove(); // the viewer is already in its place
        var hint = document.createElement('p');
        hint.className = 'model-hint';
        hint.textContent = 'Drag to rotate, scroll or pinch to zoom, two fingers or right-drag to move.';
        button.replaceWith(hint);
      });
      mv.addEventListener('error', function () {
        mv.remove();
        img.style.display = '';
        button.disabled = false;
        button.textContent = 'Could not load the 3D model. Try again';
      });
      // Show the viewer (with its progress bar) in place of the picture right away.
      img.style.display = 'none'; // (the hidden attribute loses to the CSS img rule)
      img.after(mv);
    });
  });
})();
