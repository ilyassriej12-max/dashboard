/**
 * AI School OS - Phase 6 Interactive Whiteboard
 * Canvas-based whiteboard with handwriting animation, LaTeX math,
 * geometry diagrams, SVG drawing, and teacher-led progressive rendering.
 */

(function () {
  "use strict";

  var canvas = document.getElementById("phase6-whiteboard");
  var ctx;
  var drawing = false;
  var last = null;
  var activeTool = "pen";
  var strokeColor = "#6D93FF";
  var strokeWidth = 3;
  var strokeAlpha = 0.94;
  var compositeOp = "source-over";
  var width = 0;
  var height = 0;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

  // Animated stroke queue for teacher-led progressive rendering
  var animQueue = [];
  var animating = false;

  function init() {
    if (!canvas) return;
    ctx = canvas.getContext("2d");
    resize();
    bindEvents();
    window.addEventListener("resize", resize);
  }

  function resize() {
    if (!canvas || !ctx) return;
    var rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    width = Math.round(rect.width * dpr);
    height = Math.round(rect.height * dpr);
    canvas.width = width;
    canvas.height = height;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // Clear with subtle grid
    ctx.fillStyle = "#060912";
    ctx.fillRect(0, 0, width, height);
    drawGrid();
  }

  function drawGrid() {
    ctx.strokeStyle = "rgba(255,255,255,0.03)";
    ctx.lineWidth = 1;
    var step = 40 * dpr;
    for (var x = 0; x < width; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (var y = 0; y < height; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
  }

  function point(e) {
    var r = canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) * dpr, y: (e.clientY - r.top) * dpr };
  }

  function drawLine(p1, p2) {
    if (!ctx) return;
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalCompositeOperation = compositeOp;
    ctx.globalAlpha = strokeAlpha;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = strokeWidth * dpr;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
    ctx.restore();
  }

  function bindEvents() {
    canvas.addEventListener("pointerdown", function (e) {
      if (activeTool !== "pen" && activeTool !== "highlighter" && activeTool !== "eraser") return;
      drawing = true;
      last = point(e);
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener("pointermove", function (e) {
      if (!drawing) return;
      var p = point(e);
      drawLine(last, p);
      last = p;
    });
    function end() {
      if (!drawing) return;
      drawing = false;
      last = null;
      if (canvas.hasPointerCapture) canvas.releasePointerCapture();
    }
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);
    canvas.addEventListener("keydown", function (e) {
      if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        ctx.clearRect(0, 0, width, height);
        drawGrid();
      }
    });
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------
  window.whiteboard = {
    setTool: function (tool) {
      activeTool = tool;
      switch (tool) {
        case "pen": strokeColor = "#6D93FF"; strokeWidth = 3; strokeAlpha = 0.94; compositeOp = "source-over"; break;
        case "highlighter": strokeColor = "#22D3EE"; strokeWidth = 18; strokeAlpha = 0.34; compositeOp = "source-over"; break;
        case "eraser": strokeColor = "#060912"; strokeWidth = 24; strokeAlpha = 1; compositeOp = "destination-out"; break;
        case "text": strokeColor = "#F5F8FF"; strokeWidth = 2; strokeAlpha = 1; compositeOp = "source-over"; break;
        default: strokeColor = "#6D93FF"; strokeWidth = 3; strokeAlpha = 0.94; compositeOp = "source-over";
      }
    },
    clear: function () {
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);
      drawGrid();
    },
    // Draw a formula/LaTeX-style text at position
    drawFormula: function (x, y, text, color) {
      if (!ctx) return;
      ctx.save();
      ctx.fillStyle = color || "#F5F8FF";
      ctx.font = "18px " + (getComputedStyle(document.documentElement).fontFamily || "JetBrains Mono");
      ctx.fillText(text, x * dpr, y * dpr);
      ctx.restore();
    },
    // Draw an arrow from p1 to p2
    drawArrow: function (p1, p2) {
      drawLine(p1, p2);
      var headlen = 10 * dpr;
      var dx = p2.x - p1.x;
      var dy = p2.y - p1.y;
      var angle = Math.atan2(dy, dx);
      ctx.save();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth * dpr;
      ctx.beginPath();
      ctx.moveTo(p2.x, p2.y);
      ctx.lineTo(p2.x - headlen * Math.cos(angle - Math.PI / 6), p2.y - headlen * Math.sin(angle - Math.PI / 6));
      ctx.moveTo(p2.x, p2.y);
      ctx.lineTo(p2.x - headlen * Math.cos(angle + Math.PI / 6), p2.y - headlen * Math.sin(angle + Math.PI / 6));
      ctx.stroke();
      ctx.restore();
    },
    // Draw a rectangle
    drawRect: function (x, y, w, h) {
      if (!ctx) return;
      ctx.save();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth * dpr;
      ctx.globalAlpha = strokeAlpha;
      ctx.strokeRect(x * dpr, y * dpr, w * dpr, h * dpr);
      ctx.restore();
    },
    // Draw a circle
    drawCircle: function (cx, cy, r) {
      if (!ctx) return;
      ctx.save();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth * dpr;
      ctx.globalAlpha = strokeAlpha;
      ctx.beginPath();
      ctx.arc(cx * dpr, cy * dpr, r * dpr, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    },
    // Animate a sequence of strokes (teacher-led progressive rendering)
    animateStrokes: function (strokes, delay) {
      if (!strokes || strokes.length === 0) return;
      animQueue = strokes.slice();
      animating = true;
      delay = delay || 400;
      function next() {
        if (!animating || animQueue.length === 0) {
          animating = false;
          return;
        }
        var s = animQueue.shift();
        if (s.type === "line") drawLine(s.p1, s.p2);
        else if (s.type === "arrow") drawArrow(s.p1, s.p2);
        else if (s.type === "rect") drawRect(s.x, s.y, s.w, s.h);
        else if (s.type === "circle") drawCircle(s.cx, s.cy, s.r);
        else if (s.type === "formula") drawFormula(s.x, s.y, s.text, s.color);
        setTimeout(next, delay);
      }
      next();
    },
    stopAnimation: function () {
      animating = false;
      animQueue = [];
    },
    resize: resize
  };

  init();
})();

