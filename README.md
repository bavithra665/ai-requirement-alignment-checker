# AI-Powered Requirement-to-Implementation Alignment Checker

Production-grade SaaS monorepo for validating implementations against initial requirements.

## Architecture

- **Frontend**: Next.js 15, React, Tailwind CSS v4, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, ChromaDB
- **Monorepo**: pnpm workspaces

## Getting Started

1. Copy `.env.example` to `.env` in the root, `apps/web`, and `apps/api`
2. Start infrastructure: `docker-compose up -d`
3. Install frontend dependencies: `pnpm install`
4. Setup backend: `cd apps/api && uv sync`
5. Run DB migrations: `cd apps/api && uv run alembic upgrade head`

## Commands

- Start web: `cd apps/web && pnpm dev`
- Start api: `cd apps/api && uv run uvicorn app.main:app --reload`
