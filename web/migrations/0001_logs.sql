-- The site's event log (searches, unanswered questions, feedback, logins): src/feedback.js.
-- npx wrangler d1 migrations apply matrag-logs --remote
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time TEXT NOT NULL,          -- ISO 8601, UTC
  kind TEXT NOT NULL,          -- search, unanswered, feedback, login, failedlogin
  user TEXT NOT NULL,
  q TEXT NOT NULL DEFAULT '',  -- the question or comment, cut to 180 characters
  v TEXT NOT NULL DEFAULT '',  -- the verdict
  data TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS logs_time ON logs (time);
CREATE INDEX IF NOT EXISTS logs_user_time ON logs (user, time);
