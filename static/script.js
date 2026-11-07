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

  // 4b. Comparison background switch (satellite / drone): swaps both images and the credit.
  document.querySelectorAll('.compare-switch').forEach(function (group) {
    var figure = group.nextElementSibling;
    if (!figure || !figure.classList.contains('compare')) return;
    var imgs = figure.querySelectorAll('.compare-pane img'); // [before, after]
    var credit = figure.querySelector('.compare-credit');
    var buttons = group.querySelectorAll('button');
    group.hidden = false;
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var d = button.dataset;
        [['before', imgs[0]], ['after', imgs[1]]].forEach(function (pair) {
          var img = pair[1], k = pair[0];
          if (d[k + 'Srcset']) img.srcset = d[k + 'Srcset']; else img.removeAttribute('srcset');
          img.src = d[k + 'Src'];
          img.alt = d[k + 'Alt'];
        });
        if (credit) credit.textContent = d.credit;
        buttons.forEach(function (b) { b.setAttribute('aria-pressed', b === button ? 'true' : 'false'); });
      });
    });
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

  // 7. Photo viewer (place pages): the grid links stay plain links to the large
  // image; with <dialog> support a click opens them in one shared viewer.
  // The hash (#photo-3) records the open photo, so Back closes the viewer.
  var viewer = document.querySelector('dialog.viewer');
  var photoLinks = document.querySelectorAll('.gallery a[data-index]');
  if (viewer && photoLinks.length && typeof HTMLDialogElement === 'function' && viewer.showModal) {
    var vImg = viewer.querySelector('img');
    var vCaption = viewer.querySelector('.viewer-caption');
    var vCredit = viewer.querySelector('.viewer-credit');
    var current = 0;
    var opener = null;       // the link that opened the viewer: focus goes back to it
    var pushed = false;      // true when opening added a history entry
    var hashRe = /^#photo-(\d+)$/;

    var show = function (i) {
      var n = photoLinks.length;
      current = (i + n) % n; // wraps at both ends
      var a = photoLinks[current];
      var thumb = a.querySelector('img');
      vImg.srcset = a.dataset.srcset || '';
      vImg.sizes = '100vw';
      vImg.src = a.href;
      vImg.alt = thumb ? thumb.alt : '';
      vCaption.textContent = a.querySelector('.gallery-caption').textContent;
      vCredit.textContent = a.querySelector('.gallery-credit').textContent;
      var next = photoLinks[(current + 1) % n]; // preload the next one
      var pre = new Image();
      pre.sizes = '100vw';
      pre.srcset = next.dataset.srcset || '';
      pre.src = next.href;
    };
    var openAt = function (i, fromHistory) {
      if (!viewer.open) {
        opener = photoLinks[((i % photoLinks.length) + photoLinks.length) % photoLinks.length];
        viewer.showModal();
      }
      show(i);
      var hash = '#photo-' + (current + 1);
      if (fromHistory) return;
      if (hashRe.test(location.hash) || pushed) {
        history.replaceState(null, '', hash); // moving between photos: keep one entry
      } else {
        history.pushState(null, '', hash);
        pushed = true;
      }
    };
    var step = function (d) { openAt(current + d); };

    photoLinks.forEach(function (a) {
      a.addEventListener('click', function (event) {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.button) return; // keep "open in new tab"
        event.preventDefault();
        openAt(parseInt(a.dataset.index, 10));
      });
    });
    viewer.querySelector('.viewer-prev').addEventListener('click', function () { step(-1); });
    viewer.querySelector('.viewer-next').addEventListener('click', function () { step(1); });
    viewer.querySelector('.viewer-close').addEventListener('click', function () { viewer.close(); });
    viewer.addEventListener('click', function (event) {
      if (event.target === viewer) viewer.close(); // click on the backdrop
    });
    viewer.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft') { event.preventDefault(); step(-1); }
      else if (event.key === 'ArrowRight') { event.preventDefault(); step(1); }
    });
    // Swipe: a mostly horizontal move of more than 50px.
    var startX = 0, startY = 0;
    viewer.addEventListener('pointerdown', function (event) { startX = event.clientX; startY = event.clientY; });
    viewer.addEventListener('pointerup', function (event) {
      var dx = event.clientX - startX, dy = event.clientY - startY;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) step(dx < 0 ? 1 : -1);
    });
    // Esc, the close button and Back all end here.
    viewer.addEventListener('close', function () {
      if (opener) opener.focus();
      if (hashRe.test(location.hash)) {
        if (pushed) history.back(); else history.replaceState(null, '', location.pathname + location.search);
      }
      pushed = false;
    });
    window.addEventListener('popstate', function () {
      var m = hashRe.exec(location.hash);
      if (!m) {
        pushed = false; // the entry is already gone
        if (viewer.open) viewer.close();
      } else if (+m[1] >= 1 && +m[1] <= photoLinks.length) {
        openAt(+m[1] - 1, true);
      }
    });
    var first = hashRe.exec(location.hash); // a link to one photo
    if (first && +first[1] >= 1 && +first[1] <= photoLinks.length) openAt(+first[1] - 1, true);
  }
})();
