-- yzli/cells — Migration 001
CREATE TABLE IF NOT EXISTS cells (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    emoji TEXT DEFAULT '🔷',
    description TEXT,
    mode TEXT DEFAULT 'sequential',
    input TEXT,
    output TEXT,
    sort_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cell_roles (
    id INTEGER PRIMARY KEY,
    cell_slug TEXT REFERENCES cells(slug) ON DELETE CASCADE,
    role_slug TEXT NOT NULL,
    is_lead INTEGER DEFAULT 0,
    UNIQUE(cell_slug, role_slug)
);

-- Seed initial cells
INSERT OR IGNORE INTO cells (slug, name, emoji, description, mode, sort_order) VALUES
  ('client', 'Client', '🤝', 'Cadrage, discovery, brief, PRD', 'sequential', 1),
  ('production', 'Production', '📐', 'UX, UI, specs fonctionnelles, wireframes', 'sequential', 2),
  ('developpement', 'Développement', '💻', 'Code, intégration, tests, déploiement', 'parallel', 3),
  ('veille', 'Veille', '🔭', 'Surveillance technologique et concurrentielle', 'continuous', 4),
  ('communication', 'Communication', '📣', 'Contenu, social, éditorial', 'pipeline', 5),
  ('rnd', 'R&D', '🧪', 'Innovation, expérimentation, prototypage', 'cyclical', 6);
