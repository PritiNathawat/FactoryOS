"""
FactoryOS API Root Router
==========================
Aggregates all versioned route modules into a single router.

main.py includes only this router — it does not import individual route modules.
This pattern ensures main.py remains stable as new routes are added in future sprints.

To add a new domain in future sprints:
  1. Create backend/app/api/v1/{domain}.py
  2. Add one `api_router.include_router(...)` line here
  3. main.py requires no changes
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import analysis, decisions, health, incidents, reports

api_router = APIRouter()

# ── v1 Routes ────────────────────────────────────────────────
api_router.include_router(health.router)
api_router.include_router(incidents.router)
api_router.include_router(decisions.router)
api_router.include_router(reports.router)
api_router.include_router(analysis.router)

