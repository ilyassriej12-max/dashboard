/**
 * AI School OS - Data Layer (api.js)
 * Centralized state (AppStore), shared helpers, and API client stubs.
 *
 * Phase 3A: the AppStore holds the same client-side data the app already used.
 * Phase 3B: fetchDashboard / postChat are the seams to connect to
 *   /api/dashboard  and  /api/chat  without touching dashboard.js / classroom.js.
 */

(function () {
  "use strict";

  // ============================================================
  // SHARED HELPERS (used by dashboard.js / home.js)
  // ============================================================
  window.escapeHtml = function (value) {
    return String(value || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c];
    });
  };

  window.icon = function (name) {
    return '<svg aria-hidden="true"><use href="#i-' + name + '"/></svg>';
  };

  // ============================================================
  // DEFAULT STATE
  // ============================================================
  var defaultState = {
    // User profile
    user: {
      name: "Alex Rivera",
      avatar: "AR",
      cohort: "Turing",
      semester: 2,
      joinedDate: "2026-09-01",
      level: 18,
      xp: 18420,
      xpToNextLevel: 2180,
      streak: 24,
      totalStudyTime: 42 * 60 + 18, // minutes
      mastery: 84,
      preferences: {
        theme: "dark",
        language: "en",
        animations: true,
        reducedMotion: false,
        captions: true,
        focusMode: false,
        lessonReminders: true
      }
    },

    // Subjects data
    subjects: [
      { id: "mathematics", icon: "\u2211", name: "Mathematics", description: "Calculus · Algebra", progress: 62, color: "var(--primary)", teacher: "Dr. Ada", nextSession: "16:30", lessons: 58, mastery: 84, streak: 12, difficulty: "Advanced", lastLesson: "Integration by Parts · Part 2" },
      { id: "physics", icon: "\u269b", name: "Physics", description: "Mechanics · Waves", progress: 47, color: "var(--primary-soft)", teacher: "Prof. Newton", nextSession: "14:00", lessons: 42, mastery: 71, streak: 8, difficulty: "Intermediate", lastLesson: "Wave Motion" },
      { id: "chemistry", icon: "\u{1F9EA}", name: "Chemistry", description: "Organic · Bonds", progress: 54, color: "var(--secondary)", teacher: "Dr. Curie", nextSession: "10:30", lessons: 36, mastery: 68, streak: 5, difficulty: "Intermediate", lastLesson: "Molecular Bonds" },
      { id: "programming", icon: "\u{1F4BB}", name: "Programming", description: "Algorithms · Python", progress: 78, color: "var(--accent)", teacher: "Prof. Turing", nextSession: "18:00", lessons: 64, mastery: 91, streak: 24, difficulty: "Advanced", lastLesson: "Binary Search" },
      { id: "biology", icon: "\u{1F9EC}", name: "Biology", description: "Genetics · Cells", progress: 41, color: "var(--success)", teacher: "Dr. Darwin", nextSession: "11:00", lessons: 48, mastery: 63, streak: 3, difficulty: "Beginner", lastLesson: "Cell Division" },
      { id: "geography", icon: "\u{1F30D}", name: "Geography", description: "Climate · Mapping", progress: 66, color: "var(--warning)", teacher: "Prof. Humboldt", nextSession: "09:00", lessons: 28, mastery: 79, streak: 7, difficulty: "Intermediate", lastLesson: "Climate Patterns" },
      { id: "literature", icon: "\u{1F4D6}", name: "Literature", description: "Modernism · Poetry", progress: 33, color: "var(--secondary)", teacher: "Prof. Woolf", nextSession: "15:30", lessons: 32, mastery: 57, streak: 2, difficulty: "Beginner", lastLesson: "Modernist Poetry" },
      { id: "english", icon: "\u{1F1EC}\u{1F1E7}", name: "English", description: "Writing · Analysis", progress: 71, color: "var(--primary)", teacher: "Dr. Austen", nextSession: "13:00", lessons: 40, mastery: 82, streak: 14, difficulty: "Advanced", lastLesson: "Essay Writing" },
      { id: "french", icon: "\u{1F1EB}\u{1F1F7}", name: "French", description: "Grammar · Listening", progress: 29, color: "var(--accent)", teacher: "M. Proust", nextSession: "16:00", lessons: 35, mastery: 48, streak: 1, difficulty: "Beginner", lastLesson: "Basic Grammar" },
      { id: "history", icon: "\u{1F4DC}", name: "History", description: "Modern era · Sources", progress: 58, color: "var(--warning)", teacher: "Prof. Braudel", nextSession: "10:00", lessons: 45, mastery: 73, streak: 6, difficulty: "Intermediate", lastLesson: "Modern Era" }
    ],

    // Teachers data
    teachers: [
      { id: "ada", name: "Dr. Ada", specialty: "Mathematics · AI Mentor", status: "Available", description: "Adaptive calculus sessions with real-time difficulty adjustment.", skills: ["Calculus", "Linear Algebra", "Adaptive Learning"], subjects: ["mathematics"], avatar: "AA", rating: 4.9, nextSession: "Today · 16:30" },
      { id: "turing", name: "Prof. Turing", specialty: "Programming · AI Mentor", status: "Available", description: "Algorithms studio with hands-on coding challenges.", skills: ["Algorithms", "Python", "Data Structures"], subjects: ["programming"], avatar: "AT", rating: 4.8, nextSession: "Tomorrow · 18:00" },
      { id: "curie", name: "Dr. Curie", specialty: "Chemistry · Human Teacher", status: "Busy", description: "Office hours available Wednesdays 15:30.", skills: ["Organic Chemistry", "Bonds", "Lab Safety"], subjects: ["chemistry"], avatar: "MC", rating: 4.9, nextSession: "Wed · 15:30" },
      { id: "newton", name: "Prof. Newton", specialty: "Physics · Human Teacher", status: "Available", description: "Mechanics and waves with interactive simulations.", skills: ["Mechanics", "Waves", "Simulations"], subjects: ["physics"], avatar: "PN", rating: 4.7, nextSession: "Today · 14:00" },
      { id: "darwin", name: "Dr. Darwin", specialty: "Biology · Human Teacher", status: "Available", description: "Genetics and cell biology with virtual labs.", skills: ["Genetics", "Cell Biology", "Evolution"], subjects: ["biology"], avatar: "DD", rating: 4.8, nextSession: "Today · 11:00" },
      { id: "humboldt", name: "Prof. Humboldt", specialty: "Geography · Human Teacher", status: "Available", description: "Climate science and mapping with real-world data.", skills: ["Climate", "GIS", "Mapping"], subjects: ["geography"], avatar: "PH", rating: 4.6, nextSession: "Today · 09:00" }
    ],

    // Homework/Assignments
    homework: [
      { id: "hw1", subjectId: "mathematics", subject: "Mathematics", title: "Integration by Parts — Set 4", description: "8 problems covering integration by parts technique", dueDate: "2026-10-10T20:00:00", status: "in-progress", priority: "high", progress: 63, completedProblems: 5, totalProblems: 8, estimatedTime: 18 },
      { id: "hw2", subjectId: "physics", subject: "Physics", title: "Wave Motion Reflection", description: "Reflection essay on wave behavior in different media", dueDate: "2026-10-11T23:59:00", status: "pending", priority: "medium", progress: 0, completedProblems: 0, totalProblems: 1, estimatedTime: 45 },
      { id: "hw3", subjectId: "programming", subject: "Programming", title: "Binary Search Walkthrough", description: "Implement and document binary search algorithm", dueDate: "2026-10-09T18:00:00", status: "completed", priority: "high", progress: 100, completedProblems: 1, totalProblems: 1, estimatedTime: 60 },
      { id: "hw4", subjectId: "chemistry", subject: "Chemistry", title: "Molecular Bonds Map", description: "Create concept map of molecular bond types", dueDate: "2026-10-13T20:00:00", status: "pending", priority: "low", progress: 25, completedProblems: 1, totalProblems: 4, estimatedTime: 30 },
      { id: "hw5", subjectId: "literature", subject: "Literature", title: "Modernist Poetry Analysis", description: "Analyze three modernist poems", dueDate: "2026-10-12T15:00:00", status: "in-progress", priority: "medium", progress: 40, completedProblems: 2, totalProblems: 5, estimatedTime: 40 }
    ],

    // Calendar events
    calendarEvents: [
      { id: "evt1", date: "2026-10-10", title: "Calculus Lesson", type: "lesson", subjectId: "mathematics", time: "16:30", duration: 45 },
      { id: "evt2", date: "2026-10-10", title: "Set 4 Due", type: "deadline", subjectId: "mathematics", time: "20:00" },
      { id: "evt3", date: "2026-10-11", title: "Physics Lab", type: "lesson", subjectId: "physics", time: "14:00", duration: 60 },
      { id: "evt4", date: "2026-10-12", title: "Literature Discussion", type: "lesson", subjectId: "literature", time: "15:30", duration: 45 },
      { id: "evt5", date: "2026-10-13", title: "Chemistry Lab", type: "lesson", subjectId: "chemistry", time: "10:30", duration: 90 },
      { id: "evt6", date: "2026-10-14", title: "Programming Workshop", type: "lesson", subjectId: "programming", time: "18:00", duration: 120 },
      { id: "evt7", date: "2026-10-15", title: "Checkpoint Quiz", type: "deadline", subjectId: "mathematics", time: "16:30" },
      { id: "evt8", date: "2026-10-16", title: "Biology Review", type: "lesson", subjectId: "biology", time: "11:00", duration: 60 },
      { id: "evt9", date: "2026-10-17", title: "Geography Mapping", type: "lesson", subjectId: "geography", time: "09:00", duration: 45 },
      { id: "evt10", date: "2026-10-18", title: "Midterm Checkpoint", type: "deadline", subjectId: "mathematics", time: "16:30" }
    ],

    // Library resources
    library: [
      { id: "lib1", type: "worksheet", title: "Integration by Parts — Set 4", description: "Worksheet · 12 problems · 18 min", subjectId: "mathematics", icon: "file", pages: 3, favorite: false, tags: ["calculus", "integration", "practice"] },
      { id: "lib2", type: "book", title: "Calculus Formula Notebook", description: "Reference · 34 pages · Bookmarked", subjectId: "mathematics", icon: "book", pages: 34, favorite: true, tags: ["calculus", "formulas", "reference"] },
      { id: "lib3", type: "video", title: "Choosing u and dv", description: "Lesson clip · 8 min", subjectId: "mathematics", icon: "video", duration: "8 min", favorite: false, tags: ["calculus", "technique", "video"] },
      { id: "lib4", type: "research", title: "Patterns in Repeated Integration", description: "Research paper · 12 pages", subjectId: "mathematics", icon: "research", pages: 12, favorite: true, tags: ["calculus", "research", "advanced"] },
      { id: "lib5", type: "worksheet", title: "Mixed Practice — Weekly", description: "Worksheet · 20 problems · 25 min", subjectId: "mathematics", icon: "file", pages: 5, favorite: false, tags: ["calculus", "mixed", "practice"] },
      { id: "lib6", type: "book", title: "Wave Mechanics Fundamentals", description: "Textbook · 156 pages", subjectId: "physics", icon: "book", pages: 156, favorite: true, tags: ["physics", "waves", "textbook"] },
      { id: "lib7", type: "video", title: "Standing Waves Explained", description: "Lesson · 15 min", subjectId: "physics", icon: "video", duration: "15 min", favorite: false, tags: ["physics", "waves", "video"] },
      { id: "lib8", type: "worksheet", title: "Binary Search Problems", description: "Worksheet · 10 problems · 30 min", subjectId: "programming", icon: "file", pages: 4, favorite: false, tags: ["algorithms", "search", "practice"] },
      { id: "lib9", type: "book", title: "Algorithm Design Manual", description: "Reference · 420 pages", subjectId: "programming", icon: "book", pages: 420, favorite: true, tags: ["algorithms", "reference", "textbook"] },
      { id: "lib10", type: "video", title: "Dynamic Programming Intro", description: "Lesson · 22 min", subjectId: "programming", icon: "video", duration: "22 min", favorite: false, tags: ["algorithms", "dp", "video"] }
    ],

    // Live Classroom sessions
    liveSessions: [
      { id: "ls1", subjectId: "mathematics", subject: "Mathematics", title: "Integration by Parts", lesson: "Lesson 4 of 9", teacher: "Dr. Ada", time: "16:30", duration: 45, status: "live", cohort: "Turing", joinUrl: "#" },
      { id: "ls2", subjectId: "physics", subject: "Physics", title: "Wave Mechanics", lesson: "Lesson 3 of 8", teacher: "Prof. Newton", time: "14:00", duration: 60, status: "upcoming", cohort: "Turing", joinUrl: "#" },
      { id: "ls3", subjectId: "programming", subject: "Programming", title: "Algorithms Studio", lesson: "Lesson 5 of 12", teacher: "Prof. Turing", time: "18:00", duration: 90, status: "upcoming", cohort: "Turing", joinUrl: "#" },
      { id: "ls4", subjectId: "chemistry", subject: "Chemistry", title: "Organic Reactions", lesson: "Lesson 2 of 6", teacher: "Dr. Curie", time: "10:30", duration: 60, status: "scheduled", cohort: "Turing", joinUrl: "#" },
      { id: "ls5", subjectId: "biology", subject: "Biology", title: "Cell Division Lab", lesson: "Lesson 4 of 10", teacher: "Dr. Darwin", time: "11:00", duration: 60, status: "scheduled", cohort: "Turing", joinUrl: "#" }
    ],

    // Notifications
    notifications: [
      { id: "notif1", type: "board", title: "Your Mathematics lesson starts in 30 minutes", message: "Integration by Parts · 16:30", read: false, timestamp: Date.now() - 30 * 60 * 1000 },
      { id: "notif2", type: "homework", title: "Set 4 is due today", message: "You have 3 problems left · due 20:00", read: false, timestamp: Date.now() - 60 * 60 * 1000 },
      { id: "notif3", type: "spark", title: "A practice hint is ready", message: "The AI tutor noticed a repeated error pattern.", read: false, timestamp: Date.now() - 2 * 60 * 60 * 1000 },
      { id: "notif4", type: "check", title: "Checkpoint feedback arrived", message: "You scored 92% on Substitution Deep Dive.", read: true, timestamp: Date.now() - 24 * 60 * 60 * 1000 },
      { id: "notif5", type: "book", title: "A saved resource was updated", message: "Calculus formula notebook · new examples added", read: true, timestamp: Date.now() - 48 * 60 * 60 * 1000 }
    ],

    // Achievements
    achievements: [
      { id: "ach1", icon: "target", title: "Precision Learner", description: "Five checkpoint scores above 90%.", unlocked: true, unlockedDate: "2026-10-01" },
      { id: "ach2", icon: "flame", title: "Three-Week Rhythm", description: "Studied on 24 consecutive days.", unlocked: true, unlockedDate: "2026-10-05" },
      { id: "ach3", icon: "book", title: "Deep Reader", description: "Finished six supporting resources.", unlocked: true, unlockedDate: "2026-10-08" },
      { id: "ach4", icon: "bolt", title: "Speed Demon", description: "Complete a lesson in under 15 minutes.", unlocked: false },
      { id: "ach5", icon: "star", title: "Perfectionist", description: "Score 100% on three checkpoints.", unlocked: false },
      { id: "ach6", icon: "spark", title: "Early Bird", description: "Complete 10 lessons before 9 AM.", unlocked: false }
    ],

    // Learning goals
    goals: [
      { id: "goal1", title: "Complete Integration Techniques", description: "Finish the Integration Techniques roadmap by October 24.", targetDate: "2026-10-24", progress: 62, subjectId: "mathematics" },
      { id: "goal2", title: "Reach Level 20", description: "Earn enough XP to reach level 20.", targetDate: "2026-11-01", progress: 45, subjectId: null },
      { id: "goal3", title: "30-Day Streak", description: "Maintain a 30-day learning streak.", targetDate: "2026-11-10", progress: 80, subjectId: null }
    ],

    // Dashboard stats
    dashboard: {
      weeklyXP: 4820,
      weeklyTime: 6 * 60 + 42, // minutes
      mastery: 84,
      exercisesCompleted: 128,
      completionRate: 91,
      weeklyGoalProgress: 72, // 5 of 7 days
      currentSubjectId: "mathematics"
    },

    // UI State
    ui: {
      currentView: "dashboard",
      sidebarCollapsed: false,
      mobileMenuOpen: false,
      companionDismissed: false,
      activeFilters: {
        subjects: "all",
        homework: "all",
        library: "all",
        notifications: "all"
      },
      searchQuery: "",
      selectedSubjectId: "mathematics"
    }
  };

  // ============================================================
  // STORE CLASS
  // ============================================================
  var Store = (function () {
    function Store() {
      this.state = this.loadState();
      this.listeners = new Map();
      this.persistenceKeys = [
        "user",
        "homework",
        "library",
        "notifications",
        "achievements",
        "goals",
        "dashboard",
        "ui"
      ];
    }

    Store.prototype.loadState = function () {
      try {
        var saved = localStorage.getItem("ai-school-os:state");
        if (saved) {
          var parsed = JSON.parse(saved);
          return this.mergeDeep(defaultState, parsed);
        }
      } catch (e) {
        console.warn("Failed to load state from localStorage:", e);
      }
      return this.deepCopy(defaultState);
    };

    Store.prototype.deepCopy = function (obj) {
      return JSON.parse(JSON.stringify(obj));
    };

    Store.prototype.mergeDeep = function (target, source) {
      var result = {};
      var key;
      for (key in target) {
        if ({}.hasOwnProperty.call(target, key)) {
          result[key] = target[key];
        }
      }
      for (key in source) {
        if ({}.hasOwnProperty.call(source, key)) {
          if (source[key] && typeof source[key] === "object" && !Array.isArray(source[key])) {
            result[key] = this.mergeDeep(target[key] || {}, source[key]);
          } else {
            result[key] = source[key];
          }
        }
      }
      return result;
    };

    Store.prototype.saveState = function () {
      try {
        var toSave = {};
        for (var i = 0; i < this.persistenceKeys.length; i++) {
          var key = this.persistenceKeys[i];
          toSave[key] = this.state[key];
        }
        localStorage.setItem("ai-school-os:state", JSON.stringify(toSave));
      } catch (e) {
        console.warn("Failed to save state to localStorage:", e);
      }
    };

    Store.prototype.get = function (path) {
      if (!path) return this.state;
      return path.split(".").reduce(function (obj, key) {
        return obj ? obj[key] : undefined;
      }, this.state);
    };

    Store.prototype.set = function (path, value) {
      var keys = path.split(".");
      var lastKey = keys.pop();
      var target = keys.reduce(function (obj, key) {
        if (!obj[key]) obj[key] = {};
        return obj[key];
      }, this.state);

      var oldValue = target[lastKey];
      target[lastKey] = value;

      this.saveState();
      this.notify(path, value, oldValue);
    };

    Store.prototype.update = function (path, partial) {
      var current = this.get(path) || {};
      this.set(path, Object.assign({}, current, partial));
    };

    Store.prototype.push = function (path, item) {
      var arr = this.get(path) || [];
      arr.push(item);
      this.set(path, arr);
    };

    Store.prototype.remove = function (path, predicate) {
      var arr = this.get(path) || [];
      var index = arr.findIndex(predicate);
      if (index !== -1) {
        arr.splice(index, 1);
        this.set(path, arr);
      }
    };

    Store.prototype.find = function (path, predicate) {
      var arr = this.get(path) || [];
      return arr.find(predicate);
    };

    Store.prototype.filter = function (path, predicate) {
      var arr = this.get(path) || [];
      return arr.filter(predicate);
    };

    Store.prototype.subscribe = function (path, callback) {
      if (!this.listeners.has(path)) {
        this.listeners.set(path, new Set());
      }
      this.listeners.get(path).add(callback);
      return function () {
        var set = this.listeners.get(path);
        if (set) set.delete(callback);
      };
    };

    Store.prototype.notify = function (path, newValue, oldValue) {
      var exactListeners = this.listeners.get(path);
      if (exactListeners) {
        exactListeners.forEach(function (cb) { cb(newValue, oldValue, path); });
      }
      var keys = path.split(".");
      for (var i = keys.length - 1; i > 0; i--) {
        var parentPath = keys.slice(0, i).join(".");
        var parentListeners = this.listeners.get(parentPath);
        if (parentListeners) {
          parentListeners.forEach(function (cb) { cb(this.get(parentPath), oldValue, parentPath); });
        }
      }
      var rootListeners = this.listeners.get("*");
      if (rootListeners) {
        rootListeners.forEach(function (cb) { cb(this.state, oldValue, path); });
      }
    };

    Store.prototype.getSubject = function (id) {
      return this.state.subjects.find(function (s) { return s.id === id; });
    };

    Store.prototype.getSubjectsByFilter = function (filter) {
      var subjects = this.state.subjects;
      switch (filter) {
        case "progress": return subjects.filter(function (s) { return s.progress > 0 && s.progress < 100; });
        case "recommended": return subjects.filter(function (s) { return s.mastery < 70; });
        case "completed": return subjects.filter(function (s) { return s.progress >= 75; });
        default: return subjects;
      }
    };

    Store.prototype.getHomeworkByStatus = function (status) {
      if (status === "all") return this.state.homework;
      return this.state.homework.filter(function (h) { return h.status === status; });
    };

    Store.prototype.getUnreadNotificationsCount = function () {
      return this.state.notifications.filter(function (n) { return !n.read; }).length;
    };

    Store.prototype.getUpcomingEvents = function (days) {
      if (days === undefined) days = 7;
      var now = new Date();
      var future = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
      return this.state.calendarEvents
        .filter(function (e) { return new Date(e.date) >= now && new Date(e.date) <= future; })
        .sort(function (a, b) { return new Date(a.date) - new Date(b.date); });
    };

    Store.prototype.getLiveSessions = function () {
      return this.state.liveSessions.filter(function (s) { return s.status === "live" || s.status === "upcoming"; });
    };

    Store.prototype.getLibraryByFilter = function (filter) {
      if (filter === "all") return this.state.library;
      return this.state.library.filter(function (r) { return r.type === filter; });
    };

    Store.prototype.searchLibrary = function (query) {
      var q = query.toLowerCase();
      return this.state.library.filter(function (r) {
        return r.title.toLowerCase().indexOf(q) !== -1 ||
               r.description.toLowerCase().indexOf(q) !== -1 ||
               r.tags.some(function (t) { return t.toLowerCase().indexOf(q) !== -1; });
      });
    };

    Store.prototype.searchGlobal = function (query) {
      var q = query.toLowerCase();
      var results = [];
      this.state.subjects.forEach(function (s) {
        if (s.name.toLowerCase().indexOf(q) !== -1 || s.description.toLowerCase().indexOf(q) !== -1 || s.teacher.toLowerCase().indexOf(q) !== -1) {
          results.push({ type: "subject", data: s });
        }
      });
      this.state.teachers.forEach(function (t) {
        if (t.name.toLowerCase().indexOf(q) !== -1 || t.specialty.toLowerCase().indexOf(q) !== -1 || t.description.toLowerCase().indexOf(q) !== -1) {
          results.push({ type: "teacher", data: t });
        }
      });
      this.state.homework.forEach(function (h) {
        if (h.title.toLowerCase().indexOf(q) !== -1 || h.description.toLowerCase().indexOf(q) !== -1) {
          results.push({ type: "homework", data: h });
        }
      });
      this.state.library.forEach(function (r) {
        if (r.title.toLowerCase().indexOf(q) !== -1 || r.description.toLowerCase().indexOf(q) !== -1) {
          results.push({ type: "resource", data: r });
        }
      });
      return results.slice(0, 10);
    };

    Store.prototype.completeHomework = function (id) {
      var hw = this.find("homework", function (h) { return h.id === id; });
      if (hw) {
        hw.status = "completed";
        hw.progress = 100;
        hw.completedProblems = hw.totalProblems;
        this.set("homework", this.state.homework);
        this.addXP(50);
        this.updateDashboardStats();
      }
    };

    Store.prototype.addXP = function (amount) {
      this.update("user", { xp: this.state.user.xp + amount });
      this.checkLevelUp();
    };

    Store.prototype.checkLevelUp = function () {
      var xpForNextLevel = this.state.user.level * 1000;
      if (this.state.user.xp >= xpForNextLevel) {
        this.update("user", {
          level: this.state.user.level + 1,
          xpToNextLevel: (this.state.user.level + 1) * 1000 - this.state.user.xp
        });
        this.showToast("Level up! You're now level " + (this.state.user.level + 1));
      } else {
        this.update("user", { xpToNextLevel: xpForNextLevel - this.state.user.xp });
      }
    };

    Store.prototype.updateDashboardStats = function () {
      var completedHw = this.state.homework.filter(function (h) { return h.status === "completed"; }).length;
      var totalStudyTime = this.state.user.totalStudyTime;
      this.update("dashboard", {
        exercisesCompleted: this.state.dashboard.exercisesCompleted + completedHw,
        weeklyXP: this.state.dashboard.weeklyXP + completedHw * 50
      });
    };

    Store.prototype.markNotificationRead = function (id) {
      var notif = this.find("notifications", function (n) { return n.id === id; });
      if (notif) {
        notif.read = true;
        this.set("notifications", this.state.notifications);
      }
    };

    Store.prototype.markAllNotificationsRead = function () {
      this.state.notifications.forEach(function (n) { n.read = true; });
      this.set("notifications", this.state.notifications);
    };

    Store.prototype.clearNotifications = function () {
      this.set("notifications", []);
    };

    Store.prototype.toggleFavoriteLibrary = function (id) {
      var resource = this.find("library", function (r) { return r.id === id; });
      if (resource) {
        resource.favorite = !resource.favorite;
        this.set("library", this.state.library);
      }
    };

    Store.prototype.updateStudyTime = function (minutes) {
      this.update("user", { totalStudyTime: this.state.user.totalStudyTime + minutes });
      this.update("dashboard", { weeklyTime: this.state.dashboard.weeklyTime + minutes });
    };

    Store.prototype.unlockAchievement = function (id) {
      var ach = this.find("achievements", function (a) { return a.id === id; });
      if (ach && !ach.unlocked) {
        ach.unlocked = true;
        ach.unlockedDate = new Date().toISOString().split("T")[0];
        this.set("achievements", this.state.achievements);
        this.showToast("Achievement unlocked: " + ach.title);
      }
    };

    Store.prototype.showToast = function (message) {
      var region = document.getElementById("toastRegion");
      if (!region) return;
      var toast = document.createElement("div");
      toast.className = "toast";
      toast.textContent = message;
      region.appendChild(toast);
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 4200);
    };

    Store.prototype.init = function () {
      try {
        this.state.ui.companionDismissed = localStorage.getItem("companion-dismissed") === "1";
      } catch (e) {}
      this.state.user.preferences.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      this.saveState();
    };

    return Store;
  })();

  // Phase 3B: load initial data from the FastAPI backend. Populates the
  // store so every dashboard / subject / calendar / teacher / homework /
  // notification read comes from SQLite. Falls back silently to the local
  // mock data when the API is unavailable, keeping the frontend working
  // standalone with no visual or behavioural change.
  Store.prototype.initFromAPI = async function () {
    var self = this;
    var endpoints = [
      "/api/dashboard",
      "/api/subjects",
      "/api/teachers",
      "/api/homework",
      "/api/calendar",
      "/api/profile",
      "/api/settings",
      "/api/notifications",
    ];
    await Promise.all(
      endpoints.map(function (path) {
        return fetch(path)
          .then(function (resp) {
            return resp.json();
          })
          .then(function (data) {
            switch (path) {
              case "/api/dashboard":
                if (data && data.stats) self.set("dashboard", data.stats);
                if (data && data.subjects) self.set("subjects", data.subjects);
                break;
              case "/api/subjects":
                if (Array.isArray(data)) self.set("subjects", data);
                break;
              case "/api/teachers":
                if (Array.isArray(data)) self.set("teachers", data);
                break;
              case "/api/homework":
                if (Array.isArray(data)) self.set("homework", data);
                break;
              case "/api/calendar":
                if (Array.isArray(data)) self.set("calendarEvents", data);
                break;
              case "/api/profile":
                if (data) self.set("user", data);
                break;
              case "/api/settings":
                if (Array.isArray(data)) {
                  var prefs = {};
                  data.forEach(function (s) {
                    var v = s.value;
                    if (v === "true") v = true;
                    else if (v === "false") v = false;
                    prefs[s.key] = v;
                  });
                  self.update("user.preferences", prefs);
                }
                break;
              case "/api/notifications":
                if (Array.isArray(data)) self.set("notifications", data);
                break;
            }
          })
          .catch(function (err) {
            // Per-endpoint failure is acceptable; local mock data stays.
            console.warn("API endpoint " + path + " unavailable:", err);
          });
      })
    );
  };

  // Create singleton instance
  window.AppStore = new Store();
  window.AppStore.init();

  // ============================================================
  // API CLIENT (Phase 3B)
  // ============================================================
  // fetchDashboard / postChat now hit the FastAPI backend. When the API
  // is unavailable they fall back to local mock data so the UI never
  // crashes and keeps looking identical.

  window.fetchDashboard = function () {
    return fetch("/api/dashboard")
      .then(function (resp) {
        return resp.json();
      })
      .then(function (data) {
        if (data && data.stats) {
          window.AppStore.set("dashboard", data.stats);
        }
        return data && data.stats
          ? data.stats
          : window.AppStore.get("dashboard");
      })
      .catch(function () {
        return window.AppStore.get("dashboard");
      });
  };

  window.postChat = function (message, teacherId, studentId) {
    return fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        teacher: teacherId || "mathematics",
        student: studentId || 1,
        curriculum: null,
      }),
    })
      .then(function (resp) {
        if (!resp.ok) {
          throw new Error("Chat API error: " + resp.status);
        }
        return resp.json();
      })
      .then(function (data) {
        return {
          reply: data.answer || data.reply || "",
          echo: message,
          timestamp: new Date().toISOString(),
        };
      })
      .catch(function () {
        return {
          reply: "API not yet connected. This is the Phase 3A stub for /api/chat.",
          echo: message,
          timestamp: new Date().toISOString(),
        };
      });
  };

  // ============================================================
  // Phase 5.6: Homework / Quiz / Exam / Timeline / Stats API
  // ============================================================
  window.generateHomework = function (payload) {
    return fetch("/api/homework/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Homework generate error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Homework generate unavailable:", err);
        return null;
      });
  };

  window.submitHomework = function (payload) {
    return fetch("/api/homework/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Homework submit error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Homework submit unavailable:", err);
        return null;
      });
  };

  window.generateQuiz = function (payload) {
    return fetch("/api/quiz/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Quiz generate error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Quiz generate unavailable:", err);
        return null;
      });
  };

  window.submitQuiz = function (payload) {
    return fetch("/api/quiz/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Quiz submit error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Quiz submit unavailable:", err);
        return null;
      });
  };

  window.generateExam = function (payload) {
    return fetch("/api/exam/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Exam generate error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Exam generate unavailable:", err);
        return null;
      });
  };

  window.submitExam = function (payload) {
    return fetch("/api/exam/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("Exam submit error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Exam submit unavailable:", err);
        return null;
      });
  };

  window.fetchTimeline = function (studentId, limit) {
    var url = "/api/timeline?student_id=" + (studentId || 1);
    if (limit) url += "&limit=" + limit;
    return fetch(url)
      .then(function (resp) {
        if (!resp.ok) throw new Error("Timeline error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Timeline unavailable:", err);
        return [];
      });
  };

  window.fetchLearningStats = function (studentId, periodType, subjectId) {
    var url = "/api/stats?student_id=" + (studentId || 1);
    if (periodType) url += "&period_type=" + periodType;
    if (subjectId) url += "&subject_id=" + subjectId;
    return fetch(url)
      .then(function (resp) {
        if (!resp.ok) throw new Error("Stats error: " + resp.status);
        return resp.json();
      })
      .catch(function (err) {
        console.warn("Stats unavailable:", err);
        return [];
      });
  };

})();
