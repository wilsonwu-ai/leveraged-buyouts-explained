/* Shared helpers for every figure script (window.HX). Loaded after data.js and GSAP, before the figure scripts.
   The number formats here match build.py exactly, so text filled at build time and text updated in the browser agree. */
(function () {
  "use strict";
  var D = window.SITE_DATA || {};
  var reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  if (window.gsap && window.ScrollTrigger) window.gsap.registerPlugin(window.ScrollTrigger);

  /* get("stack.a.dscr"), get("sens[multiple=4.5].dscr"), get("scenarios.base.bridge.sale_price") */
  function get(path, root) {
    var cur = root || D;
    var parts = String(path).match(/[^.[\]]+|\[[^\]]+\]/g) || [];
    for (var i = 0; i < parts.length; i++) {
      if (cur == null) return undefined;
      var p = parts[i];
      if (p.charAt(0) === "[") {
        var inner = p.slice(1, -1), eq = inner.indexOf("=");
        if (eq > 0) {
          var k = inner.slice(0, eq), v = inner.slice(eq + 1);
          cur = (cur || []).filter(function (o) { return o && String(o[k]) === v; })[0];
        } else { cur = cur[+inner]; }
      } else { cur = cur[p]; }
    }
    return cur;
  }

  function loc(a, d) { return a.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }); }

  /* Half-up rounding to d decimals; build.py uses the same steps, so build-time and browser text agree. */
  function rnd(a, d) { var m = Math.pow(10, d); return Math.floor(a * m + 0.5) / m; }

  /* Formats (values are in dollars unless noted): d0 ($1,234,567), K0 ($647K), M1 ($4.0M), M2 ($3.83M),
     x1 (4.0x), x2 (1.33x), p0 (10%), p1 (66.1%), n0 (1,000), n1 (8.1), raw. Negative numbers get a leading hyphen-minus. */
  function fmt(v, f) {
    if (v == null) return "";
    if (f === "raw" || isNaN(+v)) return String(v);
    var n = +v, neg = n < 0, a = Math.abs(n), s;
    switch (f) {
      case "d0": s = "$" + loc(rnd(a, 0), 0); break;
      case "K0": s = "$" + loc(rnd(a / 1000, 0), 0) + "K"; break;
      case "M1": s = "$" + loc(rnd(a / 1e6, 1), 1) + "M"; break;
      case "M2": s = "$" + loc(rnd(a / 1e6, 2), 2) + "M"; break;
      case "x1": s = loc(rnd(a, 1), 1) + "x"; break;
      case "x2": s = loc(rnd(a, 2), 2) + "x"; break;
      case "p0": s = loc(rnd(a, 0), 0) + "%"; break;
      case "p1": s = loc(rnd(a, 1), 1) + "%"; break;
      case "n0": s = loc(rnd(a, 0), 0); break;
      case "n1": s = loc(rnd(a, 1), 1); break;
      default: return String(v);
    }
    return (neg ? "-" : "") + s;
  }

  function css(name) { return getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim(); }

  /* reveal(target, function (tl, el) { tl.from(...) }, {end: fn})
     Builds a paused GSAP timeline and plays it once when the figure scrolls into view.
     Without GSAP, or with reduced motion, nothing animates and opts.end(el) runs (the static state is the end state). */
  function reveal(target, build, opts) {
    var el = typeof target === "string" ? document.querySelector(target) : target;
    if (!el) return null;
    if (!window.gsap || reduced) { if (opts && opts.end) opts.end(el); return null; }
    var tl = window.gsap.timeline({ paused: true, defaults: { ease: "power2.out", duration: 0.7 } });
    build(tl, el);
    if (window.ScrollTrigger) {
      window.ScrollTrigger.create({ trigger: el, start: "top 80%", once: true, onEnter: function () { tl.play(); } });
    } else { tl.play(); }
    return tl;
  }

  /* chartReady(el): marks a .chart as drawn so its fallback table (the next sibling) becomes screen-reader only */
  function chartReady(el) { if (el) el.classList.add("is-ready"); }

  function ready(fn) {
    if (document.readyState !== "loading") fn(); else document.addEventListener("DOMContentLoaded", fn);
  }

  /* onResize(fn): debounced, width changes only (ignores mobile URL-bar height changes) */
  function onResize(fn) {
    var w = window.innerWidth, t;
    window.addEventListener("resize", function () {
      if (window.innerWidth === w) return;
      w = window.innerWidth; clearTimeout(t); t = setTimeout(fn, 150);
    });
  }

  /* Deep links: with smooth scrolling on, the browser animates a #hash landing, and ScrollTrigger's refresh on load
     can stop that animation part way down. Once everything has loaded, land on the target again, instantly. */
  window.addEventListener("load", function () {
    var id = decodeURIComponent(location.hash.slice(1));
    var target = id && document.getElementById(id);
    if (!target) return;
    setTimeout(function () {
      var root = document.documentElement, prev = root.style.scrollBehavior;
      root.style.scrollBehavior = "auto";
      target.scrollIntoView({ block: "start" });
      root.style.scrollBehavior = prev;
    }, 250);
  });

  window.HX = { data: D, get: get, fmt: fmt, css: css, reduced: reduced, reveal: reveal, chartReady: chartReady,
                ready: ready, onResize: onResize };
})();
