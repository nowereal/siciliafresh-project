/* SiciliaFresh — interazioni della pagina dei risultati.
   JavaScript nativo, nessuna libreria. Tutti i dati sono gia scritti nell'HTML
   da Python: questo file aggiunge solo comportamento (selettori, tooltip,
   animazioni). Senza JavaScript la pagina mostra comunque ogni contenuto. */
(function () {
  "use strict";
  var root = document.documentElement;
  root.classList.add("js");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Formato numerico italiano, identico a quello usato da Python (1.234,56) */
  function fmt(value, decimals) {
    var parts = Math.abs(value).toFixed(decimals).split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (value < 0 ? "−" : "") + parts.join(",");
  }

  /* ---------- Contatori dei KPI (una sola volta) ---------- */
  function runCounter(el) {
    var target = parseFloat(el.dataset.count);
    var decimals = parseInt(el.dataset.decimals || "0", 10);
    var final = el.textContent;
    if (reduced || !isFinite(target)) return;
    var start = null, duration = 900;
    function frame(ts) {
      if (start === null) start = ts;
      var t = Math.min(1, (ts - start) / duration);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = t < 1 ? fmt(target * eased, decimals) : final;
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /* ---------- Disegno progressivo dei percorsi ---------- */
  function drawRoutes(scope) {
    scope.querySelectorAll(".g-draw").forEach(function (path) {
      if (reduced || !path.getTotalLength) return;
      var len = path.getTotalLength();
      path.style.transition = "none";
      path.style.strokeDasharray = len;
      path.style.strokeDashoffset = len;
      path.getBoundingClientRect();
      var delay = parseInt(path.dataset.delay || "0", 10);
      path.style.transition = "stroke-dashoffset 1.1s cubic-bezier(.45,.05,.25,1) " + delay + "ms";
      path.style.strokeDashoffset = 0;
    });
    scope.querySelectorAll(".g-node, .g-leg").forEach(function (node, i) {
      if (reduced) return;
      node.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 150 + i * 40, fill: "backwards" });
    });
  }

  function drawLines(scope) {
    scope.querySelectorAll(".line").forEach(function (line) {
      if (reduced || !line.getTotalLength) return;
      var len = line.getTotalLength();
      line.style.transition = "none";
      line.style.strokeDasharray = len;
      line.style.strokeDashoffset = len;
      line.getBoundingClientRect();
      line.style.transition = "stroke-dashoffset .9s cubic-bezier(.45,.05,.25,1)";
      line.style.strokeDashoffset = 0;
    });
  }

  /* ---------- Comparsa delle sezioni ---------- */
  var revealed = new WeakSet();
  function onVisible(el) {
    el.classList.add("in");
    if (revealed.has(el)) return;
    revealed.add(el);
    el.querySelectorAll(".count").forEach(runCounter);
    var graph = el.querySelector("[data-scenario-graph].is-active");
    if (graph) drawRoutes(graph);
    var sens = el.querySelector("[data-sens-panel].is-active");
    if (sens) drawLines(sens);
  }
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { onVisible(entry.target); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- Selettore degli scenari ---------- */
  function setScenario(key, animate) {
    document.querySelectorAll("[data-scenario-btn]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.scenarioBtn === key));
    });
    document.querySelectorAll("[data-scenario-graph], [data-scenario-panel]").forEach(function (el) {
      var on = (el.dataset.scenarioGraph || el.dataset.scenarioPanel) === key;
      el.classList.toggle("is-active", on);
      el.classList.remove("is-entering");
      if (on && animate && !reduced) { el.getBoundingClientRect(); el.classList.add("is-entering"); }
    });
    if (animate) {
      var graph = document.querySelector('[data-scenario-graph="' + key + '"]');
      if (graph) drawRoutes(graph);
    }
  }
  document.querySelectorAll("[data-scenario-btn]").forEach(function (b) {
    b.addEventListener("click", function () { setScenario(b.dataset.scenarioBtn, true); });
  });
  setScenario("A", false);

  /* ---------- Parametri dell'analisi di sensibilita ---------- */
  function setSens(index, animate) {
    document.querySelectorAll("[data-sens-btn]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.sensBtn === index));
    });
    document.querySelectorAll("[data-sens-panel]").forEach(function (p) {
      var on = p.dataset.sensPanel === index;
      p.classList.toggle("is-active", on);
      p.classList.remove("is-entering");
      if (on && animate && !reduced) { p.getBoundingClientRect(); p.classList.add("is-entering"); drawLines(p); }
    });
  }
  document.querySelectorAll("[data-sens-btn]").forEach(function (b) {
    b.addEventListener("click", function () { setSens(b.dataset.sensBtn, true); });
  });
  setSens("0", false);

  /* ---------- Tooltip ---------- */
  var tip = document.querySelector(".tooltip");
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.hidden = false;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var left = Math.min(window.innerWidth - w - 12, Math.max(12, x + 14));
    var top = y - h - 14 < 8 ? y + 18 : y - h - 14;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }
  function hideTip() { tip.hidden = true; }
  function escapeHtml(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

  document.querySelectorAll("[data-tip]").forEach(function (el) {
    el.addEventListener("mousemove", function (e) { showTip(escapeHtml(el.dataset.tip), e.clientX, e.clientY); });
    el.addEventListener("mouseleave", hideTip);
    el.addEventListener("focus", function () {
      var r = el.getBoundingClientRect();
      showTip(escapeHtml(el.dataset.tip), r.left + r.width / 2, r.top);
    });
    el.addEventListener("blur", hideTip);
  });

  /* Mirino sui grafici di sensibilita: punto calcolato piu vicino */
  document.querySelectorAll(".sens-chart").forEach(function (svg) {
    var d = JSON.parse(svg.dataset.series);
    var hit = svg.querySelector(".hit"), hover = svg.querySelector(".hover");
    var line = svg.querySelector(".hover-line"), ca = svg.querySelector(".hover-a"), cb = svg.querySelector(".hover-b");
    function px(v) { return d.left + (v - d.x0) / ((d.x1 - d.x0) || 1) * d.pw; }
    function py(v) { return d.top + d.ph - (v - d.y0) / ((d.y1 - d.y0) || 1) * d.ph; }
    hit.addEventListener("mousemove", function (e) {
      var pt = svg.createSVGPoint();
      pt.x = e.clientX; pt.y = e.clientY;
      var local = pt.matrixTransform(svg.getScreenCTM().inverse());
      var best = 0;
      d.x.forEach(function (v, i) { if (Math.abs(px(v) - local.x) < Math.abs(px(d.x[best]) - local.x)) best = i; });
      var x = px(d.x[best]);
      line.setAttribute("x1", x); line.setAttribute("x2", x);
      ca.setAttribute("cx", x); ca.setAttribute("cy", py(d.a[best]));
      cb.setAttribute("cx", x); cb.setAttribute("cy", py(d.b[best]));
      hover.classList.add("on");
      var diff = d.b[best] - d.a[best];
      showTip("<b>" + escapeHtml(d.label) + ": " + fmt(d.x[best], 2) + "</b>" +
        '<span><i style="background:var(--sa)"></i>Scenario A ' + fmt(d.a[best], 2) + " €</span>" +
        '<span><i style="background:var(--sb)"></i>Scenario B ' + fmt(d.b[best], 2) + " €</span>" +
        "<span>B − A " + (diff > 0 ? "+" : "") + fmt(diff, 2) + " €</span>", e.clientX, e.clientY);
    });
    hit.addEventListener("mouseleave", function () { hover.classList.remove("on"); hideTip(); });
  });

  window.addEventListener("scroll", hideTip, { passive: true });
})();
