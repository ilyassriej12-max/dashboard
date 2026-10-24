/**
 * AI School OS - Dashboard & Subject Page (dashboard.js)
 * Renders the dashboard view (injected from dashboard.html) and the subject
 * page view (inline in index.html). No visual/functional changes to the data
 * or markup — only moved here from the single-file index.html.
 */

(function () {
  "use strict";

  var escapeHtml = window.escapeHtml;
  var icon = window.icon;
  var showView = window.showView;
  var subjects = window.AppStore.get("subjects");

  // expose subject list for search module in home.js
  window.__subjects = subjects.map(function (s) {
    return { id: s.id, n: s.name, s: s.description, teacher: s.teacher };
  });

  // ------------------------------------------------------------------
  // Dashboard rendering (runs when dashboard partial is injected)
  // ------------------------------------------------------------------

  function subjectCard(d, i) {
    return '<article class="card subject reveal" style="--i:' + (i % 12) + '">' +
      '<div class="head"><span class="emoji">' + d.icon + '</span><div><h3>' + d.name + '</h3><p class="subject-sub">' + d.description + '</p></div></div>' +
      '<div><div class="pct"><span>Progress</span><b>' + d.progress + '%</b></div><div class="bar"><i data-w="' + d.progress + '" style="background:' + d.color + ';animation:none"></i></div></div>' +
      '<button class="go" data-goview="subject" data-subject="' + d.id + '">Continue<svg><use href="#i-arrow"/></svg></button></article>';
  }

  function renderDashboard() {
    var grid = document.getElementById("subjectGrid");
    var gridFull = document.getElementById("subjectGridFull");
    if (grid) { grid.innerHTML = subjects.slice(0, 8).map(subjectCard).join(""); }
    if (gridFull) { gridFull.innerHTML = subjects.map(subjectCard).join(""); }

    var progressGrid = document.getElementById("progressGrid");
    if (progressGrid) {
      progressGrid.innerHTML = [
        { l: "Mastery", v: 84, u: "%", c: "var(--success)" },
        { l: "Completion", v: 91, u: "%", c: "var(--warning)" },
        { l: "Retention", v: 76, u: "%", c: "var(--primary)" }
      ].map(function (m) {
        return '<article class="card metric"><div class="label"><svg class="tone-primary"><use href="#i-target"/></svg>' + m.l + '</div><div class="big"><span data-count="' + m.v + '">0</span><small>' + m.u + '</small></div><div class="chart"><div class="mini-bars"><i style="--h:40;--i:0"></i><i style="--h:66;--i:1"></i><i style="--h:52;--i:2"></i><i class="hot" style="--h:88;--i:3"></i><i style="--h:70;--i:4"></i><i style="--h:94;--i:5"></i></div></div></article>';
      }).join("");
    }

    var swatches = document.getElementById("swatches");
    if (swatches) {
      var tokens = [
        ["Primary", "#4F7CFF"], ["Secondary", "#A855F7"], ["Accent", "#22D3EE"],
        ["Success", "#34D399"], ["Warning", "#FB923C"], ["Danger", "#F87171"],
        ["Background", "#060912"], ["Surface", "#0A1120"], ["Text", "#F5F8FF"], ["Muted", "#8EA0B8"]
      ];
      swatches.innerHTML = tokens.map(function (t) {
        return '<div class="swatch"><div class="chipd" style="background:' + t[1] + '"></div><div class="meta"><b>' + t[0] + '</b><span>' + t[1] + '</span></div></div>';
      }).join("");
    }

    if (window.activateBars) window.activateBars(document);
    if (window.activateRings) window.activateRings(document);
    if (window.activateNumbers) window.activateNumbers(document);
  }

  function filterSubjects(filter) {
    var filtered = subjects.filter(function (s) {
      if (filter === "progress") return s.progress > 0 && s.progress < 100;
      if (filter === "recommended") return s.mastery < 70;
      if (filter === "completed") return s.progress >= 75;
      return true;
    });
    var gridFull = document.getElementById("subjectGridFull");
    if (gridFull) { gridFull.innerHTML = filtered.map(subjectCard).join(""); }
    document.querySelectorAll("[data-subject-filter]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-subject-filter") === filter ? "true" : "false");
    });
    if (window.activateBars) window.activateBars(gridFull || document);
  }

  // ------------------------------------------------------------------
  // Subject page data & rendering
  // ------------------------------------------------------------------

  var currentSubjectId = "mathematics";
  var SUBJECT = { emoji: "\u2211" };

  var subStatsData = [
    { l: "Progress", v: 62, u: "%", i: "#i-progress", tone: "tone-primary" },
    { l: "Mastery", v: 84, u: "%", i: "#i-target", tone: "tone-success" },
    { l: "Lessons done", v: 36, u: " / 58", i: "#i-check", tone: "tone-accent" },
    { l: "Avg. practice", v: 14, u: " min", i: "#i-clock", tone: "tone-warning" }
  ];

  var roadmapData = [
    { n: "Foundations & Limits", s: "12 lessons · checkpoint", p: 100, st: "done" },
    { n: "Derivatives", s: "10 lessons · checkpoint", p: 100, st: "done" },
    { n: "Integration Techniques", s: "9 lessons · checkpoint", p: 62, st: "active" },
    { n: "Integration by Parts", s: "7 lessons · project", p: 20, st: "active" },
    { n: "Sequences & Series", s: "11 lessons · exam", p: 0, st: "locked" },
    { n: "Differential Equations", s: "13 lessons · exam", p: 0, st: "locked" }
  ];

  var lessonsData = [
    { n: "Integration by Parts", d: "Today · 14:10", tag: "In progress", dur: "18 min", ok: false, score: "\u2014" },
    { n: "Substitution Deep Dive", d: "Yesterday · 16:30", tag: "Completed", dur: "26 min", ok: true, score: "92" },
    { n: "Trig Integrals", d: "Oct 8 · 15:05", tag: "Completed", dur: "24 min", ok: true, score: "88" },
    { n: "Definite Integrals", d: "Oct 7 · 14:40", tag: "Completed", dur: "22 min", ok: true, score: "95" },
    { n: "Area Under Curves", d: "Oct 6 · 13:20", tag: "Completed", dur: "30 min", ok: true, score: "81" }
  ];

  var worksheetsData = [
    { n: "Integration by Parts — Set 4", s: "PDF · 12 problems", i: "#i-file" },
    { n: "Mixed Practice — Weekly", s: "PDF · 20 problems", i: "#i-file" },
    { n: "Formula sheet — Calculus", s: "PDF · 2 pages", i: "#i-book" }
  ];

  function renderSubjectPage(subjectId) {
    var d = subjects.filter(function (s) { return s.id === subjectId; })[0] || subjects[0];
    currentSubjectId = d.id;
    SUBJECT.emoji = d.icon;

    var heading = document.querySelector("#view-subject .sub-id h1");
    var eyebrow = document.querySelector("#view-subject .sub-id .eyebrow");
    var meta = document.querySelector("#view-subject .sub-id .meta");
    var emoji = document.getElementById("subEmoji");
    var ring = document.querySelector("#view-subject .ring .fill");
    var ringLabel = document.querySelector("#view-subject .ring-wrap [data-count]");

    if (heading) heading.textContent = d.name;
    if (eyebrow) eyebrow.textContent = "Subject · " + d.name;
    if (emoji) emoji.textContent = d.icon;
    if (meta) {
      meta.innerHTML = '<span class="chip teacher-chip"><span class="teacher-ico sm" aria-hidden="true">' + icon("brain") + '</span>Teacher · ' + d.teacher + '</span><span class="chip">' + icon("book") + d.description + '</span><span class="chip">' + icon("timer") + 'Next session · ' + d.nextSession + '</span>';
    }
    if (ring) ring.setAttribute("data-p", d.progress);
    if (ringLabel) {
      ringLabel.setAttribute("data-count", d.progress);
      ringLabel.dataset.done = "";
      ringLabel.textContent = "0";
    }

    renderSubject();
  }

  function renderSubject() {
    var es = document.getElementById("subEmoji");
    if (es) es.textContent = SUBJECT.emoji;

    var st = document.getElementById("subStats");
    if (st) {
      st.innerHTML = subStatsData.map(function (m) {
        return '<article class="card mini-stat reveal"><div class="l"><svg class="' + m.tone + '"><use href="' + m.i + '"/></svg>' + m.l + '</div><div class="v"><span data-count="' + m.v + '">0</span><small>' + m.u + '</small></div></article>';
      }).join("");
    }

    var rm = document.getElementById("roadmap");
    if (rm) {
      rm.innerHTML = roadmapData.map(function (c, i) {
        var right = c.st === "locked"
          ? '<span class="tag"><svg style="width:12px;height:12px"><use href="#i-lock"/></svg>Locked</span>'
          : (c.st === "done"
            ? '<span class="tag ok"><svg style="width:12px;height:12px"><use href="#i-check"/></svg>Done</span>'
            : '<button class="btn btn-soft btn-sm" data-goview="transition">Resume<svg><use href="#i-arrow"/></svg></button>');
        return '<article class="card chapter ' + c.st + ' reveal" style="--i:' + i + '">' +
          '<span class="no">' + (c.st === "done" ? '<svg><use href="#i-check"/></svg>' : (i + 1)) + '</span>' +
          '<div><h4>' + c.n + '</h4><p class="cs">' + c.s + '</p>' +
          '<div class="bar cp"><i data-w="' + c.p + '"></i></div></div>' +
          '<div class="right">' + right + '</div></article>';
      }).join("");
    }

    var lh = document.getElementById("lessonHistory");
    if (lh) {
      lh.innerHTML = lessonsData.map(function (l) {
        return '<div class="lesson-row"><div class="ln"><b>' + l.n + '</b><span>' + l.d + '</span></div>' +
          '<span class="dur">' + l.dur + '</span>' +
          '<span class="score">' + (l.score === "\u2014" ? "\u2014" : l.score + "%") + '</span>' +
          '<span class="st' + (l.ok ? " ok" : "") + '">' + l.tag + '</span></div>';
      }).join("");
    }

    var wk = document.getElementById("worksheets");
    if (wk) {
      wk.innerHTML = worksheetsData.map(function (w) {
        return '<div class="ws-item"><span class="fi"><svg><use href="' + w.i + '"/></svg></span>' +
          '<div class="fm"><b>' + w.n + '</b><span>' + w.s + '</span></div>' +
          '<button class="dl" aria-label="Download ' + w.n + '"><svg><use href="#i-download"/></svg></button></div>';
      }).join("");
    }

    if (window.activateNumbers) window.activateNumbers(document);
    if (window.activateBars) window.activateBars(document);
    if (window.activateRings) window.activateRings(document);
  }

  // Expose for home.js
  window.renderDashboard = renderDashboard;
  window.renderSubjectPage = renderSubjectPage;
  window.filterSubjects = filterSubjects;
})();
