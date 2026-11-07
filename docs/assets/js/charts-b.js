/* Leveraged buyouts, explained: charts-b (fig-team, fig-checklist, fig-ai, fig-sentiment).
   The static HTML is the finished picture: every person, question, tile and theme is readable with script off.
   This file adds the collapse, the toggles and the reveal on scroll, and draws the sentiment chart from site data.
   Every block is guarded: a missing element, library or data key means that block quietly does nothing. */
(function () {
  "use strict";
  if (!window.HX || typeof window.HX.ready !== "function") { return; }
  var HX = window.HX;

  /* ---------- helpers ---------- */
  function one(sel, root) { try { return (root || document).querySelector(sel); } catch (e) { return null; } }
  function all(sel, root) {
    try { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); } catch (e) { return []; }
  }
  function safe(fn) { try { fn(); } catch (e) { /* one figure must never break the others */ } }
  function isNum(v) { return typeof v === "number" && isFinite(v); }
  function text(el) { return el ? String(el.textContent || "").replace(/\s+/g, " ").trim() : ""; }
  function say(el, msg) { if (el) { el.textContent = msg || ""; } }
  function mk(tag, cls, txt, parent) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (txt != null) { n.textContent = txt; }
    if (parent) { parent.appendChild(n); }
    return n;
  }
  /* The "tap to ..." hints are hidden in the markup, because they only make sense once script is running. */
  function showHint(root, sel) {
    var h = one(sel, root);
    if (h) { h.hidden = false; }
  }
  /* Same job as build.py: put HX.fmt(HX.get(k), f) into every hooked element. Missing data leaves the static text. */
  function refreshHooks(root) {
    all("[data-k]", root).forEach(function (el) {
      var v = HX.get(el.getAttribute("data-k"));
      if (v === undefined || v === null) { return; }
      el.textContent = HX.fmt(v, el.getAttribute("data-f") || "raw");
    });
  }
  /* A guarded tl.from: an empty selection or a failed tween never stops the rest of the reveal. */
  function from(tl, root, sel, vars, at) {
    var list = all(sel, root);
    if (!list.length) { return; }
    try { tl.from(list, vars, at); } catch (e) { /* the static state stays */ }
  }

  /* ---------- fig-team ---------- */
  function team() {
    var root = one("#fig-team");
    if (!root) { return; }
    refreshHooks(root);
    var armed = 0;
    all(".fig-team-person", root).forEach(function (p) {
      var btn = one(".fig-team-btn", p), what = one(".fig-team-what", p);
      if (!btn || !what) { return; }
      armed += 1;
      function set(open) {
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        what.hidden = !open;
        p.classList.toggle("is-open", open);
      }
      set(false);
      btn.addEventListener("click", function () { set(btn.getAttribute("aria-expanded") !== "true"); });
    });
    if (armed) {
      root.classList.add("is-interactive");
      showHint(root, ".fig-team-hint");
    }
    HX.reveal(root, function (tl, el) {
      from(tl, el, ".fig-team-sellers .fig-team-person", { opacity: 0, x: -14, duration: 0.7, stagger: 0.1 }, 0);
      from(tl, el, ".fig-team-buyers .fig-team-person", { opacity: 0, x: 14, duration: 0.7, stagger: 0.08 }, 0);
      from(tl, el, ".fig-team-middle", { opacity: 0, scale: 0.96, duration: 0.7 }, 0.2);
    });
  }

  /* ---------- fig-checklist ---------- */
  function checklist() {
    var root = one("#fig-checklist");
    if (!root) { return; }
    var rows = all(".fig-checklist-row", root);
    if (!rows.length) { return; }
    var live = one(".fig-checklist-live", root);
    var seg = one(".seg", root);
    var modeBtns = seg ? all("button", seg) : [];

    function setOpen(row, open) {
      var head = one(".fig-checklist-head", row), panel = one(".fig-checklist-panel", row);
      if (!head || !panel) { return; }
      head.setAttribute("aria-expanded", open ? "true" : "false");
      panel.hidden = !open;
      row.classList.toggle("is-open", open);
    }
    function isDone(row) {
      var boxes = all("input[type=checkbox]", row);
      return boxes.length > 0 && boxes.every(function (b) { return b.checked; });
    }
    function setMode(mode, quiet) {
      var firstOnly = mode === "first";
      root.classList.toggle("is-first", firstOnly);
      rows.forEach(function (row) { setOpen(row, firstOnly && row.hasAttribute("data-first")); });
      modeBtns.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-mode") === mode ? "true" : "false");
      });
      if (quiet) { return; }
      if (!firstOnly) { say(live, "Showing every question, all closed."); return; }
      var names = rows.filter(function (r) { return r.hasAttribute("data-first"); })
        .map(function (r) { return text(one(".fig-checklist-name", r)); });
      say(live, "Highlighting the questions I would check first: " + names.join(", ") + ".");
    }

    rows.forEach(function (row) {
      var head = one(".fig-checklist-head", row);
      if (head) {
        head.addEventListener("click", function () { setOpen(row, head.getAttribute("aria-expanded") !== "true"); });
      }
      row.classList.toggle("is-done", isDone(row)); /* browsers can restore ticks on reload */
      all("input[type=checkbox]", row).forEach(function (box) {
        box.addEventListener("change", function () {
          var done = isDone(row);
          row.classList.toggle("is-done", done);
          if (done) { say(live, text(one(".fig-checklist-name", row)) + ": every item ticked."); }
        });
      });
    });

    root.classList.add("is-interactive");
    showHint(root, ".fig-checklist-hint");
    setMode("all", true);
    if (seg) {
      seg.hidden = false;
      modeBtns.forEach(function (b) {
        b.addEventListener("click", function () { setMode(b.getAttribute("data-mode") || "all", false); });
      });
    }
    HX.reveal(root, function (tl, el) {
      from(tl, el, ".fig-checklist-row", { opacity: 0, y: 12, duration: 0.6, stagger: 0.08 }, 0);
    });
  }

  /* ---------- fig-ai ---------- */
  function ai() {
    var root = one("#fig-ai");
    if (!root) { return; }
    var tiles = all(".fig-ai-tile", root);
    if (!tiles.length) { return; }
    var live = one(".fig-ai-live", root);
    var seg = one(".seg", root);
    var segBtns = seg ? all("button", seg) : [];

    function dept(t) { return text(one(".fig-ai-dept", t)); }
    function paint(t) {
      var on = t.classList.contains("is-flipped");
      var b = one(".fig-ai-flip", t), h = one(".fig-ai-hint", t);
      if (b) { b.setAttribute("aria-label", dept(t) + (on ? ": show how it works today" : ": show the workflow")); }
      if (h) { h.textContent = on ? "See today's way" : "See the workflow"; }
    }
    function syncSeg() {
      var n = tiles.filter(function (t) { return t.classList.contains("is-flipped"); }).length;
      segBtns.forEach(function (b) {
        var face = b.getAttribute("data-face");
        var pressed = (face === "ai" && n === tiles.length) || (face === "today" && n === 0);
        b.setAttribute("aria-pressed", pressed ? "true" : "false");
      });
    }

    tiles.forEach(function (t) {
      var b = mk("button", "fig-ai-flip", null, t);
      b.type = "button";
      mk("span", "fig-ai-hint", "", b).setAttribute("aria-hidden", "true");
      paint(t);
      b.addEventListener("click", function () {
        var on = !t.classList.contains("is-flipped");
        t.classList.toggle("is-flipped", on);
        paint(t);
        syncSeg();
        var line = one(on ? ".fig-ai-with .fig-ai-v" : ".fig-ai-today .fig-ai-v", t);
        say(live, dept(t) + (on ? ", with an agentic workflow: " : ", today: ") + text(line));
      });
    });

    root.classList.add("is-interactive");
    showHint(root, ".fig-ai-hint-line");
    syncSeg();
    if (seg) {
      seg.hidden = false;
      segBtns.forEach(function (b) {
        b.addEventListener("click", function () {
          var on = b.getAttribute("data-face") === "ai";
          tiles.forEach(function (t) { t.classList.toggle("is-flipped", on); paint(t); });
          syncSeg();
          say(live, on ? "Showing the workflow for every department." : "Showing today's way for every department.");
        });
      });
    }
    HX.reveal(root, function (tl, el) {
      from(tl, el, ".fig-ai-bar", { scaleX: 0, transformOrigin: "0% 50%", duration: 0.6, stagger: 0.1 }, 0);
      from(tl, el, ".fig-ai-tile", { opacity: 0.3, y: 10, duration: 0.7, stagger: 0.1 }, 0);
    });
  }

  /* ---------- fig-sentiment ---------- */
  function sentiment() {
    var root = one("#fig-sentiment");
    var host = document.getElementById("fig-sentiment-chart");
    if (!root || !host) { return; }
    refreshHooks(root);
    var d3 = window.d3;
    var data = HX.get("sentiment.themes");
    if (!d3 || !d3.select || !d3.scaleLinear || !Array.isArray(data)) { return; }
    var themes = data.filter(function (t) { return t && t.theme && isNum(t.tone_score); })
      .slice().sort(function (a, b) { return a.tone_score - b.tone_score; });
    if (!themes.length) { return; }
    var TRACK_H = 34;

    function clearHost() { while (host.firstChild) { host.removeChild(host.firstChild); } }

    function drawTrack(el, W, score) {
      var c = W / 2;
      var xs = d3.scaleLinear().domain([-1, 1]).range([16, W - 16]).clamp(true);
      var svg = d3.select(el).append("svg")
        .attr("viewBox", "0 0 " + W + " " + TRACK_H).attr("width", W).attr("height", TRACK_H)
        .attr("aria-hidden", "true").attr("focusable", "false");
      svg.append("rect").attr("class", "fig-sentiment-wn").attr("x", 0).attr("y", 0).attr("width", c).attr("height", TRACK_H);
      svg.append("rect").attr("class", "fig-sentiment-wp").attr("x", c).attr("y", 0).attr("width", W - c).attr("height", TRACK_H);
      svg.append("line").attr("class", "fig-sentiment-mid").attr("x1", c).attr("x2", c).attr("y1", 0).attr("y2", TRACK_H);
      svg.append("line").attr("class", "fig-sentiment-stem")
        .attr("x1", c).attr("x2", xs(score)).attr("y1", TRACK_H / 2).attr("y2", TRACK_H / 2);
      svg.append("circle").attr("class", "fig-sentiment-dot")
        .attr("cx", xs(score)).attr("cy", TRACK_H / 2).attr("r", 8);
    }

    function draw() {
      clearHost();
      var axis = mk("div", "fig-sentiment-axis", null, host);
      axis.setAttribute("aria-hidden", "true");
      var inner = mk("div", "fig-sentiment-ax-in", null, axis);
      mk("span", "fig-sentiment-ax-n", "Negative", inner);
      mk("span", "fig-sentiment-ax-m", "Mixed", inner);
      mk("span", "fig-sentiment-ax-p", "Positive", inner);
      var list = mk("ol", "fig-sentiment-rows", null, host);
      var tracks = [];
      themes.forEach(function (t) {
        var li = mk("li", "fig-sentiment-row", null, list);
        mk("p", "fig-sentiment-theme", t.theme, li);
        var tr = mk("div", "fig-sentiment-track", null, li);
        var meta = mk("p", "fig-sentiment-meta", null, li);
        if (t.tone) { mk("strong", "fig-sentiment-tone", t.tone, meta); }
        if (t.where) { meta.appendChild(document.createTextNode(t.where)); }
        if (t.count_label) { mk("p", "fig-sentiment-count", t.count_label, li); }
        tracks.push({ el: tr, score: t.tone_score });
      });
      var W = Math.floor(tracks[0].el.clientWidth);
      if (W < 120) { return false; }
      tracks.forEach(function (t) { drawTrack(t.el, W, t.score); });
      host.setAttribute("aria-label",
        "Diverging chart of themes from the news and social media, most negative first: " +
        themes.map(function (t) { return t.theme + (t.tone ? " (" + t.tone + ")" : ""); }).join("; ") +
        ". The table that follows lists where each theme was seen and a rough count.");
      return true;
    }

    function run() {
      try {
        if (draw() === false) { clearHost(); host.classList.remove("is-ready"); return false; }
        HX.chartReady(host);
        return true;
      } catch (e) {
        clearHost();
        host.classList.remove("is-ready");
        return false;
      }
    }

    if (run()) {
      HX.reveal(root, function (tl, el) {
        var stems = all(".fig-sentiment-stem", el);
        var center = stems.length ? Number(stems[0].getAttribute("x1")) : 0;
        from(tl, el, ".fig-sentiment-row", { opacity: 0, y: 8, duration: 0.6, stagger: 0.1 }, 0);
        if (center > 0) {
          from(tl, el, ".fig-sentiment-dot", { attr: { cx: center }, duration: 0.9, stagger: 0.1 }, 0.1);
          from(tl, el, ".fig-sentiment-stem", { attr: { x2: center }, duration: 0.9, stagger: 0.1 }, 0.1);
        }
      });
    }
    HX.onResize(function () { run(); });
  }

  HX.ready(function () {
    safe(team);
    safe(checklist);
    safe(ai);
    safe(sentiment);
  });
})();
