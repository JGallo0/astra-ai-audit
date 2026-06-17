-- Co2mply — tabelas com prefixo ca_ para não colidir com astra-forestry
-- Rodar no SQL Editor do Supabase (projeto frspdiilcstqtytmjgbe)

CREATE TABLE IF NOT EXISTS ca_projects (
  id                          TEXT PRIMARY KEY,
  name                        TEXT NOT NULL,
  methodology                 TEXT NOT NULL,
  project_vector_store_id     TEXT NOT NULL,
  methodology_vector_store_id TEXT,
  doc_count                   INTEGER DEFAULT 0,
  created_at                  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ca_audit_runs (
  id           TEXT PRIMARY KEY,
  project_id   TEXT NOT NULL REFERENCES ca_projects(id) ON DELETE CASCADE,
  methodology  TEXT,
  modules      JSONB,
  status       TEXT NOT NULL DEFAULT 'running',
  result       JSONB,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ca_chat_messages (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES ca_projects(id) ON DELETE CASCADE,
  role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ca_audit_runs_project ON ca_audit_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_ca_chat_messages_project ON ca_chat_messages(project_id);
