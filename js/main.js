/* Pando Surgical website interactions */
(function () {
  "use strict";

  var root = document.documentElement;
  var body = document.body;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  /* ---------- Theme toggle (cold / warm) ---------- */
  function setThemeLabel() {
    var warm = root.getAttribute("data-theme") === "warm";
    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      var label = btn.querySelector(".theme-label");
      if (label) label.textContent = warm ? "Warm" : "Cold";
      btn.setAttribute("aria-label", "Color theme: " + (warm ? "warm" : "cold") + ". Switch to " + (warm ? "cold" : "warm"));
    });
  }
  setThemeLabel();
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var next = root.getAttribute("data-theme") === "warm" ? "cold" : "warm";
    root.setAttribute("data-theme", next);
    store("pando-theme", next);
    setThemeLabel();
  });

  /* ---------- Page fade in / fade out (Dissolve, ease-out, 300ms) ---------- */
  requestAnimationFrame(function () { body.classList.add("is-ready"); });
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) { body.classList.remove("is-leaving"); body.classList.add("is-ready"); }
  });
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    if (a.target === "_blank" || a.hasAttribute("download")) return;
    var href = a.getAttribute("href");
    if (!href || href.charAt(0) === "#" || /^(mailto|tel|https?):/i.test(href)) return;
    if (reduceMotion) return;
    e.preventDefault();
    body.classList.remove("is-ready");
    body.classList.add("is-leaving");
    setTimeout(function () { window.location.href = a.href; }, 300);
  });

  /* ---------- Nav: hide on scroll down, show on scroll up ---------- */
  var nav = document.querySelector(".nav");
  var lastY = window.scrollY;
  window.addEventListener("scroll", function () {
    var y = window.scrollY;
    if (!nav) return;
    var menuOpen = nav.classList.contains("menu-open");
    var ddOpen = nav.querySelector(".dd.is-open");
    if (y > lastY + 4 && y > 120 && !menuOpen && !ddOpen) nav.classList.add("is-hidden");
    else if (y < lastY - 4 || y <= 120) nav.classList.remove("is-hidden");
    lastY = y;
  }, { passive: true });

  /* ---------- Dropdowns ---------- */
  var dds = Array.prototype.slice.call(document.querySelectorAll(".dd"));
  var canHover = window.matchMedia("(hover: hover)").matches;
  function closeAll(except) {
    dds.forEach(function (dd) {
      if (dd === except) return;
      dd.classList.remove("is-open");
      var t = dd.querySelector(".dd-toggle");
      if (t) t.setAttribute("aria-expanded", "false");
    });
  }
  dds.forEach(function (dd) {
    var toggle = dd.querySelector(".dd-toggle");
    var timer;
    function open() { clearTimeout(timer); closeAll(dd); dd.classList.add("is-open"); toggle.setAttribute("aria-expanded", "true"); }
    function close() { dd.classList.remove("is-open"); toggle.setAttribute("aria-expanded", "false"); }
    toggle.addEventListener("click", function () { dd.classList.contains("is-open") ? close() : open(); });
    if (canHover) {
      dd.addEventListener("mouseenter", open);
      dd.addEventListener("mouseleave", function () { timer = setTimeout(close, 180); });
    }
    dd.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { close(); toggle.focus(); }
    });
    dd.addEventListener("focusout", function (e) {
      if (!dd.contains(e.relatedTarget)) close();
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".dd")) closeAll();
  });

  /* ---------- Mobile menu ---------- */
  var burger = document.querySelector(".nav-burger");
  if (burger) {
    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("menu-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- Rolling hero word ---------- */
  var track = document.querySelector(".rolling-track");
  if (track && !reduceMotion) {
    var words = track.children.length - 1; // last item repeats the first for a seamless loop
    var i = 0;
    setInterval(function () {
      i += 1;
      track.style.transition = "";
      track.style.transform = "translateY(" + (-100 * i / (words + 1)) + "%)";
      if (i === words) {
        setTimeout(function () {
          track.style.transition = "none";
          track.style.transform = "translateY(0)";
          i = 0;
        }, 650);
      }
    }, 2400);
  }

  /* ---------- Count-up (0 -> 78%) when scrolled into view ---------- */
  var counters = document.querySelectorAll("[data-count]");
  function runCount(el) {
    var target = parseInt(el.getAttribute("data-count"), 10);
    var suffix = el.getAttribute("data-suffix") || "";
    if (reduceMotion) { el.textContent = target + suffix; return; }
    var start = null, dur = 600;
    function step(t) {
      if (!start) start = t;
      var p = Math.min((t - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ---------- Reveal + count-up observer ---------- */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        if (el.hasAttribute("data-count")) runCount(el);
        else el.classList.add("is-in");
        io.unobserve(el);
      });
    }, { threshold: 0.35 });
    counters.forEach(function (el) { el.textContent = "0" + (el.getAttribute("data-suffix") || ""); io.observe(el); });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- Tabs ---------- */
  document.querySelectorAll("[role=tablist]").forEach(function (list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll("[role=tab]"));
    // One underline that slides from tab to tab
    var bar = document.createElement("span");
    bar.className = "tab-indicator no-anim";
    bar.setAttribute("aria-hidden", "true");
    list.appendChild(bar);
    list.classList.add("has-indicator");
    function current() { return list.querySelector('[aria-selected="true"]') || tabs[0]; }
    function place(tab) {
      bar.style.width = tab.offsetWidth + "px";
      bar.style.transform = "translateX(" + tab.offsetLeft + "px)";
    }
    function placeNow() {
      bar.classList.add("no-anim");
      place(current());
      void bar.offsetWidth; // apply the jump before turning the slide back on
      bar.classList.remove("no-anim");
    }
    placeNow();
    window.addEventListener("resize", placeNow);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeNow);
    function select(tab) {
      if (tab === current()) return;
      tabs.forEach(function (t) {
        var on = t === tab;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        panel.hidden = !on;
        panel.classList.remove("is-entering");
        if (on) { void panel.offsetWidth; panel.classList.add("is-entering"); }
      });
      place(tab);
    }
    tabs.forEach(function (tab, idx) {
      tab.addEventListener("click", function () { select(tab); });
      tab.addEventListener("keydown", function (e) {
        var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        var next = tabs[(idx + d + tabs.length) % tabs.length];
        select(next); next.focus();
      });
    });
  });

  /* ---------- LapRotator render slideshow ----------
     Each render shows ~4 s, then the CSS fades it into the next (Figma "LapRotator Render Slideshow").
     Runs only while on screen and the page is visible; with reduced motion it stays on the first image. */
  document.querySelectorAll(".lr-slides").forEach(function (box) {
    var slides = box.querySelectorAll("img");
    if (slides.length < 2 || reduceMotion || !("IntersectionObserver" in window)) return;
    var i = 0, timer = 0, onScreen = false;
    function next() {
      slides[i].classList.remove("is-on");
      i = (i + 1) % slides.length;
      slides[i].classList.add("is-on");
    }
    function sync() {
      var run = onScreen && !document.hidden;
      if (run && !timer) timer = setInterval(next, 4800);
      if (!run && timer) { clearInterval(timer); timer = 0; }
    }
    new IntersectionObserver(function (entries) {
      onScreen = entries[entries.length - 1].isIntersecting;
      sync();
    }).observe(box);
    document.addEventListener("visibilitychange", sync);
  });

  /* ---------- Modals (Log in, news stories) ---------- */
  var lastFocus = null;
  function openModal(id) {
    var m = document.getElementById(id);
    if (!m) return;
    lastFocus = document.activeElement;
    m.classList.add("is-open");
    m.setAttribute("aria-hidden", "false");
    body.classList.add("modal-open");
    var f = m.querySelector("input, button.modal-close");
    if (f) setTimeout(function () { f.focus(); }, 50);
  }
  function closeModal(m) {
    m.classList.remove("is-open");
    m.setAttribute("aria-hidden", "true");
    if (!document.querySelector(".modal.is-open")) body.classList.remove("modal-open");
    if (lastFocus) lastFocus.focus();
  }
  document.addEventListener("click", function (e) {
    var opener = e.target.closest("[data-modal]");
    if (opener) { e.preventDefault(); openModal(opener.getAttribute("data-modal")); return; }
    if (e.target.closest(".modal-close")) { closeModal(e.target.closest(".modal")); return; }
    if (e.target.classList && e.target.classList.contains("modal")) closeModal(e.target);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var m = document.querySelector(".modal.is-open");
    if (m) closeModal(m);
  });
  if (location.hash === "#login") openModal("login");

  /* Password show / hide */
  document.querySelectorAll(".eye").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = btn.parentNode.querySelector("input");
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  });

  /* ---------- Word counters (Careers) ---------- */
  document.querySelectorAll("[data-words]").forEach(function (ta) {
    var max = parseInt(ta.getAttribute("data-words"), 10);
    var counter = document.getElementById(ta.getAttribute("aria-describedby"));
    function update() {
      var n = ta.value.trim() ? ta.value.trim().split(/\s+/).length : 0;
      counter.textContent = n + "/" + max + " words";
      counter.classList.toggle("over", n > max);
      ta.setCustomValidity(n > max ? "Please keep this under " + max + " words." : "");
    }
    ta.addEventListener("input", update);
    update();
  });

  /* ---------- Forms (front end only for now) ---------- */
  document.querySelectorAll("form[data-demo]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var note = form.querySelector(".form-note");
      if (note) note.textContent = form.getAttribute("data-demo");
    });
  });

  /* ---------- LapRotator hero: float on hover (Figma "LapRotator Hover Drift") ----------
     Mouse in: rises 12px (800ms ease-out), then circles up, right, down, left, 12px each step (1.4s ease-in-out).
     Mouse out: settles back to rest (800ms ease-out). */
  var lrHero = document.querySelector(".lr-hero");
  var lrFloat = lrHero && lrHero.querySelector(".lr-float");
  if (lrFloat && !reduceMotion && lrFloat.animate) {
    var orbit = [[0, -12], [12, 0], [0, 12], [-12, 0]];
    var step = 0, floatAnim = null, hovering = false;
    var currentOffset = function () {
      var t = getComputedStyle(lrFloat).translate;
      if (!t || t === "none") return [0, 0];
      var p = t.split(" ").map(parseFloat);
      return [p[0] || 0, p[1] || 0];
    };
    var moveTo = function (to, duration, easing, then) {
      var from = currentOffset();
      if (floatAnim) floatAnim.cancel();
      floatAnim = lrFloat.animate(
        [{ translate: from[0] + "px " + from[1] + "px" }, { translate: to[0] + "px " + to[1] + "px" }],
        { duration: duration, easing: easing, fill: "forwards" }
      );
      floatAnim.onfinish = then || null;
    };
    var next = function () {
      if (!hovering) return;
      step = (step + 1) % orbit.length;
      moveTo(orbit[step], 1400, "ease-in-out", next);
    };
    lrHero.addEventListener("mouseenter", function () {
      hovering = true; step = 0;
      moveTo(orbit[0], 800, "ease-out", next);
    });
    lrHero.addEventListener("mouseleave", function () {
      hovering = false;
      moveTo([0, 0], 800, "ease-out");
    });
  }

  /* ---------- Demo videos: stay still for people who ask for reduced motion ---------- */
  if (reduceMotion) {
    document.querySelectorAll("video[autoplay]").forEach(function (v) { v.removeAttribute("autoplay"); v.pause(); });
  }
})();
