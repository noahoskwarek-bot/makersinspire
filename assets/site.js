// Makers Inspire: tiny first-party script (menu, gallery, lightbox, forms). No trackers, no third-party code.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var behavior = reduce ? 'auto' : 'smooth';

  // Menu: aria-expanded on the button; Escape or choosing a link closes it and returns focus to the button.
  var btn = document.querySelector('.menu-btn'), nav = document.getElementById('site-nav');
  if (btn && nav) {
    var setMenu = function (open, focusBtn) {
      nav.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (!open && focusBtn) btn.focus();
    };
    btn.addEventListener('click', function () { setMenu(btn.getAttribute('aria-expanded') !== 'true', false); });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') setMenu(false, true);
    });
    document.addEventListener('click', function (ev) {
      if (btn.getAttribute('aria-expanded') === 'true' && !nav.contains(ev.target) && !btn.contains(ev.target)) setMenu(false, false);
    });
  }

  // Gallery: native horizontal swipe (scroll-snap); thumbnails jump to a photo and mark the current one (aria-current).
  document.querySelectorAll('[data-gallery]').forEach(function (g) {
    var track = g.querySelector('.slides'), th = g.querySelectorAll('.thumbs a');
    if (!track) return;
    var count = track.children.length;
    function current() { return Math.max(0, Math.min(count - 1, Math.round(track.scrollLeft / Math.max(1, track.clientWidth)))); }
    function mark() {
      var i = current();
      th.forEach(function (a, k) { if (k === i) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
    }
    function go(k) { track.scrollTo({ left: k * track.clientWidth, behavior: behavior }); }
    th.forEach(function (a) {
      a.addEventListener('click', function (ev) { ev.preventDefault(); go(+a.getAttribute('data-go')); });
    });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(mark); }, { passive: true });
    track.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
        ev.preventDefault();
        go(Math.max(0, Math.min(count - 1, current() + (ev.key === 'ArrowRight' ? 1 : -1))));
      }
    });
    mark();
  });

  // Lightbox: native modal <dialog> (focus stays inside it; Escape closes). Previous/Next buttons and arrow keys,
  // a live "Photo 2 of 4" count, and focus goes back to the photo that opened it.
  var lb = document.querySelector('.lightbox');
  if (lb && lb.showModal) {
    var img = lb.querySelector('img'), cnt = lb.querySelector('.lb-count');
    var zooms = Array.prototype.slice.call(document.querySelectorAll('.zoom')), at = 0, opener = null;
    var show = function (k) {
      at = (k + zooms.length) % zooms.length;
      var z = zooms[at];
      img.removeAttribute('srcset');
      if (z.getAttribute('data-srcset')) { img.srcset = z.getAttribute('data-srcset'); img.sizes = '100vw'; }
      img.src = z.getAttribute('data-full');
      img.alt = z.getAttribute('data-alt') || '';
      lb.setAttribute('aria-label', 'Enlarged photo ' + (at + 1) + ' of ' + zooms.length);
      if (cnt) cnt.textContent = zooms.length > 1 ? 'Photo ' + (at + 1) + ' of ' + zooms.length : '';
    };
    zooms.forEach(function (z, k) {
      z.addEventListener('click', function () {
        opener = z; show(k); lb.showModal();
        var c = lb.querySelector('.lb-close'); if (c) c.focus();
      });
    });
    lb.addEventListener('click', function (ev) {
      var t = ev.target;
      if (t === lb || t.closest('.lb-close')) lb.close();
      else if (t.closest('.lb-prev')) show(at - 1);
      else if (t.closest('.lb-next')) show(at + 1);
    });
    lb.addEventListener('keydown', function (ev) {
      if (ev.key === 'Tab') {  // keep Tab inside the dialog's buttons
        var bs = lb.querySelectorAll('button'), f0 = bs[0], fl = bs[bs.length - 1];
        if (ev.shiftKey && document.activeElement === f0) { ev.preventDefault(); fl.focus(); }
        else if (!ev.shiftKey && document.activeElement === fl) { ev.preventDefault(); f0.focus(); }
      }
      if (ev.key === 'ArrowRight') { ev.preventDefault(); show(at + 1); }
      if (ev.key === 'ArrowLeft') { ev.preventDefault(); show(at - 1); }
    });
    lb.addEventListener('close', function () {
      // return focus to the photo now showing (scrolling the gallery to it), else the one that opened the lightbox
      var z = zooms[at] || opener;
      if (z) {
        var track = z.closest('.slides');
        if (track) track.scrollTo({ left: at * track.clientWidth, behavior: 'auto' });
        z.focus({ preventScroll: true });
      }
    });
  }

  // Contact form: prefill the piece name from ?piece=<name> (the 'Ask about this piece' button).
  var pf = document.querySelector('[data-piece-field]');
  if (pf) {
    var slug = new URLSearchParams(location.search).get('piece');
    if (slug) pf.value = slug;
  }

  // Form validation: inline messages tied to each field (aria-describedby + aria-invalid), focus moves to the first
  // problem. Without JavaScript the browser's own validation still runs.
  function errFor(el) {
    if (el.validity.valid) return '';
    if (el.validity.typeMismatch && el.getAttribute('data-err-type')) return el.getAttribute('data-err-type');
    return el.getAttribute('data-err') || 'Please fill in this field.';
  }
  function setErr(el, msg) {
    var id = el.id + '-err', p = document.getElementById(id);
    if (msg) {
      if (!p) { p = document.createElement('p'); p.className = 'err'; p.id = id; el.insertAdjacentElement('afterend', p); }
      p.textContent = msg;
      el.setAttribute('aria-invalid', 'true');
      var d = (el.getAttribute('aria-describedby') || '').split(' ').filter(function (x) { return x && x !== id; });
      d.push(id); el.setAttribute('aria-describedby', d.join(' '));
    } else {
      if (p) p.remove();
      el.removeAttribute('aria-invalid');
      var rest = (el.getAttribute('aria-describedby') || '').split(' ').filter(function (x) { return x && x !== id; });
      if (rest.length) el.setAttribute('aria-describedby', rest.join(' ')); else el.removeAttribute('aria-describedby');
    }
  }
  function validate(f) {
    var bad = null;
    f.querySelectorAll('input[required],textarea[required]').forEach(function (el) {
      var m = errFor(el); setErr(el, m); if (m && !bad) bad = el;
    });
    return bad;
  }

  // Forms. With form_endpoint (site.json) the form POSTs there; for the contact form the subject names the piece.
  // Without it (data-mailto): open the visitor's email app with a prefilled message.
  function subjectFor(f) {
    var piece = f.querySelector('[name="piece"]');
    var p = piece && piece.value.trim();
    return f.getAttribute('data-kind') === 'contact' && p ? 'Question about ' + p : f.getAttribute('data-subject');
  }
  document.querySelectorAll('form.form').forEach(function (f) {
    f.setAttribute('novalidate', '');
    f.querySelectorAll('input[required],textarea[required]').forEach(function (el) {
      el.addEventListener('blur', function () { if (el.getAttribute('aria-invalid') === 'true' || el.value) setErr(el, errFor(el)); });
      el.addEventListener('input', function () { if (el.getAttribute('aria-invalid') === 'true') setErr(el, errFor(el)); });
    });
    f.addEventListener('submit', function (ev) {
      var bad = validate(f);
      if (bad) { ev.preventDefault(); bad.focus(); return; }
      var to = f.getAttribute('data-mailto');
      if (to === null) {  // POST to the endpoint
        var sub = f.querySelector('input[name="_subject"]');
        if (sub) sub.value = subjectFor(f);
        return;
      }
      ev.preventDefault();
      if (!to) return;
      var lines = [];
      f.querySelectorAll('[data-label]').forEach(function (el) {
        var v = el.value.trim();
        if (v) lines.push(el.getAttribute('data-label') + ': ' + v);
      });
      var href = 'mailto:' + to + '?subject=' + encodeURIComponent(subjectFor(f)) + '&body=' + encodeURIComponent(lines.join('\n'));
      var s = f.querySelector('.form-status');
      if (s) { s.hidden = false; s.focus(); }
      window.location.href = href;
    });
  });
})();
