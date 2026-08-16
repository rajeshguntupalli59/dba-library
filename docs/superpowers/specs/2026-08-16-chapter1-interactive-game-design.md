# Chapter 1 Interactive Game — Design Spec

**Date:** 2026-08-16
**Status:** Approved by user, pending spec review
**Repo:** rajeshguntupalli59/https-rajeshguntupalli59.github.io

## Goal

Turn Chapter 1 of *The DBA Handbook* ("Introduction") into a self-contained interactive
learning experience — animated concept visuals, a scenario challenge, and a quiz —
with XP/progress tracked in the browser. This is a pilot: if it works, the same engine
and content-file pattern extend to the other 39 chapters (and eventually the other
6 books) later. That extension is explicitly out of scope for this spec.

**Hard constraint:** no edits to any existing chapter file (`book/ch*.html`,
and by extension the equivalent chapter directories in `book2/`–`book7/`). Small
additive links may be added to `book.html` and `book/index.html` only.

## Current site facts (verified from the cloned repo)

- Static site, no build step. Every page is a standalone HTML file using the
  **Tailwind CDN** (`<script src="https://cdn.tailwindcss.com">`) plus a shared
  `style.css`. Dark theme: `bg-gray-950`, `text-gray-100`, blue-600/300 accents.
- Chapters also load **Mermaid.js** (`theme: dark`) for diagrams — e.g. the B-tree
  figure in Chapter 6 is a Mermaid diagram, not a static image. Chapter 1 itself has
  no diagrams, only prose sections.
- Each chapter page repeats the same nav markup inline (no shared include/template
  system, no server-side includes — this is a fully static multi-page site).
