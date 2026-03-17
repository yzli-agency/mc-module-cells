"""
yzli/cells — Routes FastAPI
Gestion des cellules fonctionnelles et de leurs rôles.
"""

import re
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter(tags=["cells"])


# ─── Database helpers ─────────────────────────────────────────────────────────

_db = None

def get_db():
    global _db
    if _db is None:
        from core.db import get_db as core_get_db
        _db = core_get_db()
    return _db


def q(sql: str, params: tuple = (), one: bool = False):
    return get_db().q(sql, params, one)


def run(sql: str, params: tuple = ()):
    return get_db().run(sql, params)


async def emit(event: str, data: dict, level: str = "info"):
    from core.bus import get_bus
    await get_bus().emit(event, data, level)


# ─── Models ───────────────────────────────────────────────────────────────────

class CellIn(BaseModel):
    name: str
    slug: Optional[str] = None
    emoji: Optional[str] = "🔷"
    description: Optional[str] = None
    mode: str = "sequential"
    input: Optional[str] = None
    output: Optional[str] = None
    sort_order: Optional[int] = None
    status: str = "active"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_slug(name: str) -> str:
    s = name.lower()
    for fr, en in [('é','e'),('è','e'),('ê','e'),('à','a'),('ü','u')]:
        s = s.replace(fr, en)
    return re.sub(r'[^a-z0-9-]', '', s.replace(' ', '-'))


# ─── Routes: Cells ────────────────────────────────────────────────────────────

@router.get("/")
def list_cells():
    """Liste toutes les cellules avec leurs rôles."""
    cells = q("SELECT * FROM cells ORDER BY sort_order")
    for cell in cells:
        cell["roles"] = q(
            """SELECT r.*, cr.is_lead FROM agent_roles r
               JOIN cell_roles cr ON r.slug = cr.role_slug
               WHERE cr.cell_slug = ? ORDER BY cr.is_lead DESC, r.level""",
            (cell["slug"],)
        )
    return cells


@router.get("/{slug}")
def get_cell(slug: str):
    """Détails d'une cellule."""
    cell = q("SELECT * FROM cells WHERE slug=?", (slug,), one=True)
    if not cell:
        raise HTTPException(404)
    
    cell["roles"] = q(
        """SELECT r.*, cr.is_lead FROM agent_roles r
           JOIN cell_roles cr ON r.slug = cr.role_slug
           WHERE cr.cell_slug = ? ORDER BY cr.is_lead DESC, r.level""",
        (slug,)
    )
    return cell


@router.post("/", status_code=201)
async def create_cell(c: CellIn):
    """Créer une nouvelle cellule."""
    slug = c.slug or _make_slug(c.name)
    
    existing = q("SELECT id FROM cells WHERE slug=?", (slug,), one=True)
    if existing:
        raise HTTPException(409, f"Cellule avec slug '{slug}' existe déjà")
    
    max_order = q("SELECT MAX(sort_order) as m FROM cells", one=True)
    sort_order = c.sort_order or ((max_order["m"] or 0) + 1)
    
    run(
        "INSERT INTO cells (slug,name,emoji,description,mode,input,output,sort_order,status) VALUES (?,?,?,?,?,?,?,?,?)",
        (slug, c.name, c.emoji, c.description, c.mode, c.input, c.output, sort_order, c.status)
    )
    
    await emit("cell.created", {"slug": slug, "name": c.name}, "success")
    return q("SELECT * FROM cells WHERE slug=?", (slug,), one=True)


@router.put("/{slug}")
async def update_cell(slug: str, c: CellIn):
    """Mettre à jour une cellule."""
    row = q("SELECT * FROM cells WHERE slug=?", (slug,), one=True)
    if not row:
        raise HTTPException(404, "Cellule introuvable")
    
    run(
        "UPDATE cells SET name=?,emoji=?,description=?,mode=?,input=?,output=?,status=? WHERE slug=?",
        (c.name, c.emoji, c.description, c.mode, c.input, c.output, c.status, slug)
    )
    
    await emit("cell.updated", {"slug": slug, "name": c.name}, "info")
    return q("SELECT * FROM cells WHERE slug=?", (slug,), one=True)


@router.delete("/{slug}", status_code=204)
async def delete_cell(slug: str):
    """Supprimer une cellule."""
    row = q("SELECT * FROM cells WHERE slug=?", (slug,), one=True)
    if not row:
        raise HTTPException(404, "Cellule introuvable")
    
    run("DELETE FROM cell_roles WHERE cell_slug=?", (slug,))
    run("DELETE FROM cells WHERE slug=?", (slug,))
    
    await emit("cell.deleted", {"slug": slug}, "warn")


# ─── Routes: Cell Roles ───────────────────────────────────────────────────────

@router.post("/{slug}/roles")
async def add_cell_role(slug: str, body: dict = Body(...)):
    """Ajouter un rôle à une cellule."""
    role_slug = body.get("role_slug")
    is_lead = body.get("is_lead", False)
    
    if not role_slug:
        raise HTTPException(400, "role_slug requis")
    
    existing = q("SELECT * FROM cell_roles WHERE cell_slug=? AND role_slug=?", (slug, role_slug), one=True)
    if existing:
        run("UPDATE cell_roles SET is_lead=? WHERE cell_slug=? AND role_slug=?", (1 if is_lead else 0, slug, role_slug))
    else:
        run("INSERT INTO cell_roles (cell_slug, role_slug, is_lead) VALUES (?,?,?)", (slug, role_slug, 1 if is_lead else 0))
    
    await emit("cell.role.added", {"cell": slug, "role": role_slug, "is_lead": is_lead}, "info")
    return {"ok": True}


@router.delete("/{slug}/roles/{role_slug}", status_code=204)
async def remove_cell_role(slug: str, role_slug: str):
    """Retirer un rôle d'une cellule."""
    run("DELETE FROM cell_roles WHERE cell_slug=? AND role_slug=?", (slug, role_slug))
    await emit("cell.role.removed", {"cell": slug, "role": role_slug}, "info")


# ─── Routes: Constellation View ───────────────────────────────────────────────

@router.get("/constellation")
def get_constellation():
    """Vue constellation : cellules avec leurs rôles et connexions."""
    cells = q("SELECT * FROM cells ORDER BY sort_order")
    
    # Build adjacency based on input/output
    connections = []
    cell_by_output = {}
    
    for cell in cells:
        if cell.get("output"):
            cell_by_output[cell["output"]] = cell["slug"]
    
    for cell in cells:
        if cell.get("input") and cell["input"] in cell_by_output:
            connections.append({
                "from": cell_by_output[cell["input"]],
                "to": cell["slug"],
                "type": cell["input"],
            })
        
        cell["roles"] = q(
            """SELECT r.slug, r.name, r.level, cr.is_lead FROM agent_roles r
               JOIN cell_roles cr ON r.slug = cr.role_slug
               WHERE cr.cell_slug = ?""",
            (cell["slug"],)
        )
    
    return {
        "cells": cells,
        "connections": connections,
    }


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/health")
def cells_health():
    """Health check."""
    cells = q("SELECT COUNT(*) as n FROM cells", one=True)["n"]
    roles = q("SELECT COUNT(*) as n FROM cell_roles", one=True)["n"]
    return {
        "status": "ok",
        "cells": cells,
        "role_assignments": roles,
    }
