/* Diagrams B: fig-hero, fig-buybox, fig-models, fig-sellers, fig-process, fig-transition.
   The HTML already holds the finished picture, so the page reads correctly with no script.
   This file refreshes the hooked text from site data, plays a short reveal on scroll (HX.reveal, skipped for
   reduced motion or without GSAP) and runs the card taps in fig-models. Every block is guarded: a missing
   element or data key means that block quietly does nothing. */
(function () {
  "use strict";

  var HX = window.HX;
  if (!HX || typeof HX.ready !== "function") { return; }
  var doc = document;

  function one(sel, root) {
    try { return (root || doc).querySelector(sel); } catch (e) { return null; }
  }
  function all(sel, root) {
    try { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); } catch (e) { return []; }
  }
  function safe(fn) {
    try { fn(); } catch (e) { /* one figure must never break the others */ }
  }

  /* First step of every figure.
     1. Same job as build.py: put HX.fmt(HX.get(k), f) into every hooked element. Missing data keeps the static text.
     2. Some screen readers drop list semantics when list-style is none, so the lists say role="list" outright. */
  function prep(root) {
    all("[data-k]", root).forEach(function (el) {
      var v = HX.get(el.getAttribute("data-k"));
      if (v === undefined || v === null) { return; }
      el.textContent = HX.fmt(v, el.getAttribute("data-f") || "raw");
    });
    all("ul, ol", root).forEach(function (l) {
      if (!l.getAttribute("role")) { l.setAttribute("role", "list"); }
    });
  }

  /* tl.from(...) on every match of sel inside root; skipped quietly when nothing matches */
  function from(tl, root, sel, vars, pos) {
    var t = all(sel, root);
    if (t.length) { tl.from(t, vars, pos); }
  }

  function wide() {
    return !!(window.matchMedia && window.matchMedia("(min-width:720px)").matches);
  }

  /* "$32.4B" becomes {pre:"$", val:32.4, dec:1, comma:false, post:"B"}; null when there is no number to count */
  function parseDisplay(s) {
    var m = /^(\D*?)(\d[\d,]*(?:\.\d+)?)(.*)$/.exec(String(s));
    if (!m) { return null; }
    var raw = m[2];
    var val = parseFloat(raw.replace(/,/g, ""));
    if (!isFinite(val)) { return null; }
    var dot = raw.indexOf(".");
    return { pre: m[1], post: m[3], val: val, dec: dot < 0 ? 0 : raw.length - dot - 1, comma: raw.indexOf(",") > -1 };
  }
  function render(p, v) {
    var s = v.toFixed(p.dec);
    if (p.comma) {
      var parts = s.split(".");
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      s = parts.join(".");
    }
    return p.pre + s + p.post;
  }

  /* ---------- fig-hero ---------- */
  function initHero() {
    var root = one("#fig-hero");
    if (!root) { return; }
    prep(root);

    /* the numeric part of each tile counts up once; the markup already shows the final text */
    var nums = [];
    all(".fig-hero-big", root).forEach(function (el) {
      var text = el.textContent, p = parseDisplay(text);
      if (p) { nums.push({ el: el, text: text, p: p }); }
    });

    /* the shop settles, the stack slides in from the bottom up, then the cash loop and the tiles appear.
       The idle drifting of the coins and the flowing dashes is CSS only. */
    HX.reveal(root, function (tl, el) {
      from(tl, el, ".fig-hero-shop", { opacity: 0, y: 14 }, 0);
      from(tl, el, ".fig-hero-ly", { opacity: 0, y: 26, stagger: { each: 0.15, from: "end" } }, 0.3);
      from(tl, el, ".fig-hero-flow-g", { opacity: 0 }, 1.1);
      from(tl, el, ".fig-hero-coins", { opacity: 0 }, 1.4);
      from(tl, el, ".fig-hero-tile", { opacity: 0, y: 12, stagger: 0.1 }, 0.5);
      if (nums.length) {
        var o = { v: 0 };
        tl.to(o, {
          v: 1,
          duration: 1.6,
          ease: "power2.out",
          onUpdate: function () {
            nums.forEach(function (n) { n.el.textContent = render(n.p, n.p.val * o.v); });
          },
          onComplete: function () {
            nums.forEach(function (n) { n.el.textContent = n.text; });
          }
        }, 0.5);
      }
    });
  }

  /* ---------- fig-buybox ---------- */
  function initBuybox() {
    var root = one("#fig-buybox");
    if (!root) { return; }
    prep(root);
    HX.reveal(root, function (tl, el) {
      /* headers and checks appear one by one, in reading order */
      from(tl, el, ".fig-buybox-h, .fig-buybox-item", { opacity: 0, x: -12, stagger: 0.1 }, 0);
      from(tl, el, ".fig-buybox-ck", { scale: 0, transformOrigin: "50% 50%", duration: 0.4, stagger: 0.1 }, 0.15);
    });
  }

  /* ---------- fig-models ---------- */
  function initModels() {
    var root = one("#fig-models");
    if (!root) { return; }
    prep(root);
    var cards = all(".fig-models-card", root);
    var live = one(".fig-models-live", root);
    var hint = one(".fig-models-hint", root);

    function say(text) { if (live) { live.textContent = text || ""; } }

    function setOpen(card, open, quiet) {
      var b = one(".fig-models-btn", card), r = one(".fig-models-res", card);
      if (!b || !r) { return; }
      b.setAttribute("aria-expanded", open ? "true" : "false");
      r.hidden = !open;
      if (quiet) { return; }
      var n = one(".fig-models-name", card), v = one(".fig-models-rv", card);
      say((n ? n.textContent : "") + (open ? ": " + (v ? v.textContent : "") : ": evidence hidden"));
    }

    if (cards.length) {
      /* with script, the evidence lines start folded (except on the highlighted card); without it they all show */
      root.classList.add("fig-models-js");
      if (hint) { hint.hidden = false; }
    }
    cards.forEach(function (card) {
      var b = one(".fig-models-btn", card), r = one(".fig-models-res", card);
      if (!b || !r) { return; }
      setOpen(card, card.classList.contains("fig-models-mine"), true);
      card.addEventListener("click", function (ev) {
        var t = ev.target;
        if (t && t.closest && t.closest(".fig-models-res")) { return; }
        setOpen(card, r.hidden);
      });
      /* keyboard users: arriving on a card reveals it (tap and mouse use the click above) */
      b.addEventListener("focus", function () {
        var kb = false;
        try { kb = b.matches(":focus-visible"); } catch (e) { kb = false; }
        if (kb && r.hidden) { setOpen(card, true); }
      });
    });

    HX.reveal(root, function (tl, el) {
      from(tl, el, ".fig-models-card", { opacity: 0, y: 14, stagger: 0.1 }, 0);
    });
  }

  /* ---------- fig-sellers ---------- */
  function initSellers() {
    var root = one("#fig-sellers");
    if (!root) { return; }
    prep(root);
    HX.reveal(root, function (tl, el) {
      var across = wide();
      var rail = one(".fig-sellers-rail", el);
      /* the rail draws first, then each rung of the ladder in order, then the two side channels */
      if (rail) {
        tl.from(rail, across ? { scaleX: 0, transformOrigin: "0% 50%", duration: 1.1 } : { scaleY: 0, transformOrigin: "50% 0%", duration: 1.1 }, 0);
      }
      from(tl, el, ".fig-sellers-rung", across ? { opacity: 0, y: 14, stagger: 0.28 } : { opacity: 0, x: -12, stagger: 0.28 }, 0.1);
      from(tl, el, ".fig-sellers-sidehead", { opacity: 0, y: 8 }, 1.0);
      from(tl, el, ".fig-sellers-side .fig-sellers-card", { opacity: 0, y: 12, stagger: 0.15 }, 1.1);
    });
  }

  /* ---------- fig-process ---------- */
  function initProcess() {
    var root = one("#fig-process");
    if (!root) { return; }
    prep(root);
    HX.reveal(root, function (tl, el) {
      /* steps drop in one by one while the funnel grows downward with them */
      from(tl, el, ".fig-process-step", { opacity: 0, y: 12, stagger: 0.14 }, 0);
      from(tl, el, ".fig-process-shape", { scaleY: 0, transformOrigin: "50% 0%", duration: 0.5, stagger: 0.14 }, 0);
      from(tl, el, ".fig-process-bar", { scaleX: 0, transformOrigin: "0% 50%", duration: 0.7, stagger: 0.12 }, 1.0);
      from(tl, el, ".fig-process-total, .fig-process-note", { opacity: 0, y: 8, stagger: 0.1 }, 1.3);
    });
  }

  /* ---------- fig-transition ---------- */
  function initTransition() {
    var root = one("#fig-transition");
    if (!root) { return; }
    prep(root);
    /* the label on each phase follows the data: an example plan, or the rule itself */
    all(".fig-transition-plan", root).forEach(function (el) {
      var plan = HX.get("transition.phases[key=" + el.getAttribute("data-key") + "].plan");
      if (plan === undefined || plan === null) { return; }
      el.textContent = plan ? "An example plan" : "The rule, not a plan";
      if (plan) { el.classList.remove("is-rule"); } else { el.classList.add("is-rule"); }
    });
    HX.reveal(root, function (tl, el) {
      var across = wide();
      from(tl, el, ".fig-transition-step", { opacity: 0, y: 12, stagger: 0.22 }, 0);
      from(tl, el, ".fig-transition-sel", across ? { scaleY: 0, transformOrigin: "50% 0%", duration: 0.8, stagger: 0.22 } : { scaleX: 0, transformOrigin: "0% 50%", duration: 0.8, stagger: 0.22 }, 0.1);
      from(tl, el, ".fig-transition-limit", { opacity: 0, y: 8 }, 0.9);
    });
  }

  HX.ready(function () {
    safe(initHero);
    safe(initBuybox);
    safe(initModels);
    safe(initSellers);
    safe(initProcess);
    safe(initTransition);
  });
})();