- `book.html` already has two dead links to `http://localhost:5175` ("Study with AI
  Quizzes" / "Try Free — No Signup", lines 219 and 598) — an abandoned prototype.
  Per user direction, these are left untouched; this project does not reuse or
  reference that experiment.
- No `docs/` folder existed before this spec.

## Chapter 1 source content (facts the game must present accurately)

Chapter 1 ("Introduction") has five sections, verified from `book/ch01-introduction.html`:

1. **Why Relational Databases Still Rule** — declarative query language separates
   intent from execution; ACID (atomicity, consistency, isolation, durability)
   guarantees illustrated via the book's own bank-transfer / airline-seat /
   hospital-dose examples.
2. **PostgreSQL and SQL Server — Two Platforms, One Discipline** — PostgreSQL:
   Berkeley research project (1980s) → open-source, free, extension ecosystem
   (PostGIS, TimescaleDB, pgvector), yearly major releases, dominant in
   startups/SaaS. SQL Server: commercial, Microsoft, first released 1989, deep
   Windows/Azure integration, dominant in finance/healthcare/manufacturing,
   SSMS tooling. Both implement SQL-92/SQL:2016, transactions, FKs, triggers,
   views, stored procedures, partitioning, replication, full-text search. The
   book's thesis: learning both in parallel reveals the *design decisions*
   under the syntax.
3. **What DBAs Actually Do in Production** — four recurring categories of real
   DBA work: performance investigation (e.g. a 200ms query becoming 45s),
   schema evolution (e.g. altering a table with 800M rows), capacity/growth
   planning, and reliability/recovery (backups, point-in-time recovery,
   replication lag).
4. **How to Read This Book** — 40 chapters, PostgreSQL + SQL Server examples
   throughout, chapters build on each other but each is also a standalone
   reference.
5. **The Mindset of a Database Engineer** — five habits: measure before you
   optimize; understand the cost of decisions (e.g. indexes speed reads, slow
   writes); think about failure modes; document what you do and why; treat the
   database as a shared system, not a black box.

All quiz questions, scenario text, and animation labels must be traceable to one
of these five sections — no invented facts.

## Architecture

New `game/` directory at repo root, sibling to `book/`, completely separate from it:

```
game/
  engine.js        shared: localStorage XP/progress store + scene player
  engine.css        (or inline Tailwind utility classes matching site theme)
  content/
    ch01.js         plain JS data file: Chapter 1's scenes, text, quiz Q&A
  ch01.html          thin page: loads engine.js + content/ch01.js, mounts game
  index.html         landing page listing playable chapters (Ch.1 only for now)
```

The engine renders three scene *types* driven entirely by the content file:
`animation`, `scenario`, `quiz`. Adding chapter 2 later means writing a new
`content/ch02.js` — no engine changes required. This is the only piece of
speculative design in this spec, and it's justified because "become an expert
along the way" requires a shared progress model to exist from the start, even
though only one chapter is built now.

Visual style reuses the site's existing Tailwind CDN + dark theme classes
(`bg-gray-950`, `text-gray-100`, blue accents) so the game doesn't look like a
bolted-on separate app. No Mermaid dependency — Chapter 1's animations are
custom (bank-transfer diagram, timeline), not the kind of static diagram
Mermaid renders.

**Entry point:** one small "▶ Play Chapter 1" link/button added near the
`id="book-1"` card in `book.html` (around line 151) and one added to
`book/index.html`'s chapter list (chapter 1 row). No other existing file is
touched.

## Chapter 1 → 4 scenes

1. **"The ACID Test" (animation)** — Interactive bank-transfer diagram (the
   book's own example, Section 1). User clicks through: debit Account A →
   credit Account B → commit. A "simulate crash mid-transfer" toggle plays a
   rollback animation, demonstrating Atomicity concretely. Brief on-screen
   labels tie the same transfer to Consistency, Isolation, and Durability.
2. **"Two Paths, One Discipline" (animation)** — Split timeline: PostgreSQL
   (Berkeley 1980s → open source → extensions) vs. SQL Server (Microsoft 1989
   → enterprise/Azure), built from Section 2's facts only. Clicking era
   markers reveals the corresponding fact. Ends by reinforcing the book's
   stated thesis: learn both in parallel.
3. **"A Day in Production" (scenario)** — Four short decision vignettes, one
   per category from Section 3 (performance investigation, schema evolution,
   capacity planning, reliability/recovery), each with 2–3 clickable choices
   and feedback that reinforces "measure before you optimize" (Section 5).
4. **"The Mindset Check" (quiz)** — 4 questions drawn from ACID, the
   PostgreSQL/SQL Server facts, and the five mindset habits (Section 5), with
   immediate right/wrong feedback and a one-line explanation per answer.

## Progression model

- Single `localStorage` key (e.g. `dba-handbook-progress`) holding: XP total,
  per-chapter completion + per-scene state, and a `chaptersMastered / 40`
  counter. The schema has room for chapters 2–40 even though only chapter 1
  is playable, so future chapters don't require a data migration.
- XP awarded per scene: small amount for completing an animation scene,
  more for correct scenario choices, more for correct quiz answers.
- No accounts, no backend, no sync — matches the site's existing "no cloud,
  no sign-up" positioning.
- If `localStorage` is unavailable (e.g. private browsing), the engine falls
  back to an in-memory object for the session instead of throwing — progress
  just won't persist across reloads in that case.

## Testing / verification

The site has no build system and no existing automated test suite, so this
follows the same pattern: manual verification only.

Checklist for the pilot:
- Open `game/ch01.html` directly and via the new links from `book.html` /
  `book/index.html`.
- Complete all 4 scenes; confirm XP increases as expected after each.
- Reload the page mid-chapter and after completion; confirm progress persists.
- Disable localStorage (private/incognito) and confirm the game still runs
  without crashing (in-memory fallback).
- Diff-check that no file under `book/` was modified, and that `book.html` /
  `book/index.html` changes are limited to the new link(s).
- Spot-check every fact shown in-game against the chapter text listed above.

## Out of scope for this spec

- Chapters 2–40, and the other 6 books.
- Any backend, accounts, or cross-device sync.
- Reworking or removing the dead `localhost:5175` links in `book.html`.
- Mermaid-based diagrams (not needed for this chapter's content).
