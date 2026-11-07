/* charts-a.js: the three model charts of "Leveraged buyouts, explained": fig-qoe, fig-day1 and fig-bridge.
   Draws with D3 v7 into each figure's .chart, then calls HX.chartReady. Every lookup is guarded: a missing element or
   data key leaves the fallback table in place. Reduced motion draws the final state with no tweens. */
(function () {
  "use strict";
  var HX = window.HX;
  var d3 = null;
  if (!HX || typeof HX.ready !== "function" || typeof HX.get !== "function") return;

  var DUR = HX.reduced ? 0 : 500;

  /* ---------- small helpers ---------- */
  function byId(id) { return document.getElementById(id); }
  function num(v) { return typeof v === "number" && isFinite(v) ? v : null; }
  function mk(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }
  function width(host) {
    var w = host ? (host.clientWidth || (host.getBoundingClientRect ? host.getBoundingClientRect().width : 0)) : 0;
    return Math.max(260, Math.floor(w || 320));
  }
  function run(fn) { try { fn(); } catch (e) { /* leave the fallback table visible */ } }
  function svgIn(host, w, h) {
    return d3.select(host).append("svg")
      .attr("viewBox", "0 0 " + w + " " + h).attr("width", w).attr("height", h)
      .attr("focusable", "false").attr("aria-hidden", "true");
  }
  function text(parent, cls, x, y, s, anchor) {
    var t = parent.append("text").attr("class", cls).attr("x", x).attr("y", y).text(s);
    if (anchor) t.attr("text-anchor", anchor);
    return t;
  }
  /* wrap(s, maxPx, charPx): greedy word wrap using an estimated character width */
  function wrap(s, maxPx, cw) {
    var max = Math.max(8, Math.floor(maxPx / cw)), out = [], cur = "";
    String(s).split(" ").forEach(function (w) {
      var t = cur ? cur + " " + w : w;
      if (t.length > max && cur) { out.push(cur); cur = w; } else { cur = t; }
    });
    if (cur) out.push(cur);
    return out;
  }
  function longest(arr) { return arr.reduce(function (m, s) { return Math.max(m, s.length); }, 0); }
  function lines(parent, cls, x, y, arr, anchor, lh) {
    var t = parent.append("text").attr("class", cls).attr("x", x).attr("y", y);
    if (anchor) t.attr("text-anchor", anchor);
    arr.forEach(function (ln, i) { t.append("tspan").attr("x", x).attr("dy", i ? lh : 0).text(ln); });
    return t;
  }
  function usd(v, f) { return v === 0 ? "$0" : HX.fmt(v, f); }
  function signed(v, f) { return v === 0 ? "$0" : (v > 0 ? "+" : "") + HX.fmt(v, f); }
  function setText(id, s) { var e = byId(id); if (e) e.textContent = s; }
  function setBtns(btns, key) {
    Object.keys(btns).forEach(function (k) { btns[k].setAttribute("aria-pressed", k === key ? "true" : "false"); });
  }
  function joinList(arr) {
    return arr.length < 2 ? arr.join("") : arr.slice(0, -1).join(", ") + " and " + arr[arr.length - 1];
  }

  /* =====================================================================
     fig-qoe: quality of earnings waterfall, then the same gap priced at the multiple
     ===================================================================== */
  function initQoe() {
    var host = byId("fig-qoe-chart"), items = HX.get("qoe.items");
    var mult = num(HX.get("qoe.multiple")), pc = num(HX.get("qoe.price_on_claimed")), pv = num(HX.get("qoe.price_on_verified"));
    var ov = num(HX.get("qoe.overpay")), gap = num(HX.get("qoe.gap"));
    var cl = num(HX.get("qoe.claimed_ebitda")), vf = num(HX.get("qoe.verified_ebitda"));
    if (!host || !Array.isArray(items) || items.length < 3) return;
    if ([mult, pc, pv, ov, gap, cl, vf].some(function (v) { return v == null || v <= 0; })) return;

    var Q = "fig-qoe-", first = true, rows = [], lvl = 0, xf = HX.fmt(mult, "x1");
    items.forEach(function (it, i) {
      var a = it ? num(it.amount) : null;
      if (a == null) return;
      var tot = it.kind === "total", x0 = tot ? 0 : lvl, x1 = tot ? a : lvl + a;
      lvl = x1;
      rows.push({ label: String(it.label || ""), v: a, tot: tot, x0: x0, x1: x1, role: !tot ? "step" : (i === 0 ? "claim" : "real") });
    });
    if (rows.length < 3) return;

    function draw() {
      var W = width(host), px = 8, iw = W - 2 * px, lh = 17, barH = 20, gp = 14, valW = 68;
      var x = d3.scaleLinear().domain([0, cl]).range([px, W - px]);
      var xp = d3.scaleLinear().domain([0, pc]).range([px, W - px]);
      var lay = [], y = 4;
      rows.forEach(function (r) {
        var ls = wrap(r.label, iw - valW, 7.4);
        lay.push({ r: r, ls: ls, top: y, by: y + ls.length * lh + 3 });
        y += ls.length * lh + 3 + barH + gp;
      });
      var y2 = y + 2, hd = wrap("Same multiple of " + xf + ", two prices", iw, 7.8);
      var yy = y2 + 24 + (hd.length - 1) * lh + 10;
      var priceRows = [
        { label: "Price on the seller's number: " + HX.fmt(cl, "M2") + " x " + xf, v: pc, role: "claim" },
        { label: "Price on the number that holds up: " + HX.fmt(vf, "M2") + " x " + xf, v: pv, role: "real" }
      ];
      priceRows.forEach(function (r) {
        r.ls = wrap(r.label, iw - valW, 7.4);
        r.top = yy;
        r.by = yy + r.ls.length * lh + 3;
        yy = r.by + barH + gp + (r.role === "real" ? 22 : 0);
      });

      clear(host);
      var svg = svgIn(host, W, yy + 6), conG = svg.append("g"), rowNodes = [];
      lay.forEach(function (L, i) {
        var r = L.r, g = svg.append("g").attr("class", Q + "row");
        lines(g, Q + "lbl", px, L.top + 13, L.ls, null, lh);
        text(g, Q + "val", W - px, L.top + 13, r.tot ? HX.fmt(r.v, "M2") : HX.fmt(r.v, "K0"), "end");
        g.append("rect").attr("class", Q + "b-" + r.role).attr("rx", 3)
          .attr("x", Math.min(x(r.x0), x(r.x1))).attr("y", L.by)
          .attr("width", Math.max(2, Math.abs(x(r.x1) - x(r.x0)))).attr("height", barH);
        if (r.role === "real") {
          var gx = x(r.x1), gw = x(cl) - gx;
          if (gw > 2) {
            g.append("rect").attr("class", Q + "ghost").attr("rx", 3).attr("x", gx).attr("y", L.by).attr("width", gw).attr("height", barH);
            if (gw >= 46) text(g, Q + "gtxt", gx + gw / 2, L.by + 15, HX.fmt(gap, "K0"), "middle");
          }
        }
        rowNodes.push(g.node());
        if (i < lay.length - 1) {
          conG.append("line").attr("class", Q + "conn").attr("x1", x(r.x1)).attr("x2", x(r.x1))
            .attr("y1", L.by + barH).attr("y2", lay[i + 1].by);
        }
      });

      conG.append("line").attr("class", Q + "div").attr("x1", px).attr("x2", W - px).attr("y1", y2).attr("y2", y2);
      lines(svg, Q + "hdr", px, y2 + 24, hd, null, lh);
      var priceNodes = [], pBars = [], pGhosts = [];
      priceRows.forEach(function (r) {
        var g = svg.append("g").attr("class", Q + "row");
        lines(g, Q + "lbl", px, r.top + 13, r.ls, null, lh);
        text(g, Q + "val", W - px, r.top + 13, HX.fmt(r.v, "M1"), "end");
        pBars.push(g.append("rect").attr("class", Q + "b-" + r.role).attr("rx", 3)
          .attr("x", px).attr("y", r.by).attr("width", xp(r.v) - px).attr("height", barH).node());
        if (r.role === "real") {
          var gx2 = xp(r.v), gw2 = xp(pc) - gx2;
          if (gw2 > 2) {
            pGhosts.push(g.append("rect").attr("class", Q + "ghost").attr("rx", 3)
              .attr("x", gx2).attr("y", r.by).attr("width", gw2).attr("height", barH).node());
            if (gw2 >= 46) pGhosts.push(text(g, Q + "gtxt", gx2 + gw2 / 2, r.by + 15, HX.fmt(ov, "M1"), "middle").node());
          }
          pGhosts.push(text(g, Q + "over", W - px, r.by + barH + 18, "You would overpay " + HX.fmt(ov, "M1"), "end").node());
        }
        priceNodes.push(g.node());
      });

      if (first) {
        first = false;
        HX.reveal(host, function (tl) {
          tl.from(conG.node(), { opacity: 0, duration: 0.6 });
          tl.from(rowNodes, { opacity: 0, y: -12, duration: 0.6, stagger: 0.1 }, 0);
          tl.from(priceNodes, { opacity: 0, duration: 0.4, stagger: 0.2 }, "-=0.1");
          tl.from(pBars, { attr: { width: 0 }, duration: 0.7, stagger: 0.2 }, "<");
          if (pGhosts.length) tl.from(pGhosts, { opacity: 0, duration: 0.5, stagger: 0.05 }, "-=0.2");
        });
      }
      host.setAttribute("aria-label", "Waterfall chart, illustrative. The seller's numbers show EBITDA of " + HX.fmt(cl, "M2") + ". " +
        rows.filter(function (r) { return !r.tot; }).map(function (r) { return r.label + ", " + HX.fmt(r.v, "K0"); }).join("; ") +
        ". That leaves " + HX.fmt(vf, "M2") + ", a gap of " + HX.fmt(gap, "K0") + ". At " + xf + " the price is " + HX.fmt(pc, "M1") +
        " on the seller's number and " + HX.fmt(pv, "M1") + " on the number that holds up, so you would overpay " + HX.fmt(ov, "M1") + ".");
    }

    draw();
    HX.chartReady(host);
    HX.onResize(function () { run(draw); });
  }

  /* =====================================================================
     fig-day1: cash balance over the first 13 weeks, with and without the receivables
     ===================================================================== */
  function initDay1() {
    var host = byId("fig-day1-chart"), ctlEl = byId("fig-day1-controls"), weeks = HX.get("day1.weeks");
    var lab = HX.get("day1.case_labels") || {};
    var reserve = num(HX.get("day1.reserve")), dso = num(HX.get("day1.dso_days")), fw = num(HX.get("day1.first_payment_week"));
    var gapv = num(HX.get("day1.shortfall_no_ar")), need = num(HX.get("day1.cash_needed_no_ar"));
    var sales = num(HX.get("day1.weekly_sales")), costs = num(HX.get("day1.weekly_costs")), pay = num(HX.get("day1.monthly_loan_payment"));
    if (!host || !Array.isArray(weeks) || weeks.length < 3 || reserve == null || gapv == null) return;

    var pts = [];
    weeks.forEach(function (r) {
      if (r && num(r.week) != null && num(r.cash_peg) != null && num(r.cash_no_ar) != null) {
        pts.push({ w: r.week, a: r.cash_peg, b: r.cash_no_ar });
      }
    });
    if (pts.length < 3) return;
    pts.sort(function (p, q) { return p.w - q.w; });

    var D = "fig-day1-", first = true, focus = "both", btns = {}, gPeg = null, gNo = null;
    var nameA = String(lab.peg || "Receivables come with the business"), nameB = String(lab.no_ar || "Seller keeps the receivables");
    var firstW = pts[0].w, lastW = pts[pts.length - 1].w, lowP = pts[0], minA = pts[0].a;
    pts.forEach(function (p) { if (p.b < lowP.b) lowP = p; if (p.a < minA) minA = p.a; });

    /* loan payment weeks, found from the data: weeks where the cash gain falls short of a normal week by a loan payment */
    var payWeeks = [];
    if (sales != null && costs != null && pay != null) {
      pts.forEach(function (p, i) {
        if (i && p.a - pts[i - 1].a < (sales - costs) - pay / 2) payWeeks.push(p.w);
      });
    }
    var pwEl = byId("fig-day1-payweeks");
    if (pwEl && payWeeks.length) {
      pwEl.textContent = "in week" + (payWeeks.length > 1 ? "s " : " ") + joinList(payWeeks.map(function (w) { return HX.fmt(w, "n0"); }));
    }

    function say() {
      var pegTxt = nameA + (minA > 0 ? ": cash stays above zero, lowest " + HX.fmt(minA, "K0") + "." : ": cash dips below zero.");
      var noTxt = nameB + ": cash falls to " + HX.fmt(lowP.b, "K0") + " in week " + HX.fmt(lowP.w, "n0") +
        (need != null ? ", so you would need about " + HX.fmt(need, "K0") + " on Day 1 instead of " + HX.fmt(reserve, "K0") + "." : ".");
      if (focus === "peg") return pegTxt;
      if (focus === "no_ar") return noTxt;
      return "Showing both cases. " + pegTxt + " " + noTxt;
    }
    function announce() { setText("fig-day1-live", say()); }

    function applyFocus(animate) {
      if (!gPeg || !gNo) return;
      var pairs = [[gPeg, focus === "no_ar" ? 0.18 : 1], [gNo, focus === "peg" ? 0.18 : 1]];
      pairs.forEach(function (p) {
        if (animate && DUR > 0) p[0].transition().duration(300).style("opacity", p[1]);
        else p[0].style("opacity", p[1]);
      });
    }

    function buildControls() {
      if (!ctlEl) return;
      clear(ctlEl);
      var seg = mk("div", "seg " + D + "seg");
      seg.setAttribute("role", "group");
      seg.setAttribute("aria-label", "Highlight a case");
      [["both", "Show both cases"], ["peg", nameA], ["no_ar", nameB]].forEach(function (c) {
        var b = mk("button", "", c[1]);
        b.type = "button";
        b.setAttribute("aria-pressed", c[0] === focus ? "true" : "false");
        b.addEventListener("click", function () {
          focus = c[0];
          setBtns(btns, focus);
          applyFocus(true);
          announce();
        });
        btns[c[0]] = b;
        seg.appendChild(b);
      });
      ctlEl.appendChild(seg);
    }

    function draw() {
      var W = width(host), m = { top: 14, left: 56, right: 8 }, ph = 280, iw = W - m.left - m.right;
      var lo = d3.min(pts, function (p) { return Math.min(p.a, p.b); }), hi = d3.max(pts, function (p) { return Math.max(p.a, p.b); });
      var yMin = Math.floor((Math.min(lo, 0) - 190000) / 100000) * 100000, yMax = Math.ceil((hi + 100000) / 100000) * 100000;
      var x = d3.scaleLinear().domain([firstW, lastW]).range([0, iw]);
      var y = d3.scaleLinear().domain([yMin, yMax]).range([ph, 0]);
      function valAt(k, w) {
        for (var i = 1; i < pts.length; i++) {
          if (w <= pts[i].w) {
            var p0 = pts[i - 1], p1 = pts[i], t = (w - p0.w) / ((p1.w - p0.w) || 1);
            return p0[k] + (p1[k] - p0[k]) * t;
          }
        }
        return pts[pts.length - 1][k];
      }
      function maxFrom(k, w) {
        var mv = valAt(k, w);
        pts.forEach(function (p) { if (p.w >= w && p[k] > mv) mv = p[k]; });
        return mv;
      }
      var fText = fw != null
        ? "First customer cash arrives in week " + HX.fmt(fw, "n0") + (dso != null ? ", about " + HX.fmt(dso, "n0") + " days after the work" : "")
        : "";
      var fl = fText ? wrap(fText, iw - 4, 6.9) : [];
      var H = m.top + ph + 66 + Math.max(0, fl.length - 1) * 16 + 12;

      clear(host);
      var svg = svgIn(host, W, H), g = svg.append("g").attr("transform", "translate(" + m.left + "," + m.top + ")");
      var gAll = g.append("g");
      d3.range(Math.ceil(yMin / 200000) * 200000, yMax + 1, 200000).forEach(function (t) {
        var zero = t === 0;
        gAll.append("line").attr("class", D + (zero ? "zero" : "grid")).attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t));
        text(gAll, D + (zero ? "zlab" : "tick"), -8, y(t) + 4.5, zero ? "$0" : HX.fmt(t, "K0"), "end");
      });
      gAll.append("line").attr("class", D + "axis").attr("x1", 0).attr("x2", iw).attr("y1", ph).attr("y2", ph);
      d3.range(firstW, lastW + 1, iw < 300 ? 2 : 1).forEach(function (w) {
        text(gAll, D + "tick", x(w), ph + 17, HX.fmt(w, "n0"), "middle");
      });
      text(gAll, D + "axt", 0, ph + 34, "Weeks after closing", "start");
      payWeeks.forEach(function (w) {
        gAll.append("line").attr("class", D + "pay").attr("x1", x(w)).attr("x2", x(w)).attr("y1", ph - 8).attr("y2", ph);
      });

      gPeg = g.append("g");
      gNo = g.append("g");
      var ap = [];
      pts.forEach(function (p, i) {
        if (i && ((pts[i - 1].b >= 0) !== (p.b >= 0))) {
          var q = pts[i - 1], t = q.b / (q.b - p.b);
          ap.push({ w: q.w + (p.w - q.w) * t, b: 0 });
        }
        ap.push({ w: p.w, b: p.b });
      });
      var areaNode = gNo.append("path").attr("class", D + "area")
        .attr("d", d3.area().x(function (p) { return x(p.w); }).y0(y(0)).y1(function (p) { return y(Math.min(0, p.b)); })(ap)).node();
      var line = d3.line().x(function (p) { return x(p.w); });
      var noPath = gNo.append("path").attr("class", D + "line " + D + "no").attr("d", line.y(function (p) { return y(p.b); })(pts));
      var pegPath = gPeg.append("path").attr("class", D + "line " + D + "peg").attr("d", line.y(function (p) { return y(p.a); })(pts));

      /* direct labels: the peg case above its line, the other case inside the gap, both wrapped to fit */
      var annPeg = gPeg.append("g"), annNo = gNo.append("g"), annStart = g.append("g");
      var pl = wrap(nameA, iw * 0.92 - 16, 6.9), plw = longest(pl) * 6.9;
      var pTop = y(maxFrom("a", x.invert(iw - plw - 16))) - 11 - (pl.length - 1) * 16;
      annPeg.append("rect").attr("class", D + "sw-peg").attr("rx", 2).attr("x", iw - plw - 16).attr("y", pTop - 10).attr("width", 10).attr("height", 10);
      lines(annPeg, D + "ann", iw, pTop, pl, "end", 16);

      var gw0 = lastW;
      pts.forEach(function (p) { if (p.b <= 0.5 * lowP.b && p.w < gw0) gw0 = p.w; });
      var gx = x(gw0) + 4;
      var gl = wrap("The gap: about " + HX.fmt(gapv, "K0") + " to fund with a credit line or more cash", iw - gx - 4, 7.3);
      lines(annNo, D + "ann " + D + "ann-b", gx, y(0) + 18, gl, "start", 16);

      var nl = wrap(nameB, iw * 0.5, 6.9), nlw = longest(nl) * 6.9;
      var nTop = y(maxFrom("b", x.invert(iw - nlw - 18))) - 9 - (nl.length - 1) * 16;
      annNo.append("rect").attr("class", D + "sw-no").attr("rx", 2).attr("x", iw - nlw - 16).attr("y", nTop - 10).attr("width", 10).attr("height", 10);
      lines(annNo, D + "ann", iw, nTop, nl, "end", 16);

      annNo.append("circle").attr("class", D + "dot " + D + "dot-low").attr("cx", x(lowP.w)).attr("cy", y(lowP.b)).attr("r", 6);
      lines(annNo, D + "ann", iw, y(lowP.b) + 21,
        wrap("Low point: " + HX.fmt(lowP.b, "K0") + ", week " + HX.fmt(lowP.w, "n0"), iw - 8, 6.9), "end", 16);
      var kink = null;
      pts.forEach(function (p) { if (fw != null && p.w === fw) kink = p; });
      if (kink) annNo.append("circle").attr("class", D + "ring").attr("cx", x(kink.w)).attr("cy", y(kink.b)).attr("r", 9);

      var sy = y(pts[0].a);
      annStart.append("line").attr("class", D + "lead").attr("x1", 0).attr("x2", 0).attr("y1", sy - 6).attr("y2", sy - 24);
      text(annStart, D + "ann", 4, sy - 27, "Start: " + HX.fmt(reserve, "K0"), "start");
      annStart.append("circle").attr("class", D + "dot " + D + "dot-start").attr("cx", x(pts[0].w)).attr("cy", sy).attr("r", 6);

      if (fl.length && kink) {
        var xk = x(fw);
        gAll.append("path").attr("class", D + "tri")
          .attr("d", "M" + xk + "," + (ph + 40) + " L" + (xk - 6) + "," + (ph + 49) + " L" + (xk + 6) + "," + (ph + 49) + " Z");
        var half = longest(fl) * 6.9 / 2, xc = Math.max(half, Math.min(iw - half, xk));
        lines(gAll, D + "axt", xc, ph + 66, fl, "middle", 16);
      }

      applyFocus(false);
      if (first) {
        first = false;
        HX.reveal(host, function (tl) {
          var ps = [pegPath.node(), noPath.node()];
          ps.forEach(function (p) {
            var L = p.getTotalLength ? p.getTotalLength() : 0;
            if (L > 0) p.style.strokeDasharray = L + " " + L;
          });
          tl.from(ps, { strokeDashoffset: function (i, t) { return t.getTotalLength ? t.getTotalLength() : 0; }, duration: 1.4, stagger: 0.2 });
          tl.from([areaNode, annPeg.node(), annNo.node(), annStart.node()], { opacity: 0, duration: 0.6, stagger: 0.1 }, "-=0.6");
          tl.call(function () { ps.forEach(function (p) { p.style.strokeDasharray = "none"; }); });
        });
      }
      host.setAttribute("aria-label", "Line chart, illustrative, of the company's cash over " + HX.fmt(lastW - firstW, "n0") +
        " weeks after closing. " + nameA + ": " + (minA > 0 ? "cash stays above zero, lowest " + HX.fmt(minA, "K0") : "cash dips below zero") + ". " +
        nameB + ": cash falls to " + HX.fmt(lowP.b, "K0") + " in week " + HX.fmt(lowP.w, "n0") + ", a gap of about " +
        HX.fmt(gapv, "K0") + " to fund with a credit line or more cash.");
    }

    buildControls();
    draw();
    HX.chartReady(host);
    HX.onResize(function () { run(draw); });
  }

  /* =====================================================================
     fig-bridge: value bridge from the price paid to the owner's proceeds, four scenarios
     ===================================================================== */
  function initBridge() {
    var host = byId("fig-bridge-chart"), ctlEl = byId("fig-bridge-controls"), S = HX.get("scenarios");
    var floor = num(HX.get("inputs.dscr_floor")), entry = num(HX.get("inputs.entry_multiple"));
    if (!host || !S) return;
    var NEED = ["price_paid", "earnings_growth", "multiple_change", "sale_price", "sba_still_owed", "seller_note_with_interest", "owner_proceeds"];
    var KEYS = ["base", "flat", "downside", "break"].filter(function (k) {
      var b = S[k] && S[k].bridge;
      return b && NEED.every(function (n) { return num(b[n]) != null; });
    });
    if (!KEYS.length) return;
    var B = "fig-bridge-", first = true, state = KEYS.indexOf("base") >= 0 ? "base" : KEYS[0], btns = {};
    var hasPay = KEYS.every(function (k) { return num(S[k].sba_paid_down) != null; });
    var ROWS = [
      { k: "price_paid", label: "Price paid", tot: true, cls: "total" },
      { k: "earnings_growth", label: "Engine 1: earnings growth", cls: "engine" },
      { k: "multiple_change", label: "Engine 2: the multiple", cls: "engine" },
      { k: "sale_price", label: "Sale price", tot: true, cls: "total" },
      { k: "sba_still_owed", label: "SBA loan still owed", neg: true, cls: "loan", sub: hasPay },
      { k: "seller_note_with_interest", label: "Seller note, with interest", neg: true, cls: "seller" },
      { k: "owner_proceeds", label: "Owner's proceeds", tot: true, cls: "owner" }
    ];
    var rowRefs = [], connRefs = [], x = null, geo = null;

    function geom(k) {
      var b = S[k].bridge, lvl = 0, out = [];
      ROWS.forEach(function (R) {
        var a = b[R.k], v = R.tot ? a : (R.neg ? -a : a), x0 = R.tot ? 0 : lvl, x1 = R.tot ? a : lvl + v;
        lvl = x1;
        out.push({ v: v, x0: x0, x1: x1 });
      });
      return out;
    }
    var dMax = 0;
    KEYS.forEach(function (k) { geom(k).forEach(function (r) { dMax = Math.max(dMax, r.x0, r.x1); }); });
    dMax = Math.max(1e6, Math.ceil(dMax / 1e6) * 1e6);

    function describe(k) {
      var s = S[k], g = num(s.growth_pct), sh = num(s.year1_shock_pct), em = num(s.exit_multiple), hy = num(s.hold_years);
      var growing = !(sh != null && sh < 0) && g != null && g > 0;
      var a = sh != null && sh < 0 ? "earnings fall " + HX.fmt(-sh, "p0") + " in year 1 and stay there"
        : (growing ? "earnings grow " + HX.fmt(g, "p0") + " a year" + (hy != null ? " for " + HX.fmt(hy, "n0") + " years" : "") : "earnings stay flat");
      var when = growing || hy == null ? " sells" : " sells in year " + HX.fmt(hy, "n0");
      var cmp = entry == null || em == null ? "" : (em > entry ? ", up from " + HX.fmt(entry, "x1") + " at purchase"
        : (em < entry ? ", down from " + HX.fmt(entry, "x1") + " at purchase" : ", the same as at purchase"));
      return "In this scenario, " + a + ", and the company" + when + (em != null ? " at " + HX.fmt(em, "x1") : "") + cmp + ".";
    }

    function layout() {
      var y = 4, out = [];
      ROWS.forEach(function (R) {
        var by = y + (R.sub ? 32 : 16) + 3;
        out.push({ R: R, top: y, by: by });
        y = by + 18 + 12;
      });
      return { rows: out, axisY: y + 2, H: y + 34 };
    }

    function draw() {
      var W = width(host), px = 8;
      geo = layout();
      x = d3.scaleLinear().domain([0, dMax]).range([px, W - px]);
      clear(host);
      var svg = svgIn(host, W, geo.H), grid = svg.append("g"), conG = svg.append("g");
      d3.range(0, dMax + 1, 2e6).forEach(function (t) {
        if (t > 0) grid.append("line").attr("class", B + "grid").attr("x1", x(t)).attr("x2", x(t)).attr("y1", 0).attr("y2", geo.axisY);
        text(grid, B + "tick", x(t), geo.axisY + 19, t === 0 ? "$0" : HX.fmt(t, "M1"), t === 0 ? "start" : "middle");
      });
      grid.append("line").attr("class", B + "axis").attr("x1", px).attr("x2", W - px).attr("y1", geo.axisY).attr("y2", geo.axisY);
      rowRefs = [];
      connRefs = [];
      geo.rows.forEach(function (L, i) {
        var g = svg.append("g").attr("class", B + "row");
        text(g, B + "lbl", px, L.top + 13, L.R.label);
        var val = text(g, B + "val", W - px, L.top + 13, "", "end");
        var sub = L.R.sub ? text(g, B + "sub", px, L.top + 29, "") : null;
        var bar = g.append("rect").attr("class", B + "b-" + L.R.cls).attr("rx", 3).attr("x", px).attr("y", L.by).attr("width", 0).attr("height", 18);
        var none = L.R.cls === "owner" ? text(g, B + "none", px + 6, L.by + 14, "Nothing left for the buyer").style("display", "none") : null;
        rowRefs.push({ g: g, bar: bar, val: val, sub: sub, none: none });
        if (i < geo.rows.length - 1) {
          connRefs.push(conG.append("line").attr("class", B + "conn").attr("y1", L.by + 18).attr("y2", geo.rows[i + 1].by));
        }
      });
    }

    function update(k, animate) {
      var G = geom(k), s = S[k], b = s.bridge, go = animate && DUR > 0;
      G.forEach(function (r, i) {
        var ref = rowRefs[i], R = ROWS[i];
        if (!ref) return;
        var a0 = Math.max(0, r.x0), a1 = Math.max(0, r.x1);
        var bt = go ? ref.bar.transition().duration(DUR) : ref.bar;
        bt.attr("x", x(Math.min(a0, a1))).attr("width", Math.max(2, Math.abs(x(a1) - x(a0))));
        ref.val.text(R.tot ? usd(r.v, "M2") : signed(r.v, "M2"));
        if (ref.none) ref.none.style("display", R.tot && r.v <= 0 ? null : "none");
        if (ref.sub && num(s.sba_paid_down) != null) ref.sub.text("Engine 3, loan paydown: " + HX.fmt(s.sba_paid_down, "M2") + " paid off");
        if (i < G.length - 1 && connRefs[i]) {
          var cx = x(Math.max(0, r.x1)), ct = go ? connRefs[i].transition().duration(DUR) : connRefs[i];
          ct.attr("x1", cx).attr("x2", cx);
        }
      });

      var bust = b.owner_proceeds <= 0, md = num(s.min_dscr), pass = md != null && floor != null ? md >= floor : true;
      var ok = byId("fig-bridge-ok"), bu = byId("fig-bridge-bust");
      if (ok) ok.hidden = bust;
      if (bu) {
        bu.hidden = !bust;
        var sp = bu.querySelector("span");
        if (sp && num(s.yearly_shortfall) != null) sp.textContent = HX.fmt(s.yearly_shortfall, "K0");
      }
      if (!bust) {
        setText("fig-bridge-v-proceeds", HX.fmt(b.owner_proceeds, "M2"));
        setText("fig-bridge-v-cash", HX.fmt(s.buyer_cash_in, "K0"));
        setText("fig-bridge-v-moic", HX.fmt(s.moic_proceeds_only, "x1"));
        setText("fig-bridge-v-years", HX.fmt(s.hold_years, "n0"));
        setText("fig-bridge-v-irr", HX.fmt(s.irr_proceeds_only_pct, "p0"));
      }
      setText("fig-bridge-desc", describe(k));
      setText("fig-bridge-v-dscr", md != null ? HX.fmt(md, "x2") : "");
      setText("fig-bridge-badge-word", pass ? "Bank test: passes" : "Bank test: fails");
      var bd = byId("fig-bridge-badge");
      if (bd) {
        bd.className = B + "badge " + (pass ? B + "pass" : B + "fail");
        var ip = bd.querySelector("." + B + "ico-pass"), ifl = bd.querySelector("." + B + "ico-fail");
        if (ip) { if (pass) ip.removeAttribute("hidden"); else ip.setAttribute("hidden", ""); }
        if (ifl) { if (pass) ifl.setAttribute("hidden", ""); else ifl.removeAttribute("hidden"); }
      }
      var said = String(s.label || k) + ": sale price " + HX.fmt(b.sale_price, "M2") + ", owner's proceeds " + usd(b.owner_proceeds, "M2") +
        (bust ? ", the buyer's cash is gone" : ", " + HX.fmt(s.moic_proceeds_only, "x1") + " the buyer's cash, proceeds only") +
        (md != null ? ". Lowest DSCR " + HX.fmt(md, "x2") + ", " + (pass ? "passes" : "fails") + " the bank test." : ".");
      setText("fig-bridge-live", animate ? said : "");
      host.setAttribute("aria-label", "Waterfall chart, illustrative, scenario " + String(s.label || k) + ". " +
        G.map(function (r, i) { return ROWS[i].label + " " + (ROWS[i].tot ? usd(r.v, "M2") : signed(r.v, "M2")); }).join(", ") + ".");
    }

    function buildControls() {
      if (!ctlEl) return;
      clear(ctlEl);
      var seg = mk("div", "seg " + B + "seg");
      seg.setAttribute("role", "group");
      seg.setAttribute("aria-label", "Scenario");
      KEYS.forEach(function (k) {
        var bt = mk("button", "", String(S[k].label || k));
        bt.type = "button";
        bt.setAttribute("aria-pressed", k === state ? "true" : "false");
        bt.addEventListener("click", function () {
          if (k === state) return;
          state = k;
          setBtns(btns, state);
          update(state, true);
        });
        btns[k] = bt;
        seg.appendChild(bt);
      });
      ctlEl.appendChild(seg);
    }

    buildControls();
    draw();
    update(state, false);
    if (first) {
      first = false;
      HX.reveal(host, function (tl) {
        tl.from(rowRefs.map(function (q) { return q.g.node(); }), { opacity: 0, y: -10, duration: 0.5, stagger: 0.1 });
        tl.from(connRefs.map(function (q) { return q.node(); }), { opacity: 0, duration: 0.4 }, "-=0.3");
      });
    }
    HX.chartReady(host);
    HX.onResize(function () { run(function () { draw(); update(state, false); }); });
  }

  /* ---------- start ---------- */
  HX.ready(function () {
    d3 = window.d3;
    if (!d3 || !d3.select || !d3.scaleLinear || !d3.range || !d3.line || !d3.area) return;
    run(initQoe);
    run(initDay1);
    run(initBridge);
  });
})();
