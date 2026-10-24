/**
 * AI School OS - Shell & Router (home.js)
 * Application entry-point logic: client-side view navigation, the app chrome
 * (sidebar drawer, collapse, companion, search, keyboard shortcuts), and the
 * generic module renderer.
 *
 * Navigation behavior is intentionally unchanged from the single-file version:
 * clicking [data-view] / [data-goview] switches views without changing the URL.
 *
 * dashboard.html and classroom.html are fetched as partials and injected into
 * #viewContainer so index.html stays the navigation shell.
 */

(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var currentView = "dashboard";
  var currentSubjectId = "mathematics";

  var namedViews = {
    dashboard: 1, subjects: 1, system: 1, progress: 1,
    subject: 1, transition: 1, classroom: 1, workspace: 1
  };
  var inlineViews = {
    subjects: 1, system: 1, progress: 1, subject: 1, transition: 1, workspace: 1
  };

  var icon = window.icon;
  var escapeHtml = window.escapeHtml;

  // ------------------------------------------------------------------
  // View navigation
  // ------------------------------------------------------------------

  function showView(name, subjectId) {
    if (subjectId) { currentSubjectId = subjectId; }

    // Partials are fetched from their own HTML files.
    if (name === "dashboard" || name === "classroom") {
      currentView = name;
      updateActiveNav(name);
      closeDrawer();
      window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
      loadPartial(name);
      return;
    }

    // Inline views live in index.html.
    document.querySelectorAll(".view").forEach(function (v) {
      v.classList.remove("active");
    });

    var target = namedViews[name] ? name : "generic";
    var el = document.getElementById("view-" + target);
    if (el) {
      el.classList.add("active");
    }

    if (target === "generic") {
      if (window.renderModule) { window.renderModule(name); }
    }
    if (name === "subject") {
      if (window.renderSubjectPage) { window.renderSubjectPage(currentSubjectId); }
    }

    updateActiveNav(name);

    currentView = name;

    if (name === "transition") { runTransition(); } else { clearTransition(); }
    if (name === "classroom") { startClassroom(); } else { stopClassroom(); }
    if (name === "workspace") { initWorkspace(); }

    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });

    animateView(el);

    if (el) {
      var mainContent = document.getElementById("mainContent");
      if (mainContent) { mainContent.focus({ preventScroll: true }); }
    }

    closeDrawer();
  }

  function loadPartial(name) {
    var file = name + ".html";
    fetch(file)
      .then(function (resp) { return resp.text(); })
      .then(function (html) {
        var container = document.getElementById("viewContainer");
        container.innerHTML = html;
        var el = container.querySelector(".view");
        if (el) { el.classList.add("active"); }

        updateActiveNav(name);

        if (name === "dashboard") {
          clearTransition();
          stopClassroom();
          if (window.renderDashboard) { window.renderDashboard(); }
          animateView(el);
        }
        if (name === "classroom") {
          clearTransition();
          if (window.initClassroom) { window.initClassroom(); }
          animateView(el);
        }

        window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });

        var mainContent = document.getElementById("mainContent");
        if (mainContent) { mainContent.focus({ preventScroll: true }); }

        closeDrawer();
      })
      .catch(function (err) {
        console.error("Failed to load view partial '" + name + "':", err);
      });
  }

  // ------------------------------------------------------------------
  // Generic module renderer (Phase 2 placeholder modules)
  // ------------------------------------------------------------------

  function moduleHead(title, sub, action) {
    return '<header class="module-head"><div><h1>' + title + '</h1><p>' + sub + '</p></div>' + (action || '') + '</header>';
  }

  function resourceRow(iconName, title, meta, tag, action) {
    return '<div class="resource-row"><span class="resource-ico">' + window.icon(iconName) + '</span><div class="resource-copy"><b>' + title + '</b><span>' + meta + '</span></div>' + (tag ? '<span class="tag">' + tag + '</span>' : '') + (action || '') + '</div>';
  }

  window.renderModule = function (name) {
    var root = document.getElementById("moduleRoot");
    if (!root) return;
    var html = "";

    if (name === "teachers") {
      var teachers = [
        ["Dr. Ada", "Mathematics · AI mentor", "Adaptive calculus sessions", "AA"],
        ["Prof. Turing", "Programming · AI mentor", "Algorithms studio", "AT"],
        ["Dr. Curie", "Chemistry · Human teacher", "Office hour · Wed 15:30", "MC"]
      ];
      html = moduleHead("Teachers", "Your subject mentors, availability, and active learning plans.", '<button class="btn btn-primary btn-sm" data-module-action="book">Book a session' + window.icon("calendar") + '</button>') +
        '<div class="module-grid">' +
        teachers.map(function (t) {
          return '<article class="card teacher-card"><div class="person"><span class="avatar">' + t[3] + '</span><div class="info"><b>' + t[0] + '</b><span>' + t[1] + '</span></div><span class="tag ok">Available</span></div><p>' + t[2] + '</p><div class="teacher-meta"><span class="tag color">Next: Today</span><span class="tag">4.9 rating</span></div><button class="btn btn-ghost btn-sm" data-module-action="teacher">View teaching plan</button></article>';
        }).join("") +
        '</div><section class="section"><div class="section-head"><div><h2>Upcoming support</h2><p>Short, focused sessions selected for your current lesson.</p></div></div><article class="card module-card">' +
        resourceRow("calendar", "Calculus clinic", "Today · 16:30 · 25 min", "Dr. Ada", '<button class="btn btn-soft btn-sm" data-module-action="join">Join</button>') +
        resourceRow("video", "Algorithm review", "Tomorrow · 18:00 · 30 min", "Prof. Turing", '<button class="btn btn-ghost btn-sm" data-module-action="book">Reserve</button>') +
        '</article></section>';
    } else if (name === "homework") {
      html = moduleHead("Homework", "Keep track of what is due, submitted, and ready to review.", '<button class="btn btn-soft btn-sm" data-module-action="filter">Due this week</button>') +
        '<div class="module-grid sidebar"><article class="card module-card"><h3>Assigned work</h3>' +
        [
          ["Integration by Parts — Set 4", "Mathematics · due today at 20:00", "Due today", false],
          ["Wave motion reflection", "Physics · due tomorrow", "Tomorrow", false],
          ["Binary search walkthrough", "Programming · submitted", "Submitted", true],
          ["Molecular bonds map", "Chemistry · due Friday", "Friday", false]
        ].map(function (t) {
          return '<label class="task-row"><input class="task-check" type="checkbox" ' + (t[3] ? "checked" : "") + ' aria-label="Mark ' + t[0] + ' complete"><span class="task-copy"><b>' + t[0] + '</b><span>' + t[1] + '</span></span><span class="tag ' + (t[2] === "Due today" ? "warn" : "") + '">' + t[2] + '</span></label>';
        }).join("") +
        '</article><aside class="card module-card"><h3>Submission checklist</h3><p>Finish the remaining three calculations, then attach your working for feedback.</p><div class="bar"><i data-w="63"></i></div><span class="hint">5 of 8 problems complete</span><button class="btn btn-primary btn-block" data-module-action="submit">Submit Set 4</button><button class="btn btn-ghost btn-block" data-goview="library">Open supporting resources</button></aside></div>';
    } else if (name === "calendar") {
      var dates = Array.from({ length: 31 }, function (_, i) { return i + 1; });
      html = moduleHead("Calendar", "October 2026 · lessons, deadlines, and review blocks in one place.", '<div class="filter-bar"><button class="btn btn-ghost btn-sm" data-module-action="previous">Previous</button><button class="btn btn-ghost btn-sm" data-module-action="next">Next</button></div>') +
        '<article class="card module-card"><div class="calendar-grid">' +
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(function (d) { return '<span class="dow">' + d + '</span>'; }).join("") +
        dates.map(function (d) {
          var event = d === 10 ? '<span class="event">Calculus · 16:30</span>' : d === 11 ? '<span class="event due">Set 4 due</span>' : d === 14 ? '<span class="event">Physics lab</span>' : d === 18 ? '<span class="event due">Checkpoint</span>' : "";
          return '<div class="calendar-day ' + (d === 10 ? "today" : "") + '"><b>' + d + '</b>' + event + '</div>';
        }).join("") +
        '</div></article><section class="section"><div class="section-head"><div><h2>Coming up</h2><p>Events selected from your active tracks.</p></div></div><div class="module-grid two"><article class="card module-card">' +
        resourceRow("board", "Live classroom", "Today · 16:30 · Integration by Parts", "Live", '<button class="btn btn-soft btn-sm" data-goview="classroom">Open</button>') +
        '</article><article class="card module-card">' +
        resourceRow("homework", "Set 4 deadline", "Today · 20:00 · Mathematics", "Due", '<button class="btn btn-ghost btn-sm" data-goview="homework">Review</button>') +
        '</article></div></section>';
    } else if (name === "library") {
      html = moduleHead("Library", "A working collection of lessons, books, worksheets, and saved resources.", '<button class="btn btn-primary btn-sm" data-module-action="library-search">Search library' + window.icon("search") + '</button>') +
        '<div class="library-hero"><article class="card continue-card"><span class="resource-ico">' + window.icon("play") + '</span><div><p class="eyebrow grad">Continue learning</p><h2 style="margin-top:7px">Integration by Parts</h2><p style="margin-top:6px">Resume the worked example, then open Set 4 when you are ready.</p></div><div class="bar"><i data-w="62"></i></div><div><button class="btn btn-soft btn-sm" data-goview="classroom">Resume lesson</button></div></article><article class="card module-card"><h3>Collections</h3><div class="tag-row"><button class="filter-btn" data-library-filter="all" aria-pressed="true">All</button><button class="filter-btn" data-library-filter="books" aria-pressed="false">Books</button><button class="filter-btn" data-library-filter="lessons" aria-pressed="false">Lessons</button><button class="filter-btn" data-library-filter="saved" aria-pressed="false">Bookmarks</button></div><p>Filter your library without losing your place.</p></article></div><section class="section"><div class="section-head"><div><h2>For your current lesson</h2><p>Relevant resources are grouped by learning context.</p></div></div><article class="card module-card" id="libraryList">' +
        resourceRow("file", "Integration by Parts — Set 4", "Worksheet · 12 problems · 18 min", "Worksheet", '<button class="btn btn-ghost btn-sm" data-module-action="open-resource">Open</button>') +
        resourceRow("book", "Calculus formula notebook", "Reference · 34 pages · Bookmarked", "Book", '<button class="btn btn-ghost btn-sm" data-module-action="bookmark">Saved</button>') +
        resourceRow("video", "Choosing u and dv", "Lesson clip · 8 min", "Lesson", '<button class="btn btn-ghost btn-sm" data-goview="classroom">Watch</button>') +
        resourceRow("research", "Patterns in repeated integration", "Research paper · 12 pages", "Research", '<button class="btn btn-ghost btn-sm" data-module-action="open-resource">Open</button>') +
        '</article></section>';
    } else if (name === "notifications") {
      html = moduleHead("Notifications", "Updates that need your attention, grouped by recency.", '<button class="btn btn-ghost btn-sm" data-module-action="read-all">Mark all read</button>') +
        '<article class="card module-card" id="noticeList"><p class="eyebrow">Today</p>' +
        [
          ["board", "Your Mathematics lesson starts in 30 minutes", "Integration by Parts · 16:30", true],
          ["homework", "Set 4 is due today", "You have 3 problems left · due 20:00", true],
          ["spark", "A practice hint is ready", "The AI tutor noticed a repeated error pattern.", true],
          ["check", "Checkpoint feedback arrived", "You scored 92% on Substitution Deep Dive.", false],
          ["book", "A saved resource was updated", "Calculus formula notebook · new examples added", false]
        ].map(function (n) {
          return '<div class="notice-row ' + (n[3] ? "unread" : "") + '"><span class="notice-ico">' + window.icon(n[0]) + '</span><div class="notice-copy"><b>' + n[1] + '</b><span>' + n[2] + '</span></div>' + (n[3] ? '<span class="tag color">New</span>' : "") + '</div>';
        }).join("") +
        '</article>';
    } else if (name === "settings") {
      html = moduleHead("Settings", "Adjust the learning environment without interrupting your study flow.") +
        '<div class="module-grid sidebar"><article class="card module-card"><h3>Experience</h3><div class="settings-list">' +
        [
          ["Focus mode", "Hide secondary panels in the live classroom.", "focus"],
          ["Lesson reminders", "Receive a reminder before scheduled sessions.", "reminders"],
          ["Captions by default", "Start live lessons with captions enabled.", "captions"]
        ].map(function (s) {
          return '<div class="setting-row"><div class="copy"><b>' + s[0] + '</b><span>' + s[1] + '</span></div><button class="switch" data-setting="' + s[2] + '" aria-pressed="' + (s[2] === "captions" ? "true" : "false") + '"><i></i><span class="sr-only">Toggle ' + s[0] + '</span></button></div>';
        }).join("") +
        '</div></article><article class="card module-card"><h3>Accessibility</h3><div class="settings-list"><div class="setting-row"><div class="copy"><b>Reduced motion</b><span>System preference is respected across the app.</span></div><span class="tag ok">System</span></div><div class="setting-row"><div class="copy"><b>Keyboard navigation</b><span>Visible focus rings and skip navigation are enabled.</span></div><span class="tag ok">Enabled</span></div><div class="setting-row"><div class="copy"><b>Text size</b><span>Use your browser controls to scale text.</span></div><button class="btn btn-ghost btn-sm" data-module-action="text-size">Preview</button></div></div></article></div><section class="section"><article class="card module-card"><h3>Account</h3><p>Your learning profile is stored locally for this front-end prototype.</p><div class="row-8"><button class="btn btn-ghost btn-sm" data-goview="profile">View profile</button><button class="btn btn-ghost btn-sm" data-module-action="export-data">Export local notes</button></div></article></section>';
    } else if (name === "labs" || name === "research") {
      var isLabs = name === "labs";
      html = moduleHead(isLabs ? "Virtual Labs" : "Research", isLabs ? "Interactive science activities connected to your active subjects." : "Guided inquiry cards and source-based study prompts.") +
        '<div class="module-grid two"><article class="card module-card"><span class="resource-ico">' + window.icon(isLabs ? "atom" : "research") + '</span><h3>' + (isLabs ? "Wave simulator" : "Integration patterns") + '</h3><p>' + (isLabs ? "Explore amplitude and observe how motion changes before your Physics session." : "Compare repeated integration strategies and save evidence to your lesson notes.") + '</p><button class="btn btn-soft btn-sm" data-goview="workspace">Open workspace</button></article><article class="card module-card"><span class="resource-ico">' + window.icon("book") + '</span><h3>' + (isLabs ? "Lab notebook" : "Source collection") + '</h3><p>Save observations, review prompts, and related library resources in one place.</p><button class="btn btn-ghost btn-sm" data-goview="library">Browse resources</button></article></div>';
    } else if (name === "search") {
      var globalSearch = document.getElementById("globalSearch");
      var q = (globalSearch || {}).value || "";
      // Local subject list kept in dashboard.js; expose a tiny search here too.
      var subjects = (window.__subjects || []);
      var matches = subjects.filter(function (s) {
        return !q || (s.n + " " + s.s + " " + s.teacher).toLowerCase().indexOf(q.toLowerCase()) !== -1;
      }).slice(0, 6);
      html = moduleHead("Search", q ? 'Results for “' + escapeHtml(q) + '”' : "Search subjects, lessons, teachers, and resources.") +
        '<div class="search-results">' +
        (matches.length ? matches.map(function (s) {
          return '<button class="search-result" data-goview="subject" data-subject="' + s.id + '">' + window.icon("search") + '<span class="task-copy"><b>' + s.n + '</b><span>' + s.s + ' · ' + s.teacher + '</span></span><span class="tag">Subject</span></button>';
        }).join("") : '<article class="card module-card"><h3>No matching resources yet</h3><p>Try a subject, lesson topic, teacher name, or resource type.</p></article>') +
        '</div>';
    } else if (name === "profile") {
      html = moduleHead("Profile", "Your learning identity, achievements, and study rhythm.", '<button class="btn btn-ghost btn-sm" data-goview="settings">Edit preferences</button>') +
        '<article class="card profile-hero"><span class="profile-avatar">AR</span><div class="hero-text"><h1>Alex Rivera</h1><p>Cohort Turing · Semester 2 · Learning since September 2026</p><div class="tag-row" style="margin-top:12px"><span class="tag color">Level 18</span><span class="tag ok">24 day streak</span></div></div></article><section class="section"><div class="module-grid"><article class="card module-card"><p class="eyebrow">Learning time</p><h2>42h 18m</h2><p>Focused study this semester.</p></article><article class="card module-card"><p class="eyebrow">Mastery</p><h2>84%</h2><p>Across 10 active subject tracks.</p></article><article class="card module-card"><p class="eyebrow">XP earned</p><h2>18,420</h2><p>2,180 XP to the next level.</p></article></div></section><section class="section"><div class="module-grid sidebar"><article class="card module-card"><h3>Recent achievements</h3><div class="achievement"><span class="badge-orb">' + window.icon("target") + '</span><div class="achievement-text"><b>Precision learner</b><p>Five checkpoint scores above 90%.</p></div></div><div class="achievement"><span class="badge-orb">' + window.icon("flame") + '</span><div class="achievement-text"><b>Three-week rhythm</b><p>Studied on 24 consecutive days.</p></div></div><div class="achievement"><span class="badge-orb">' + window.icon("book") + '</span><div class="achievement-text"><b>Deep reader</b><p>Finished six supporting resources.</p></div></div></article><aside class="card module-card"><h3>Learning goal</h3><p>Complete the Integration Techniques roadmap by October 24.</p><div class="bar"><i data-w="62"></i></div><span class="hint">62% complete</span><button class="btn btn-soft btn-sm" data-goview="subject">View roadmap</button></aside></div></section>';
    }

    root.innerHTML = html;
  };

  // ------------------------------------------------------------------
  // Navigation active states
  // ------------------------------------------------------------------

  function updateActiveNav(activeName) {
    var aliasMap = { subject: "subjects" };
    var targetName = aliasMap[activeName] || activeName;

    document.querySelectorAll("[data-view]").forEach(function (btn) {
      var view = btn.getAttribute("data-view");
      if (view === targetName || (aliasMap[view] === targetName)) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });

    document.querySelectorAll(".sidebar [data-view]").forEach(function (btn) {
      var view = btn.getAttribute("data-view");
      if (view === targetName || (aliasMap[view] === targetName)) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });

    document.querySelectorAll(".bottom-nav [data-view]").forEach(function (btn) {
      var view = btn.getAttribute("data-view");
      if (view === targetName) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });
  }

  // ------------------------------------------------------------------
  // View animations
  // ------------------------------------------------------------------

  function animateView(scope) {
    if (!scope) return;
    scope.querySelectorAll(".reveal").forEach(function (el) {
      el.style.animation = "none";
      void el.offsetWidth;
      el.style.animation = "";
    });
    activateNumbers(scope);
    activateBars(scope);
    activateRings(scope);
  }

  function activateBars(scope) {
    (scope || document).querySelectorAll(".bar > i[data-w]").forEach(function (i) {
      var w = i.getAttribute("data-w");
      i.style.width = "0%";
      requestAnimationFrame(function () { setTimeout(function () { i.style.width = w + "%"; }, 60); });
    });
    (scope || document).querySelectorAll(".mini-bar > i[data-w]").forEach(function (i) {
      var w = i.getAttribute("data-w");
      i.style.width = "0%";
      requestAnimationFrame(function () { setTimeout(function () { i.style.width = w + "%"; }, 60); });
    });
  }

  function activateRings(scope) {
    (scope || document).querySelectorAll(".ring .fill[data-p]").forEach(function (c) {
      var p = parseFloat(c.getAttribute("data-p")) || 0;
      var dash = 106.81;
      c.style.strokeDashoffset = dash;
      requestAnimationFrame(function () { setTimeout(function () { c.style.strokeDashoffset = (dash - dash * p / 100).toFixed(2); }, 120); });
    });
  }

  function activateNumbers(scope) {
    (scope || document).querySelectorAll("[data-count]").forEach(function (el) {
      if (el.dataset.done === "1") return;
      el.dataset.done = "1";
      var target = parseFloat(el.getAttribute("data-count")) || 0;
      if (reduce) { el.textContent = target.toLocaleString(); return; }
      var start = null, dur = 1100;
      function step(ts) {
        if (!start) start = ts;
        var t = Math.min((ts - start) / dur, 1);
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(target * eased).toLocaleString();
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  // ------------------------------------------------------------------
  // Sidebar drawer
  // ------------------------------------------------------------------

  function openDrawer() {
    var sidebar = document.getElementById("sidebar");
    var backdrop = document.getElementById("backdrop");
    var menuBtn = document.getElementById("menuBtn");
    if (sidebar) sidebar.classList.add("open");
    if (backdrop) { backdrop.hidden = false; }
    requestAnimationFrame(function () {
      var backdrop = document.getElementById("backdrop");
      if (backdrop) backdrop.classList.add("show");
    });
    if (menuBtn) menuBtn.setAttribute("aria-expanded", "true");
  }

  function closeDrawer() {
    var sidebar = document.getElementById("sidebar");
    var backdrop = document.getElementById("backdrop");
    var menuBtn = document.getElementById("menuBtn");
    if (sidebar && sidebar.classList.contains("open")) {
      sidebar.classList.remove("open");
      if (backdrop) backdrop.classList.remove("show");
      if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
      setTimeout(function () { var backdrop = document.getElementById("backdrop"); if (backdrop) backdrop.hidden = true; }, 240);
    }
  }

  // ------------------------------------------------------------------
  // Desktop sidebar collapse
  // ------------------------------------------------------------------

  var collapsed = false;
  function toggleCollapse() {
    collapsed = !collapsed;
    document.documentElement.style.setProperty("--sidebar-w", collapsed ? "84px" : "264px");
    var sidebar = document.getElementById("sidebar");
    if (sidebar) {
      sidebar.querySelectorAll(".nav-item .txt, .brand .id, .nav-label").forEach(function (el) {
        el.style.display = collapsed ? "none" : "";
      });
    }
    var collapseBtn = document.getElementById("collapseBtn");
    if (collapseBtn) {
      var lbl = collapseBtn.querySelector(".lbl");
      if (lbl) lbl.style.display = collapsed ? "none" : "";
    }
  }

  // ------------------------------------------------------------------
  // AI companion
  // ------------------------------------------------------------------

  function initCompanion() {
    var companion = document.getElementById("companion");
    var cc = document.getElementById("companionClose");
    var wasDismissed = false;
    try { wasDismissed = localStorage.getItem("companion-dismissed") === "1"; } catch (err) {}
    if (wasDismissed && companion) {
      companion.classList.add("dismissed");
    }
    if (cc && companion) {
      cc.addEventListener("click", function () {
        companion.classList.add("hide");
        companion.addEventListener("transitionend", function onEnd() {
          companion.classList.remove("hide");
          companion.classList.add("dismissed");
          companion.removeEventListener("transitionend", onEnd);
        });
        try { localStorage.setItem("companion-dismissed", "1"); } catch (err) {}
      });
    }
  }

  // ------------------------------------------------------------------
  // Particles background
  // ------------------------------------------------------------------

  function particles() {
    if (reduce) return;
    var cv = document.getElementById("particles");
    if (!cv) return;
    var ctx = cv.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w, h, parts = [], particleFrame = null, paused = document.hidden;

    function size() {
      w = cv.width = innerWidth * dpr;
      h = cv.height = innerHeight * dpr;
      cv.style.width = innerWidth + "px";
      cv.style.height = innerHeight + "px";
      var count = Math.min(64, Math.round(innerWidth / 26));
      parts = [];
      for (var i = 0; i < count; i++) {
        parts.push({
          x: Math.random() * w, y: Math.random() * h,
          r: (Math.random() * 1.6 + 0.5) * dpr,
          vx: (Math.random() - 0.5) * 0.12 * dpr,
          vy: -(Math.random() * 0.18 + 0.05) * dpr,
          a: Math.random() * 0.35 + 0.08,
          hue: Math.random() > 0.5 ? "79,124,255" : "34,211,238"
        });
      }
    }
    size();
    addEventListener("resize", size);
    function frame() {
      if (paused) return;
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        if (p.x < -10) p.x = w + 10; if (p.x > w + 10) p.x = -10;
        ctx.beginPath();
        ctx.fillStyle = "rgba(" + p.hue + "," + p.a + ")";
        ctx.arc(p.x, p.y, p.r, 0, 6.283);
        ctx.fill();
      }
      particleFrame = requestAnimationFrame(frame);
    }
    document.addEventListener("visibilitychange", function () {
      paused = document.hidden;
      if (!paused && !particleFrame) { particleFrame = requestAnimationFrame(frame); }
      if (paused) { particleFrame = null; }
    });
    particleFrame = requestAnimationFrame(frame);
  }

  // ------------------------------------------------------------------
  // Global click handler (navigation + chrome actions)
  // ------------------------------------------------------------------

  function notify(message) {
    var region = document.getElementById("toastRegion");
    if (!region) return;
    var toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    region.appendChild(toast);
    setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 4200);
  }

  document.addEventListener("click", function (e) {
    var trigger = e.target.closest("[data-view],[data-goview]");
    if (!trigger) return;
    var v = trigger.getAttribute("data-view") || trigger.getAttribute("data-goview");
    var subjectId = trigger.getAttribute("data-subject");
    if (v) {
      e.preventDefault();
      showView(v, subjectId);
      return;
    }

    var subjectFilter = e.target.closest("[data-subject-filter]");
    if (subjectFilter) {
      if (window.filterSubjects) { window.filterSubjects(subjectFilter.getAttribute("data-subject-filter")); }
      return;
    }

    var libraryFilter = e.target.closest("[data-library-filter]");
    if (libraryFilter) {
      document.querySelectorAll("[data-library-filter]").forEach(function (b) {
        b.setAttribute("aria-pressed", b === libraryFilter ? "true" : "false");
      });
      notify("Library filtered to " + libraryFilter.textContent.toLowerCase() + ".");
      return;
    }

    var setting = e.target.closest("[data-setting]");
    if (setting) {
      var enabled = setting.getAttribute("aria-pressed") !== "true";
      setting.setAttribute("aria-pressed", enabled ? "true" : "false");
      try { localStorage.setItem("ai-school-os:setting:" + setting.getAttribute("data-setting"), enabled ? "1" : "0"); } catch (err) {}
      return;
    }

    var action = e.target.closest("[data-module-action]");
    if (!action) return;
    var type = action.getAttribute("data-module-action");
    if (type === "read-all") {
      document.querySelectorAll(".notice-row.unread").forEach(function (row) {
        row.classList.remove("unread");
      });
      action.textContent = "All caught up";
    } else if (type === "submit") {
      action.textContent = "Submitted";
      action.disabled = true;
      notify("Set 4 submitted for feedback.");
    } else if (type === "bookmark") {
      action.textContent = "Saved";
      notify("Resource saved to Bookmarks.");
    } else if (type === "open-resource" || type === "library-search") {
      notify("Resource opened in the learning workspace.");
      showView("workspace");
    } else if (type === "export-data") {
      notify("Save notes from the live classroom to export them.");
    } else if (type === "text-size") {
      notify("Use your browser zoom controls to preview a larger text size.");
    } else {
      notify("This action is ready for your next study session.");
    }
  });

  // ------------------------------------------------------------------
  // Global search + keyboard shortcuts
  // ------------------------------------------------------------------

  var globalSearch = document.getElementById("globalSearch");
  if (globalSearch) {
    globalSearch.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { showView("search"); }
    });
    globalSearch.addEventListener("input", function () {
      if (currentView === "search") {
        window.renderModule("search");
        activateBars(document.getElementById("view-generic"));
      }
    });
  }

  var bellBtn = document.getElementById("bellBtn");
  var profileBtn = document.getElementById("profileBtn");
  if (bellBtn) {
    bellBtn.addEventListener("click", function () { showView("notifications"); });
  }
  if (profileBtn) {
    profileBtn.addEventListener("click", function () { showView("profile"); });
  }

  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (globalSearch) globalSearch.focus();
    }
    if (e.key === "Escape" && currentView === "search") {
      showView("dashboard");
    }
  });

  // ------------------------------------------------------------------
  // Module init
  // ------------------------------------------------------------------

  function initShell() {
    var sidebar = document.getElementById("sidebar");
    var backdrop = document.getElementById("backdrop");
    var menuBtn = document.getElementById("menuBtn");
    var collapseBtn = document.getElementById("collapseBtn");

    if (menuBtn) {
      menuBtn.addEventListener("click", function () {
        if (sidebar && sidebar.classList.contains("open")) { closeDrawer(); } else { openDrawer(); }
      });
    }
    if (backdrop) {
      backdrop.addEventListener("click", closeDrawer);
    }
    if (collapseBtn) {
      collapseBtn.addEventListener("click", toggleCollapse);
    }

    initCompanion();
    particles();

    // Animate all bars/rings/numbers present in the shell at load time.
    activateBars(document);
    activateRings(document);
    activateNumbers(document);

    // Render the entry view (dashboard) into the shell.
    showView("dashboard");
  }

  initShell();

  // Expose for cross-file use (bootstrap + dashboard.js / classroom.js).
  window.showView = showView;
  window.updateActiveNav = updateActiveNav;
  window.activateBars = activateBars;
  window.activateRings = activateRings;
  window.activateNumbers = activateNumbers;

})();
