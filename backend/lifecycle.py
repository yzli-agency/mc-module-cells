"""
yzli/cells — Module Lifecycle Hooks
"""

import logging

logger = logging.getLogger("yzli.cells")


def on_activate(config: dict):
    """Called when the cells module is activated."""
    logger.info("Cells module activated")
    _ensure_tables()
    return True


def on_deactivate():
    """Called when the cells module is deactivated."""
    logger.info("Cells module deactivated")


def _ensure_tables():
    """Ensure required database tables exist."""
    from core.db import get_db
    
    db = get_db()
    db.execute_script("""
        -- Cells
        CREATE TABLE IF NOT EXISTS cells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT DEFAULT '🔷',
            description TEXT,
            mode TEXT DEFAULT 'sequential',
            input TEXT,
            output TEXT,
            sort_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_cells_slug ON cells(slug);
        
        -- Cell-Role mappings
        CREATE TABLE IF NOT EXISTS cell_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cell_slug TEXT REFERENCES cells(slug),
            role_slug TEXT REFERENCES agent_roles(slug),
            is_lead INTEGER DEFAULT 0,
            UNIQUE(cell_slug, role_slug)
        );
        CREATE INDEX IF NOT EXISTS idx_cell_roles_cell ON cell_roles(cell_slug);
        CREATE INDEX IF NOT EXISTS idx_cell_roles_role ON cell_roles(role_slug);
    """)
    
    # Seed default cells if empty
    count = db.q("SELECT COUNT(*) as n FROM cells", one=True)["n"]
    if count == 0:
        _seed_default_cells(db)
    
    logger.info("Cells tables initialized")


def _seed_default_cells(db):
    """Seed default cells."""
    cells = [
        ("client", "Client", "👤", "Onboarding, brief, réunions clients", "sequential", None, "brief", 1),
        ("production", "Production", "🎨", "UX/UI, specs, user stories, maquettes", "sequential", "brief", "spec", 2),
        ("developpement", "Développement", "💻", "Code, tests, intégration, déploiement", "sequential", "spec", "code", 3),
        ("veille", "Veille", "🔭", "Veille techno, recherche, benchmark", "parallel", None, "insight", 4),
        ("communication", "Communication", "📢", "Contenu, marketing, social", "sequential", "insight", "content", 5),
        ("rnd", "R&D", "🔬", "Innovation, prototypes, exploration", "parallel", None, None, 6),
    ]
    
    for slug, name, emoji, desc, mode, inp, out, order in cells:
        db.run(
            "INSERT INTO cells (slug,name,emoji,description,mode,input,output,sort_order) VALUES (?,?,?,?,?,?,?,?)",
            (slug, name, emoji, desc, mode, inp, out, order)
        )
    
    logger.info(f"Seeded {len(cells)} default cells")
