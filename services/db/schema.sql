-- AI School OS — Phase 3B SQLite schema
-- Seed data mirrors the Phase 3A frontend mock data exactly so the UI
-- remains pixel-perfect and behaviour-identical.

PRAGMA foreign_keys = ON;

-- ============================================================
-- students
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  avatar TEXT,
  cohort TEXT,
  semester INTEGER,
  joined_date TEXT,
  level INTEGER,
  xp INTEGER,
  xp_to_next_level INTEGER,
  streak INTEGER,
  total_study_time INTEGER,
  mastery INTEGER,
  weekly_xp INTEGER,
  weekly_time INTEGER,
  exercises_completed INTEGER,
  completion_rate INTEGER,
  weekly_goal_progress INTEGER,
  current_subject_id TEXT,
  theme TEXT,
  language TEXT,
  animations INTEGER DEFAULT 1,
  reduced_motion INTEGER DEFAULT 0,
  captions INTEGER DEFAULT 1,
  focus_mode INTEGER DEFAULT 0,
  lesson_reminders INTEGER DEFAULT 1
);

-- ============================================================
-- subjects
-- ============================================================
CREATE TABLE IF NOT EXISTS subjects (
  id TEXT PRIMARY KEY,
  icon TEXT,
  name TEXT NOT NULL,
  description TEXT,
  progress INTEGER,
  color TEXT,
  teacher TEXT,
  next_session TEXT,
  lessons INTEGER,
  mastery INTEGER,
  streak INTEGER,
  difficulty TEXT,
  last_lesson TEXT
);

-- ============================================================
-- teachers
-- ============================================================
CREATE TABLE IF NOT EXISTS teachers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  specialty TEXT,
  status TEXT,
  description TEXT,
  avatar TEXT,
  rating REAL,
  next_session TEXT
);

-- ============================================================
-- progress (per-subject metric cards)
-- ============================================================
CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id TEXT,
  label TEXT,
  value INTEGER,
  unit TEXT,
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- lessons (lesson history)
-- ============================================================
CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id TEXT,
  name TEXT,
  date TEXT,
  tag TEXT,
  duration TEXT,
  score TEXT,
  status TEXT,
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- homework / assignments
-- ============================================================
CREATE TABLE IF NOT EXISTS homework (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  subject TEXT,
  title TEXT,
  description TEXT,
  due_date TEXT,
  status TEXT,
  priority TEXT,
  progress INTEGER,
  completed_problems INTEGER,
  total_problems INTEGER,
  estimated_time INTEGER,
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
  id TEXT PRIMARY KEY,
  type TEXT,
  title TEXT,
  message TEXT,
  read INTEGER DEFAULT 0,
  timestamp INTEGER
);

-- ============================================================
-- calendar events
-- ============================================================
CREATE TABLE IF NOT EXISTS calendar (
  id TEXT PRIMARY KEY,
  date TEXT,
  title TEXT,
  type TEXT,
  subject_id TEXT,
  time TEXT,
  duration INTEGER,
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- settings (key/value store)
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

-- ============================================================
-- messages (POST /api/notes target)
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT,
  created_at TEXT
);

-- ============================================================
-- conversation history (AI Foundation - Phase 4.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS conversation_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  teacher_id TEXT NOT NULL,
  role TEXT NOT NULL,            -- 'user' or 'assistant'
  message TEXT NOT NULL,
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (student_id) REFERENCES students(id)
);

-- ============================================================
-- mistakes (AI Foundation - Phase 4.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS mistakes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  subject_id TEXT,
  topic TEXT NOT NULL,
  description TEXT,
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- weak topics (AI Foundation - Phase 4.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS weak_topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  subject_id TEXT,
  topic TEXT NOT NULL,
  weakness_score REAL NOT NULL DEFAULT 0.0,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- strong topics (AI Foundation - Phase 4.1)
-- ============================================================
CREATE TABLE IF NOT EXISTS strong_topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  subject_id TEXT,
  topic TEXT NOT NULL,
  strength_score REAL NOT NULL DEFAULT 0.0,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- memory state (AI Foundation - Phase 4.1)
-- Current curriculum, teacher, and mission per student.
-- ============================================================
CREATE TABLE IF NOT EXISTS memory_state (
  id INTEGER PRIMARY KEY,
  student_id INTEGER NOT NULL UNIQUE,
  current_curriculum TEXT,
  current_teacher_id TEXT,
  current_mission TEXT,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (student_id) REFERENCES students(id)
);

-- ============================================================
-- indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_homework_subject ON homework(subject_id);
CREATE INDEX IF NOT EXISTS idx_homework_status ON homework(status);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON calendar(date);
CREATE INDEX IF NOT EXISTS idx_subjects_progress ON subjects(progress);
CREATE INDEX IF NOT EXISTS idx_lessons_subject ON lessons(subject_id);
CREATE INDEX IF NOT EXISTS idx_conversation_student ON conversation_history(student_id);
CREATE INDEX IF NOT EXISTS idx_conversation_teacher ON conversation_history(teacher_id);
CREATE INDEX IF NOT EXISTS idx_mistakes_student ON mistakes(student_id);
CREATE INDEX IF NOT EXISTS idx_weak_topics_student ON weak_topics(student_id);
CREATE INDEX IF NOT EXISTS idx_strong_topics_student ON strong_topics(student_id);
