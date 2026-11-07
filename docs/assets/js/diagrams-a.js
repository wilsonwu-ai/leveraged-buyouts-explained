/* diagrams-a.js: the capital stack family. fig-house (a house and its mortgage), fig-stack (the interactive capital
   stack visualizer) and fig-funds (closing day sources and uses).
   The HTML already holds the finished picture (the 4.0x case, no investors), so the page reads correctly with no
   script. Scroll reveals animate from a hidden state to that picture; with reduced motion, or without GSAP,
   HX.reveal does nothing and the static state stays. fig-stack recomputes in the browser from site_data
   (inputs, cfads) with the same formulas as model/lbo_model.py. Nothing in here may throw. */
(function () {
  "use strict";

  var HX = window.HX;
  if (!HX || typeof HX.ready !== "function" || typeof HX.get !== "function" || typeof HX.fmt !== "function") { return; }
  var doc = document;

  function q(sel, root) {
    try { return (root || doc).querySelector(sel); } catch (e) { return null; }
  }
  function qa(sel, root) {
    try { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); } catch (e) { return []; }
  }
  function safe(fn) {
    try { fn(); } catch (e) { /* a broken figure must never break the page */ }
  }
  function num(v) { return typeof v === "number" && isFinite(v) ? v : null; }
  function put(el, s) { if (el && el.textContent !== s) { el.textContent = s; } }
  function setVar(el, name, v) {
    if (el && el.style) { el.style.setProperty(name, String(Math.round(v * 10000) / 10000)); }
  }
  /* tl.from(...) on every match of sel inside root, skipped quietly when nothing matches */
  function addFrom(tl, root, sel, vars, pos) {
    var t = qa(sel, root);
    if (tl && t.length) { tl.from(t, vars, pos); }
  }

  /* ---------- fig-house ---------- */
  function initHouse() {
    var root = q("#fig-house");
    if (!root) { return; }
    HX.reveal(root, function (tl) {
      /* the layers stack up from the bottom: the markup lists them loan, note, cash */
      addFrom(tl, root, ".fig-house-layer", { opacity: 0, y: 30, duration: 0.7, stagger: 0.1 }, 0);
      addFrom(tl, root, ".fig-house-house", { opacity: 0, y: 12, duration: 0.6 }, 0.1);
      /* then the cash arrow flows from the house to the loan */
      var line = q(".fig-house-flow", root);
      var x1 = line ? parseFloat(line.getAttribute("x1")) : NaN;
      if (line && isFinite(x1)) { tl.from(line, { attr: { x2: x1 }, duration: 0.7 }, 1.0); }
      addFrom(tl, root, ".fig-house-head,.fig-house-mid,.fig-house-pulse", { opacity: 0, duration: 0.4 }, 1.4);
      addFrom(tl, root, ".fig-house-rent", { opacity: 0, y: 12, duration: 0.7, stagger: 0.1 }, 1.5);
    });
  }

  /* ---------- fig-funds ---------- */
  function initFunds() {
    var root = q("#fig-funds");
    if (!root) { return; }
    /* ribbons are revealed along the direction of the flow: downward on a phone, rightward on a wide screen */
    function clipIn(tl, sel, from, pos) {
      var t = qa(sel, root);
      if (!t.length) { return; }
      tl.fromTo(t, { opacity: 0, clipPath: from },
        { opacity: 1, clipPath: "inset(0% 0% 0% 0%)", duration: 0.8, stagger: 0.1, clearProps: "clipPath" }, pos);
    }
    HX.reveal(root, function (tl) {
      addFrom(tl, root, ".fig-funds-src", { opacity: 0, duration: 0.6 }, 0);
      addFrom(tl, root, ".fig-funds-lab:not(.fig-funds-lab2)", { opacity: 0, duration: 0.6 }, 0.1);
      clipIn(tl, ".fig-funds-tall .fig-funds-rib:not(.fig-funds-rib2) path", "inset(0% 0% 100% 0%)", 0.4);
      clipIn(tl, ".fig-funds-wide .fig-funds-rib:not(.fig-funds-rib2) path", "inset(0% 100% 0% 0%)", 0.4);
      addFrom(tl, root, ".fig-funds-pot", { opacity: 0, duration: 0.6 }, 0.9);
      clipIn(tl, ".fig-funds-tall .fig-funds-rib2 path", "inset(0% 0% 100% 0%)", 1.1);
      clipIn(tl, ".fig-funds-wide .fig-funds-rib2 path", "inset(0% 100% 0% 0%)", 1.1);
      addFrom(tl, root, ".fig-funds-use", { opacity: 0, duration: 0.6 }, 1.7);
      addFrom(tl, root, ".fig-funds-lab2", { opacity: 0, duration: 0.6 }, 1.8);
    });
  }

  /* ---------- fig-stack ---------- */
  function initStack() {
    var root = q("#fig-stack");
    if (!root) { return; }
    var inp = q("#fig-stack-mult", root), chart = q("#fig-stack-chart", root);
    var I = HX.get("inputs");
    var cfads = num(HX.get("cfads"));
    var dMult = num(HX.get("stack.d.multiple"));
    if (!inp || !chart || !I || cfads == null) { return; }

    var ebitda = num(I.ebitda), closing = num(I.closing_and_reserve);
    var ownPct = num(I.own_cash_pct), injPct = num(I.injection_pct);
    var ratePct = num(I.sba_rate_pct), years = num(I.sba_years);
    var floor = num(I.dscr_floor), cap = num(I.sba_cap), stepUp = num(I.step_up);
    var need = [ebitda, closing, ownPct, injPct, ratePct, years, floor, cap, stepUp];
    for (var i = 0; i < need.length; i++) { if (need[i] == null) { return; } }
    if (ebitda <= 0 || years <= 0 || floor <= 0 || ratePct <= 0) { return; }
    var minM = parseFloat(inp.min), maxM = parseFloat(inp.max);
    if (!(maxM > minM)) { return; }

    /* loan maths, as in the model: payment(L) = 12 x L x r / (1 - (1 + r)^-n) with a monthly rate r over n months;
       maxLoan is the biggest loan whose payment still leaves cash for lenders at the DSCR floor */
    var r = ratePct / 100 / 12, n = years * 12, grow = 1 - Math.pow(1 + r, -n);
    function pay(loan) { return 12 * loan * r / grow; }
    var maxLoan = (cfads / floor / 12) * grow / r;
    var maxProject = ebitda * maxM + closing;
    /* the bank test bars share one axis, wide enough for the dearest price on the slider */
    var axis = Math.ceil(Math.max(cfads, pay(maxProject * (1 - injPct / 100)) * floor) * 1.08 / 50000) * 50000;

    function calc(mult, investorsOn) {
      var price = ebitda * mult, project = price + closing;
      var own = ownPct / 100 * project, standby = (injPct - ownPct) / 100 * project;
      var core = project - own - standby;
      var inv = investorsOn ? Math.max(0, core - maxLoan) : 0;
      var sba = core - inv;
      var payment = pay(sba), dscr = cfads / payment;
      var share = inv > 0 && price > 0 ? Math.min(100, 100 * stepUp * inv / price) : 0;
      return { mult: mult, price: price, project: project, own: own, standby: standby, inv: inv, sba: sba,
               payment: payment, dscr: dscr, passes: dscr >= floor - 1e-9, overCap: sba > cap,
               invShare: share, buyerShare: 100 - share };
    }

    function byId(id) { return doc.getElementById(id); }
    var el = {
      ox: byId("fig-stack-ox"), op: byId("fig-stack-op"), track: byId("fig-stack-track"), tickl: byId("fig-stack-tickl"),
      badge: byId("fig-stack-badge"), bw: byId("fig-stack-bw"), dv: byId("fig-stack-dv"), pay: byId("fig-stack-pay"),
      bfCash: byId("fig-stack-bf-cash"), bfPay: byId("fig-stack-bf-pay"), bfCush: byId("fig-stack-bf-cush"),
      bfGap: byId("fig-stack-bf-gap"), gl: byId("fig-stack-gl"), capmsg: byId("fig-stack-capmsg"),
      own: byId("fig-stack-own"), ob: byId("fig-stack-ob"), oi: byId("fig-stack-oi"),
      total: byId("fig-stack-total"), price: byId("fig-stack-price"), live: byId("fig-stack-live"),
      test: q(".fig-stack-test", root)
    };
    var layers = {};
    qa(".fig-stack-layer", root).forEach(function (li) {
      var k = li.getAttribute("data-layer");
      if (k) { layers[k] = { li: li, amt: q(".fig-stack-amt", li), shr: q(".fig-stack-shr", li) }; }
    });
    if (!layers.loan || !layers.note || !layers.inv || !layers.cash) { return; }
    var buttons = qa(".fig-stack-seg button", root);
    var tickOff = el.tickl ? el.tickl.innerHTML : "";
    var tickOn = false, lastPass = null, timer = null;
    var state = { mult: parseFloat(inp.value), on: false };
    if (!isFinite(state.mult)) { state.mult = 4; }

    /* a note for the case where switching investors on changes nothing */
    var hint = doc.createElement("p");
    hint.className = "fig-stack-hint";
    hint.hidden = true;
    var sbaLine = q(".fig-stack-sba", root);
    if (sbaLine && sbaLine.parentNode) { sbaLine.parentNode.insertBefore(hint, sbaLine); }

    /* the tick on the track: the highest price that passes without investors */
    if (el.track && dMult != null) {
      var frac = Math.min(1, Math.max(0, (dMult - minM) / (maxM - minM)));
      el.track.style.setProperty("--d", String(Math.round(frac * 10000) / 10000));
    }

    /* dollars as $NNNK below $1M and $N.NNM from there, so a big investor layer never reads "$1,097K" */
    function money(v) { return HX.fmt(v, v >= 999500 ? "M2" : "K0"); }

    function setLayer(key, dollars, project) {
      var L = layers[key];
      setVar(L.li, "--f", dollars / maxProject);
      L.li.setAttribute("aria-hidden", dollars > 0 ? "false" : "true");  /* a collapsed layer is not read out */
      put(L.amt, key === "loan" ? HX.fmt(dollars, "M2") : money(dollars));
      put(L.shr, HX.fmt(100 * dollars / project, "p0"));
    }

    function describe(c) {
      var s = "At " + HX.fmt(c.mult, "x2") + " EBITDA the price is " + HX.fmt(c.price, "M2") +
        " and the project costs " + HX.fmt(c.project, "M2") + ". From the bottom: SBA loan " + HX.fmt(c.sba, "M2") +
        ", seller note " + HX.fmt(c.standby, "K0") + (c.inv > 0 ? ", investors " + money(c.inv) : "") +
        ", buyer cash " + HX.fmt(c.own, "K0") + ". Bank test: cash for lenders " + HX.fmt(cfads, "K0") +
        ", yearly loan payment " + HX.fmt(c.payment, "K0") + ", DSCR " + HX.fmt(c.dscr, "x2") + ", " +
        (c.passes ? "passes" : "fails") + ".";
      if (c.inv > 0) {
        s += " The buyer owns " + HX.fmt(c.buyerShare, "p1") + " and investors " + HX.fmt(c.invShare, "p1") + ".";
      }
      if (c.overCap) { s += " Over the SBA 7(a) loan limit of " + HX.fmt(cap, "M1") + "."; }
      return s;
    }

    function announce(c) {
      if (!el.live) { return; }
      var s = "At " + HX.fmt(c.mult, "x2") + (state.on ? " with investors filling the gap" : "") + " the DSCR is " +
        HX.fmt(c.dscr, "x2") + ": " + (c.passes ? "passes" : "fails") + ".";
      if (c.inv > 0) {
        s += " Investors put in " + money(c.inv) + " and the buyer owns " + HX.fmt(c.buyerShare, "p1") + ".";
      } else if (state.on) {
        s += " The bank test already passes, so no investors are needed.";
      }
      if (c.overCap) { s += " Over the SBA 7(a) loan limit of " + HX.fmt(cap, "M1") + "."; }
      if (timer) { clearTimeout(timer); }
      timer = setTimeout(function () { el.live.textContent = s; }, 300);
    }

    function render(user) {
      var c = calc(state.mult, state.on);
      var hasInv = c.inv > 0;

      /* controls readout */
      put(el.ox, HX.fmt(c.mult, "x2"));
      put(el.op, HX.fmt(c.price, "M2"));
      inp.setAttribute("aria-valuetext", HX.fmt(c.mult, "x2") + " EBITDA, price " + HX.fmt(c.price, "M2") +
        ", bank test " + (c.passes ? "passes" : "fails"));
      buttons.forEach(function (b) {
        var on = b.getAttribute("data-mode") === "on";
        b.setAttribute("aria-pressed", on === state.on ? "true" : "false");
      });
      root.classList.toggle("is-inv", state.on);
      if (el.tickl) {
        if (state.on) {
          put(el.tickl, "Past here, investors fill the gap");
          tickOn = true;
        } else if (tickOn) {
          el.tickl.innerHTML = tickOff;
          tickOn = false;
        }
      }
      hint.hidden = !(state.on && !hasInv);
      put(hint, "At this price the bank lends enough on its own, so no investors are needed.");

      /* the stack */
      put(el.total, HX.fmt(c.project, "M2"));
      put(el.price, HX.fmt(c.price, "M2"));
      setLayer("loan", c.sba, c.project);
      setLayer("note", c.standby, c.project);
      setLayer("inv", c.inv, c.project);
      setLayer("cash", c.own, c.project);
      layers.inv.li.classList.toggle("is-off", !hasInv);
      layers.inv.li.setAttribute("aria-hidden", hasInv ? "false" : "true");
      if (el.own) { el.own.hidden = !hasInv; }
      put(el.ob, HX.fmt(c.buyerShare, "p1"));
      put(el.oi, HX.fmt(c.invShare, "p1"));

      /* the bank test */
      put(el.dv, HX.fmt(c.dscr, "x2"));
      put(el.pay, HX.fmt(c.payment, "K0"));
      put(el.bw, c.passes ? "Passes" : "Fails");
      [el.badge, el.test].forEach(function (e) {
        if (!e) { return; }
        e.classList.toggle("is-pass", c.passes);
        e.classList.toggle("is-fail", !c.passes);
      });
      if (el.badge && lastPass !== null && lastPass !== c.passes) {
        el.badge.classList.remove("pop");
        void el.badge.offsetWidth;
        el.badge.classList.add("pop");
      }
      lastPass = c.passes;

      /* the bar pair: cash for lenders against the payment plus the cushion lenders want (payment x the floor) */
      var wCash = 100 * cfads / axis, wPay = 100 * c.payment / axis, wEnd = 100 * c.payment * floor / axis;
      var room = cfads - c.payment * floor;
      setVar(el.bfCash, "--w", wCash);
      setVar(el.bfPay, "--w", wPay);
      setVar(el.bfCush, "--x", wPay);
      setVar(el.bfCush, "--w", Math.max(0, wEnd - wPay));
      if (c.passes) {
        setVar(el.bfGap, "--x", wEnd);
        setVar(el.bfGap, "--w", Math.max(0, wCash - wEnd));
      } else {
        setVar(el.bfGap, "--x", wCash);
        setVar(el.bfGap, "--w", Math.max(0, wEnd - wCash));
      }
      [el.bfGap, el.gl].forEach(function (e) {
        if (!e) { return; }
        e.classList.toggle("is-room", c.passes);
        e.classList.toggle("is-short", !c.passes);
      });
      put(el.gl, !c.passes ? "Short by " + HX.fmt(-room, "K0")
        : (room < 500 ? "Just enough: it matches the cushion lenders want" : "Room to spare: " + HX.fmt(room, "K0")));
      if (el.capmsg) { el.capmsg.hidden = !c.overCap; }

      chart.setAttribute("aria-label", describe(c));
      if (user) { announce(c); }
    }

    inp.addEventListener("input", function () {
      var v = parseFloat(inp.value);
      if (isFinite(v)) { state.mult = v; render(true); }
    });
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        state.on = b.getAttribute("data-mode") === "on";
        render(true);
      });
    });

    root.classList.add("fig-stack-js");
    render(false);
    HX.chartReady(chart);

    /* the layers build up from the bottom: the list is in bottom-to-top order */
    HX.reveal(root, function (tl) {
      addFrom(tl, root, ".fig-stack-layer:not(.is-off)", { opacity: 0, y: 26, duration: 0.7, stagger: 0.1, clearProps: "opacity,transform" }, 0);
      addFrom(tl, root, ".fig-stack-test", { opacity: 0, y: 12, duration: 0.6, clearProps: "opacity,transform" }, 0.2);
    });
  }

  HX.ready(function () {
    safe(initHouse);
    safe(initStack);
    safe(initFunds);
  });
})();
