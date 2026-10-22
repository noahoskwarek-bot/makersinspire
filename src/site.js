// Makers Inspire: tiny first-party script (menu, gallery, lightbox, forms). No trackers, no third-party code.
(function () {
  var btn = document.querySelector('.menu-btn'), nav = document.getElementById('site-nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open'); btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  // Gallery: native horizontal swipe (scroll-snap); thumbnails scroll to a photo and track the current one.
  document.querySelectorAll('[data-gallery]').forEach(function (g) {
    var track = g.querySelector('.slides'), th = g.querySelectorAll('.thumbs a');
    if (!track) return;
    function mark() {
      var i = Math.round(track.scrollLeft / Math.max(1, track.clientWidth));
      th.forEach(function (a, k) { a.classList.toggle('on', k === i); });
    }
    th.forEach(function (a) {
      a.addEventListener('click', function (ev) {
        ev.preventDefault();
        var k = +a.getAttribute('data-go');
        track.scrollTo({ left: k * track.clientWidth, behavior: 'smooth' });
      });
    });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(mark); }, { passive: true });
    track.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
        ev.preventDefault();
        track.scrollBy({ left: (ev.key === 'ArrowRight' ? 1 : -1) * track.clientWidth, behavior: 'smooth' });
      }
    });
    mark();
  });

  // Tap to enlarge (native <dialog>).
  var lb = document.querySelector('.lightbox');
  if (lb && lb.showModal) {
    var img = lb.querySelector('img');
    document.addEventListener('click', function (ev) {
      var z = ev.target.closest && ev.target.closest('.zoom');
      if (z) { img.src = z.getAttribute('data-full'); img.alt = z.getAttribute('data-alt') || ''; lb.showModal(); return; }
      if (ev.target === lb || (ev.target.closest && ev.target.closest('.lb-close'))) lb.close();
    });
  }

  // Contact form: prefill the piece name from ?piece=<name> (the 'Ask about this piece' button).
  var pf = document.querySelector('[data-piece-field]');
  if (pf) {
    var slug = new URLSearchParams(location.search).get('piece');
    if (slug) pf.value = slug;
  }

  // Forms. With form_endpoint (site.json) the form POSTs there; for the contact form the subject names the piece.
  // Without it (data-mailto): after the browser's own validation, open the visitor's email app with a prefilled message.
  function subjectFor(f) {
    var piece = f.querySelector('[name="piece"]');
    var p = piece && piece.value.trim();
    return f.getAttribute('data-kind') === 'contact' && p ? 'Question about ' + p : f.getAttribute('data-subject');
  }
  document.querySelectorAll('form.form').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
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
