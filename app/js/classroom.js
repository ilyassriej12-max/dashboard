/**
 * AI School OS - Classroom, Transition & Workspace (classroom.js)
 * Renders and runs the live classroom view (injected from classroom.html),
 * the classroom transition view, and the learning workspace view.
 * No visual/functional changes — only moved from the single-file index.html.
 */

(function () {
  "use strict";

  var icon = window.icon;
  var showView = window.showView;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var currentView = "dashboard";

  // ------------------------------------------------------------------
  // Classroom transition
  // ------------------------------------------------------------------

  var trTimers = [];

  function clearTransition() {
    trTimers.forEach(clearTimeout);
    trTimers = [];
    document.querySelectorAll("#trSteps .tr-step").forEach(function (s) {
      s.classList.remove("on", "loading");
    });
    var bar = document.querySelector("#view-transition .bar > i");
    if (bar) bar.style.width = "0%";
  }

  function runTransition() {
    clearTransition();
    var steps = Array.prototype.slice.call(document.querySelectorAll("#trSteps .tr-step"));
    var bar = document.querySelector("#view-transition .bar > i");
    if (reduce) {
      steps.forEach(function (s) { s.classList.add("on"); });
      if (bar) bar.style.width = "100%";
      trTimers.push(setTimeout(function () {
        if (currentView === "transition") { showView("classroom"); }
      }, 380));
      return;
    }
    var i = 0;
    function step() {
      if (i >= steps.length) {
        trTimers.push(setTimeout(function () {
          if (currentView === "transition") { showView("classroom"); }
        }, 560));
        return;
      }
      steps[i].classList.add("on", "loading");
      var cur = i; i++;
      trTimers.push(setTimeout(function () {
        steps[cur].classList.remove("loading");
        if (bar) bar.style.width = Math.round(i / steps.length * 100) + "%";
        step();
      }, 720));
    }
    trTimers.push(setTimeout(step, 280));
  }

  // ------------------------------------------------------------------
  // Live classroom
  // ------------------------------------------------------------------

  var clsInterval = null, clsSecs = 0;

  function startClassroom() {
    stopClassroom();
    clsSecs = 0;
    updateClock();
    clsInterval = setInterval(function () { clsSecs++; updateClock(); }, 1000);
  }

  function stopClassroom() {
    if (clsInterval) { clearInterval(clsInterval); clsInterval = null; }
  }

  function updateClock() {
    var el = document.getElementById("clsClock");
    if (!el) return;
    var m = Math.floor(clsSecs / 60), s = clsSecs % 60;
    el.textContent = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
  }

  var activeTool = "pen";

  function initClassroom() {
    // Clock
    startClassroom();

    // Mic / wave
    var micBtn = document.getElementById("micBtn");
    var wave = document.getElementById("wave");
    if (micBtn) {
      micBtn.addEventListener("click", function () {
        var on = micBtn.classList.toggle("on");
        micBtn.setAttribute("aria-pressed", on ? "true" : "false");
        if (wave) wave.classList.toggle("off", !on);
      });
    }

    // Notes toggle
    var notesToggle = document.getElementById("notesToggle");
    var notesBody = document.getElementById("notesBody");
    if (notesToggle) {
      notesToggle.addEventListener("click", function () {
        var open = notesToggle.getAttribute("aria-expanded") === "true";
        notesToggle.setAttribute("aria-expanded", open ? "false" : "true");
        if (notesBody) notesBody.classList.toggle("collapsed", open);
      });
    }

    // Dock tool selection
    document.querySelectorAll(".cls-dock .dock-tool[data-tool]").forEach(function (t) {
      t.addEventListener("click", function () {
        document.querySelectorAll(".cls-dock .dock-tool[data-tool]").forEach(function (o) {
          o.classList.remove("on");
        });
        t.classList.add("on");
      });
    });

    // Dock tool actions (pen / highlighter / eraser / note / star / bookmark)
    document.querySelectorAll(".cls-dock .dock-tool[data-tool]").forEach(function (t) {
      t.addEventListener("click", function () {
        activeTool = t.getAttribute("data-tool");
        document.querySelectorAll(".cls-dock .dock-tool[data-tool]").forEach(function (o) {
          var selected = o === t;
          o.classList.toggle("on", selected);
          o.setAttribute("aria-pressed", selected ? "true" : "false");
        });
        if (activeTool === "note") {
          var notes = document.querySelector("#notesBody textarea");
          if (notes) notes.focus();
        }
        if (activeTool === "star") { notify("Worked example saved as an important step."); }
        if (activeTool === "bookmark") { notify("Lesson bookmark added to your Library."); }
      });
    });

    // Whiteboard drawing
    bindDrawing(document.getElementById("classCanvas"));

    // Notes save / export
    var saveNotes = document.getElementById("saveNotes");
    var exportNotes = document.getElementById("exportNotes");
    if (saveNotes) {
      saveNotes.addEventListener("click", function () {
        var note = document.querySelector("#notesBody textarea");
        try {
          localStorage.setItem("ai-school-os:lesson-notes", note ? note.value : "");
          notify("Lesson notes saved on this device.");
        } catch (err) { notify("Notes could not be saved in this browser."); }
      });
    }
    if (exportNotes) {
      exportNotes.addEventListener("click", function () {
        var note = document.querySelector("#notesBody textarea");
        var blob = new Blob([note ? note.value : ""], { type: "text/plain" });
        var link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "ai-school-lesson-notes.txt";
        link.click();
        URL.revokeObjectURL(link.href);
      });
    }
    try {
      var savedNotes = localStorage.getItem("ai-school-os:lesson-notes");
      var lessonNotes = document.querySelector("#notesBody textarea");
      if (savedNotes && lessonNotes) lessonNotes.value = savedNotes;
    } catch (err) {}

    // Classroom controls
    document.querySelectorAll(".cls-controls .ctrl").forEach(function (button) {
      if (button.id === "micBtn") return;
      button.addEventListener("click", function () {
        if (button.classList.contains("danger")) {
          notify("Lesson ended. Your notes have been kept.");
          showView("dashboard");
          return;
        }
        var on = !button.classList.contains("on");
        button.classList.toggle("on", on);
        button.setAttribute("aria-pressed", on ? "true" : "false");
        notify(on ? "Classroom control enabled." : "Classroom control disabled.");
      });
    });

    // Focus mode
    var focusModeBtn = document.getElementById("focusModeBtn");
    if (focusModeBtn) {
      focusModeBtn.addEventListener("click", function () {
        var on = document.getElementById("view-classroom").classList.toggle("focus-mode");
        focusModeBtn.setAttribute("aria-pressed", on ? "true" : "false");
        focusModeBtn.textContent = on ? "Exit focus mode" : "Focus mode";
      });
    }
  }

  function notify(message) {
    var region = document.getElementById("toastRegion");
    if (!region) return;
    var toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    region.appendChild(toast);
    setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 4200);
  }

  function bindDrawing(canvas) {
    if (!canvas || canvas.dataset.drawingBound) return;
    canvas.dataset.drawingBound = "1";
    var ctx = canvas.getContext("2d");
    var drawing = false, last = null;

    function resize() {
      var rect = canvas.getBoundingClientRect();
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      if (!rect.width || !rect.height) return;
      var snapshot = canvas.width && canvas.height ? canvas.toDataURL() : null;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (snapshot) {
        var image = new Image();
        image.onload = function () { ctx.drawImage(image, 0, 0, rect.width, rect.height); };
        image.src = snapshot;
      }
    }

    function point(e) {
      var r = canvas.getBoundingClientRect();
      return { x: e.clientX - r.left, y: e.clientY - r.top };
    }

    function draw(to) {
      if (!last) return;
      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.globalCompositeOperation = activeTool === "eraser" ? "destination-out" : "source-over";
      ctx.globalAlpha = activeTool === "highlighter" ? 0.34 : 0.94;
      ctx.strokeStyle = activeTool === "highlighter" ? "#22D3EE" : "#6D93FF";
      ctx.lineWidth = activeTool === "eraser" ? 24 : (activeTool === "highlighter" ? 18 : 3);
      ctx.beginPath();
      ctx.moveTo(last.x, last.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
      ctx.restore();
      last = to;
    }

    canvas.addEventListener("pointerdown", function (e) {
      if (activeTool !== "pen" && activeTool !== "highlighter" && activeTool !== "eraser") return;
      drawing = true;
      last = point(e);
      canvas.setPointerCapture(e.pointerId);
      var board = canvas.closest(".cls-board");
      if (board) board.classList.add("drawing");
    });
    canvas.addEventListener("pointermove", function (e) { if (drawing) draw(point(e)); });
    function end(e) {
      if (!drawing) return;
      drawing = false;
      last = null;
      if (canvas.hasPointerCapture(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
      var board = canvas.closest(".cls-board");
      if (board) board.classList.remove("drawing");
    }
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);
    canvas.addEventListener("keydown", function (e) {
      if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        notify("Whiteboard cleared.");
      }
    });
    resize();
    window.addEventListener("resize", resize);
  }

  // ------------------------------------------------------------------
  // Learning workspace
  // ------------------------------------------------------------------

  var wsPanels = {
    notebook: { t: "Notebook", i: "#i-notebook", x: 0, y: 0, w: 330, h: 540,
      b: '<p class="hint" style="margin-bottom:12px">Live notebook · synced to the lesson</p>' +
         '<div class="ws-code">\\int u dv = uv - \\int v du\\n\\n<b>u = x</b>  (algebraic)\\ndv = e^x dx  (exponential)\\n\\n-> du = dx,  v = e^x\\n-> x·e^x - \\int e^x dx\\n-> e^x (x - 1) + C</div>' +
         '<div style="margin-top:14px"><div class="ws-line"></div><div class="ws-line m"></div><div class="ws-line s"></div><div class="ws-line m"></div></div>' },
    whiteboard: { t: "Whiteboard", i: "#i-board", x: 342, y: 0, w: 520, h: 260,
      b: '<div class="ws-board-draw"><span>Given  \\int u dv = uv - \\int v du</span><span>Step 1  u = x,  dv = e^x dx</span><span>Step 2  = x·e^x - \\int e^x dx</span><span>Result  e^x (x - 1) + C</span><canvas class="draw-canvas" id="wsBoardCanvas" tabindex="0" aria-label="Workspace whiteboard. Use the classroom drawing tools."></canvas></div>' +
         '<div class="tag-row" style="margin-top:12px"><span class="tag color"><svg style="width:13px;height:13px"><use href="#i-pen"/></svg>Pen</span><span class="tag"><svg style="width:13px;height:13px"><use href="#i-eraser"/></svg>Eraser</span><span class="tag">Grid on</span></div>' },
    video: { t: "Video lesson", i: "#i-video", x: 342, y: 272, w: 520, h: 268,
      b: '<div class="ws-video"><button class="pbtn" aria-label="Play"><svg><use href="#i-play"/></svg></button><span class="pbar"><i></i></span></div>' +
         '<div class="od-row" style="justify-content:space-between;margin-top:12px"><span class="hint">Integration by Parts · 12:40</span><span class="tag">1.25×</span></div>' },
    pdf: { t: "Worksheet.pdf", i: "#i-file", x: 874, y: 0, w: 330, h: 330,
      b: '<div class="ws-pdf-page"><div class="pl h"></div><div class="pl"></div><div class="pl"></div><div class="pl" style="width:74%"></div><div class="pl"></div><div class="pl" style="width:56%"></div></div>' +
         '<div class="ws-pdf-bar"><span>Page 2 of 6</span><span>Integration by Parts</span></div>' },
    simulation: { t: "Wave simulator", i: "#i-atom", x: 874, y: 342, w: 330, h: 198,
      b: '<div class="ws-sim"><div class="sim-stage"><span class="ball"></span></div><div class="sim-read"><span>Amplitude</span><b id="simVal">0.62</b></div><input type="range" min="0" max="100" value="62" aria-label="Amplitude"></div>' }
  };

  var wsZ = 10;

  function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }

  function applyGeom(p) {
    p.style.left = (parseFloat(p.dataset.x) || 0) + "px";
    p.style.top = (parseFloat(p.dataset.y) || 0) + "px";
    p.style.width = (parseFloat(p.dataset.w) || 300) + "px";
    p.style.height = (parseFloat(p.dataset.h) || 240) + "px";
  }

  function wsPanelEl(id) {
    var d = wsPanels[id];
    var el = document.createElement("article");
    el.className = "ws-panel";
    el.dataset.panel = id;
    el.dataset.x = d.x; el.dataset.y = d.y; el.dataset.w = d.w; el.dataset.h = d.h;
    el.innerHTML =
      '<header class="ws-head" tabindex="0" aria-label="' + d.t + ' panel. Use Alt plus arrow keys to move."><button class="ws-grip" type="button" aria-label="Move ' + d.t + ' panel with Alt plus arrow keys"><svg><use href="#i-drag"/></svg></button>' +
      '<span class="ws-ico"><svg><use href="' + d.i + '"/></svg></span>' +
      '<span class="ws-title">' + d.t + '</span>' +
      '<span class="ws-tools"><button data-wsbtn="collapse" aria-label="Collapse"><svg><use href="#i-chevron"/></svg></button>' +
      '<button data-wsbtn="max" aria-label="Maximize"><svg><use href="#i-expand"/></svg></button>' +
      '<button data-wsbtn="close" class="close" aria-label="Close"><svg><use href="#i-close"/></svg></button></span></header>' +
      '<div class="ws-body">' + d.b + '</div><span class="ws-resize" aria-hidden="true"></span>';
    return el;
  }

  function bindPanel(p) {
    if (p.dataset.bound) return;
    p.dataset.bound = "1";
    var head = p.querySelector(".ws-head");
    var rz = p.querySelector(".ws-resize");
    p.addEventListener("pointerdown", function () { p.style.zIndex = ++wsZ; });
    head.addEventListener("pointerdown", function (e) {
      if (e.target.closest("[data-wsbtn]")) return;
      if (window.innerWidth <= 900) return;
      dragPanel(e, p, "move");
    });
    head.addEventListener("keydown", function (e) {
      if (!e.altKey || !/^Arrow/.test(e.key) || window.innerWidth <= 900) return;
      e.preventDefault();
      var rect = p.parentElement.getBoundingClientRect();
      var step = 24;
      var x = parseFloat(p.dataset.x) || 0, y = parseFloat(p.dataset.y) || 0;
      if (e.key === "ArrowLeft") x -= step;
      if (e.key === "ArrowRight") x += step;
      if (e.key === "ArrowUp") y -= step;
      if (e.key === "ArrowDown") y += step;
      p.dataset.x = clamp(x, 0, Math.max(0, rect.width - (parseFloat(p.dataset.w) || 300)));
      p.dataset.y = clamp(y, 0, Math.max(0, rect.height - (parseFloat(p.dataset.h) || 240)));
      applyGeom(p);
    });
    if (rz) rz.addEventListener("pointerdown", function (e) { dragPanel(e, p, "resize"); });
    p.querySelectorAll("[data-wsbtn]").forEach(function (b) {
      b.addEventListener("click", function (ev) {
        ev.stopPropagation();
        var k = b.getAttribute("data-wsbtn");
        if (k === "collapse") p.classList.toggle("collapsed");
        else if (k === "max") p.classList.toggle("max");
        else if (k === "close") p.classList.add("hidden");
      });
    });
  }

  function dragPanel(e, p, mode) {
    e.preventDefault();
    var rect = p.parentElement.getBoundingClientRect();
    var sx = e.clientX, sy = e.clientY;
    var L = parseFloat(p.dataset.x) || 0, T = parseFloat(p.dataset.y) || 0;
    var W = parseFloat(p.dataset.w) || 300, H = parseFloat(p.dataset.h) || 240;
    p.classList.add("dragging");
    function move(ev) {
      var dx = ev.clientX - sx, dy = ev.clientY - sy;
      if (mode === "move") {
        p.dataset.x = clamp(L + dx, 0, Math.max(0, rect.width - W));
        p.dataset.y = clamp(T + dy, 0, Math.max(0, rect.height - 60));
      } else {
        p.dataset.w = clamp(W + dx, 220, Math.max(240, rect.width - L));
        p.dataset.h = clamp(H + dy, 120, Math.max(160, rect.height - T));
      }
      applyGeom(p);
    }
    function up() {
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
      p.classList.remove("dragging");
    }
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", up);
  }

  function rescaleCanvas() {
    var canvas = document.getElementById("wsCanvas");
    if (!canvas || window.innerWidth <= 900) return;
    var rect = canvas.getBoundingClientRect();
    var availW = Math.max(240, rect.width - 24);
    var availH = Math.max(160, rect.height - 24);
    canvas.querySelectorAll(".ws-panel").forEach(function (p) {
      var w = clamp(parseFloat(p.dataset.w) || 300, 220, availW);
      var h = clamp(parseFloat(p.dataset.h) || 240, 120, availH);
      p.dataset.w = w;
      p.dataset.h = h;
      p.dataset.x = clamp(parseFloat(p.dataset.x) || 0, 0, Math.max(0, rect.width - w - 12));
      p.dataset.y = clamp(parseFloat(p.dataset.y) || 0, 0, Math.max(0, rect.height - h - 12));
      applyGeom(p);
    });
  }

  function buildPanels(canvas) {
    canvas.innerHTML = "";
    Object.keys(wsPanels).forEach(function (id) {
      var el = wsPanelEl(id);
      canvas.appendChild(el);
      bindPanel(el);
    });
    bindDrawing(canvas.querySelector("#wsBoardCanvas"));
  }

  function addPanel(id) {
    var canvas = document.getElementById("wsCanvas");
    if (!canvas || !wsPanels[id]) return;
    var existing = canvas.querySelector('[data-panel="' + id + '"]');
    if (existing) {
      existing.classList.remove("hidden");
      existing.style.zIndex = ++wsZ;
      return;
    }
    var el = wsPanelEl(id);
    canvas.appendChild(el);
    bindPanel(el);
    if (id === "whiteboard") bindDrawing(el.querySelector("#wsBoardCanvas"));
    el.style.zIndex = ++wsZ;
    rescaleCanvas();
  }

  function initWorkspace() {
    var canvas = document.getElementById("wsCanvas");
    if (!canvas) return;
    if (!canvas.dataset.ready) {
      canvas.dataset.ready = "1";
      buildPanels(canvas);
      var rz = document.getElementById("wsReset");
      if (rz) {
        rz.addEventListener("click", function () { buildPanels(canvas); rescaleCanvas(); });
      }
      window.addEventListener("resize", function () {
        if (currentView === "workspace") rescaleCanvas();
      });
    }
    rescaleCanvas();
  }

  document.querySelectorAll("[data-addpanel]").forEach(function (b) {
    b.addEventListener("click", function () {
      addPanel(b.getAttribute("data-addpanel"));
    });
  });

  document.addEventListener("input", function (e) {
    if (e.target && e.target.type === "range") {
      var v = document.getElementById("simVal");
      if (v) v.textContent = (e.target.value / 100).toFixed(2);
    }
  });

  // Expose
  window.initClassroom = initClassroom;
  window.initWorkspace = initWorkspace;
  window.startClassroom = startClassroom;
  window.stopClassroom = stopClassroom;
  window.clearTransition = clearTransition;
  window.runTransition = runTransition;
})();
