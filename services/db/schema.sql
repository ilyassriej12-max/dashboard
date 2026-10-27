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
-- lesson_progress (Phase 5.6 - persistent per-lesson progress)
-- ============================================================
CREATE TABLE IF NOT EXISTS lesson_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  subject_id TEXT NOT NULL,
  lesson_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'not_started',
  attempts INTEGER DEFAULT 0,
  time_spent_minutes INTEGER DEFAULT 0,
  best_score REAL,
  last_attempt_at INTEGER,
  completed_at INTEGER,
  UNIQUE(student_id, subject_id, lesson_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- competency_mastery (Phase 5.6 - persistent competency scores)
-- ============================================================
CREATE TABLE IF NOT EXISTS competency_mastery (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  subject_id TEXT NOT NULL,
  competency_id TEXT NOT NULL,
  score REAL DEFAULT 0.0,
  updated_at INTEGER,
  times_assessed INTEGER DEFAULT 0,
  UNIQUE(student_id, subject_id, competency_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- homework_attempts (Phase 5.6 - persistent homework records)
-- ============================================================
CREATE TABLE IF NOT EXISTS homework_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  homework_id TEXT NOT NULL UNIQUE,
  student_id INTEGER NOT NULL,
  subject_id TEXT NOT NULL,
  chapter_id TEXT,
  lesson_id TEXT,
  competency TEXT,
  title TEXT,
  description TEXT,
  difficulty TEXT,
  due_date TEXT,
  estimated_time INTEGER,
  status TEXT DEFAULT 'pending',
  score REAL,
  total_score REAL,
  percentage REAL,
  created_at INTEGER,
  completed_at INTEGER,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- quiz_attempts (Phase 5.6 - persistent quiz records)
-- ============================================================
CREATE TABLE IF NOT EXISTS quiz_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  quiz_id TEXT NOT NULL UNIQUE,
  student_id INTEGER NOT NULL,
  subject_id TEXT NOT NULL,
  chapter_id TEXT,
  lesson_id TEXT,
  competency TEXT,
  title TEXT,
  difficulty TEXT,
  num_questions INTEGER,
  score REAL,
  total_score REAL,
  percentage REAL,
  grade TEXT,
  passed INTEGER DEFAULT 0,
  started_at INTEGER,
  completed_at INTEGER,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- exam_attempts (Phase 5.6 - persistent exam records)
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exam_id TEXT NOT NULL UNIQUE,
  student_id INTEGER NOT NULL,
  subject_id TEXT NOT NULL,
  chapter_id TEXT,
  lesson_id TEXT,
  competency TEXT,
  title TEXT,
  exam_type TEXT,
  difficulty TEXT,
  num_questions INTEGER,
  score REAL,
  total_score REAL,
  percentage REAL,
  grade TEXT,
  passed INTEGER DEFAULT 0,
  time_spent_minutes INTEGER DEFAULT 0,
  started_at INTEGER,
  completed_at INTEGER,
  recommendations TEXT,
  barème TEXT,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- learning_timeline (Phase 5.6 - chronological learning history)
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_timeline (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  subject_id TEXT,
  lesson_id TEXT,
  chapter_id TEXT,
  title TEXT,
  description TEXT,
  score REAL,
  timestamp INTEGER NOT NULL,
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- learning_statistics (Phase 5.6 - aggregated study stats)
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_statistics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  period_type TEXT NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  total_study_time_minutes INTEGER DEFAULT 0,
  lessons_completed INTEGER DEFAULT 0,
  quizzes_taken INTEGER DEFAULT 0,
  exams_taken INTEGER DEFAULT 0,
  average_quiz_score REAL,
  average_exam_score REAL,
  completion_rate REAL,
  subject_id TEXT,
  updated_at INTEGER,
  UNIQUE(student_id, period_type, period_start, subject_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- ============================================================
-- indexes (Phase 5.6 additions)
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
CREATE INDEX IF NOT EXISTS idx_lesson_progress_student ON lesson_progress(student_id);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_subject ON lesson_progress(subject_id);
CREATE INDEX IF NOT EXISTS idx_competency_mastery_student ON competency_mastery(student_id);
CREATE INDEX IF NOT EXISTS idx_competency_mastery_subject ON competency_mastery(subject_id);
CREATE INDEX IF NOT EXISTS idx_homework_attempts_student ON homework_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_exam_attempts_student ON exam_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_learning_timeline_student ON learning_timeline(student_id);
CREATE INDEX IF NOT EXISTS idx_learning_statistics_student ON learning_statistics(student_id);
