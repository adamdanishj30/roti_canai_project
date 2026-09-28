/* Jar&Maz motion layer (vanilla JS, no dependencies).
   To revert: delete the <script ...enhance.js> and <link ...enhance.css> tags in index.html. */
(function () {
  'use strict';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var main = $('.main');
  var banner = $('.banner');

  /* ---------- 1. Scroll reveal ---------- */
  var io = null;
  if (!reduce && 'IntersectionObserver' in window) {
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        io.unobserve(el);
        el.classList.add('in');
        setTimeout(function () { el.classList.remove('rv'); el.style.removeProperty('--rd'); }, 1400);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -5% 0px' });
  }
  function reveal(el, delay) {
    if (!io || el.classList.contains('rv') || el.classList.contains('in')) return;
    el.style.setProperty('--rd', (delay || 0) + 'ms');
    el.classList.add('rv');
    io.observe(el);
  }
  $$('.steps div').forEach(function (el, i) { reveal(el, i * 120); });
  $$('.fb').forEach(function (el) { reveal(el, 0); });

  /* ---------- 2. Product cards: offscreen reveal + image shimmer ---------- */
  var grid = $('#grid');
  function cols(g) {
    try { return getComputedStyle(g).gridTemplateColumns.split(' ').length || 1; } catch (e) { return 1; }
  }
  function handleCards() {
    if (!grid) return;
    var n = cols(grid), vh = window.innerHeight;
    $$('.card', grid).forEach(function (c, i) {
      var ph = $('.ph', c), img = $('.ph img', c);
      if (ph && img && !img.complete) {
        ph.classList.add('hk-load');
        var done = function () { ph.classList.remove('hk-load'); };
        img.addEventListener('load', done, { once: true });
        img.addEventListener('error', done, { once: true });
      }
      if (!io || c.dataset.hk) return;
      c.dataset.hk = '1';
      if (c.getBoundingClientRect().top > vh * 0.92) {
        c.style.animation = 'none';
        reveal(c, (i % n) * 90);
      }
    });
  }
  if (grid && 'MutationObserver' in window) {
    var pend = false;
    new MutationObserver(function () {
      if (pend) return;
      pend = true;
      requestAnimationFrame(function () { pend = false; handleCards(); });
    }).observe(grid, { childList: true });
  }
  handleCards();

  /* ---------- 3. Sliding tab indicator (desktop CSS only shows it) ---------- */
  var tabs = $('.tabs');
  if (tabs) {
    var ink = document.createElement('span');
    ink.className = 'hk-ink';
    ink.style.transition = 'none';
    tabs.appendChild(ink);
    var placeInk = function () {
      var on = $('button.on', tabs);
      if (!on) return;
      ink.style.width = on.offsetWidth + 'px';
      ink.style.transform = 'translateX(' + on.offsetLeft + 'px)';
    };
    placeInk();
    requestAnimationFrame(function () { ink.style.transition = ''; });
    if ('MutationObserver' in window) {
      new MutationObserver(placeInk).observe(tabs, { attributes: true, attributeFilter: ['class'], subtree: true, characterData: true, childList: true });
    }
    window.addEventListener('resize', placeInk);
    window.addEventListener('load', placeInk);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeInk);
  }

  /* ---------- 4. Hero: steam + parallax ---------- */
  if (banner && !reduce) {
    var wrap = document.createElement('div');
    wrap.className = 'hk-steam';
    wrap.setAttribute('aria-hidden', 'true');
    var count = window.innerWidth < 600 ? 6 : 9;
    for (var i = 0; i < count; i++) {
      var s = document.createElement('i');
      s.style.cssText =
        '--x:' + (6 + i * (88 / count) + Math.random() * 4).toFixed(1) + '%;' +
        '--s:' + (26 + Math.floor(Math.random() * 34)) + 'px;' +
        '--d:' + (6 + Math.random() * 5).toFixed(1) + 's;' +
        '--dl:-' + (Math.random() * 8).toFixed(1) + 's;' +
        '--dx:' + Math.floor(Math.random() * 50 - 25) + 'px';
      wrap.appendChild(s);
    }
    banner.appendChild(wrap);
  }

  var base = null, ticking = false;
  var railHome = $('.rail a[href="#top"]');
  var railMenu = $('.rail a[href="#menu"]');
  function frame() {
    ticking = false;
    if (banner && !reduce) {
      var r = banner.getBoundingClientRect();
      if (base === null) base = r.top;
      var py = Math.max(-10, Math.min(10, (base - r.top) * 0.08));
      banner.style.setProperty('--py', py.toFixed(1) + 'px');
    }
    if (tabs && railHome && railMenu) {
      var inMenu = tabs.getBoundingClientRect().top < window.innerHeight * 0.45;
      railMenu.classList.toggle('cur', inMenu);
      railHome.classList.toggle('cur', !inMenu);
    }
  }
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(frame);
  }
  if (main) main.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  requestAnimationFrame(frame);
})();
