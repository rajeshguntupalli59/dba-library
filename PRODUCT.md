# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are junior and aspiring DBAs — people early in their database
administration career working through foundational material (SQL Server and
PostgreSQL fundamentals, indexing, performance, HA/DR, security). For the
interactive game surface specifically (`game/`), the user is reading or has
read a chapter of *The DBA Handbook* and wants active practice instead of
passively re-reading — someone at a desk, in a focused self-study session,
not a passive/ambient reading moment. The wider site also serves more senior
DBAs and platform engineers through its advanced books (AI-Powered DBA, ADE
Handbook, Cloud Database Engineer) and its self-hosted tools (QueryOptimizer,
DB Documenter, DB Hub).

## Product Purpose

A personal site by Rajesh Guntupalli (SQL Server DBA, tool builder, author)
offering free, self-hosted database tools and free technical books online.
No cloud, no subscription, no telemetry, no sign-up — content and tools are
downloadable/readable and run entirely on the user's own infrastructure or
in their browser. Success means readers actually learn and retain database
concepts, and DBAs adopt the free tools for real diagnostic work.

## Positioning

"No cloud, no subscription, no telemetry — built by a DBA for DBAs" is the
site-wide claim a SaaS competitor could not truthfully copy. For the
interactive game surface specifically, the differentiator is active
retention over passive reading: turning one-way book prose into click-through
practice (animated concept walkthroughs, realistic production scenarios,
quizzes with immediate feedback) so concepts actually stick, rather than
being read once and forgotten. Progress/XP tracking exists to reinforce this
mechanism (has the reader actually engaged with the material), not as a
gamification/habit-loop end in itself.

## Operating Context

Static site (GitHub Pages), zero build step, plain HTML pages using the
Tailwind CDN with no bundler. 7 books, ~250 chapters of long-form technical
prose, each chapter a standalone HTML file. A pilot interactive layer
(`game/`) currently covers Chapter 1 of *The DBA Handbook* (4 scenes: an
ACID-guarantees animation, a PostgreSQL-vs-SQL-Server timeline animation, a
production-scenario challenge, and a quiz), reusable in principle for the
other 39 chapters of that book and eventually the other 6 books.

## Capabilities and Constraints

- No accounts, no backend, no cloud sync anywhere on the site — the game's
  XP/progress lives in the browser's `localStorage` only, with an in-memory
  fallback when unavailable (e.g. private browsing).
- Existing book chapter files (`book/ch*.html`, and the equivalent chapter
  directories in `book2/`–`book7/`) must never be edited by design/animation
  work — the interactive layer is strictly additive, living in its own
  `game/` directory plus small, additive links from `book.html` and
  `book/index.html`.
- Every fact presented in an interactive scene must trace back to the actual
  chapter text; where a scene dramatizes an abstract example with invented
  specifics (e.g. concrete dollar figures for the chapter's abstract
  bank-transfer example), that must be clearly labeled as an illustrative
  simulation, not presented as literal chapter content.
- No animation library is currently installed; the site has zero JS
  dependencies beyond the Tailwind CDN and (on some chapter pages only)
  Mermaid.js for diagrams. Any new animation approach should stay consistent
  with this repo's "no build step" posture unless a real need justifies
  otherwise.

## Brand Commitments

Author/owner: Rajesh Guntupalli — "SQL Server DBA, Tool Builder & Author."
Dark theme (`bg-gray-950`, `text-gray-100`, blue-600/300 accents) is the
established visual identity across the entire site, including the game
surface. No existing motion/animation system to preserve — this is
greenfield for motion specifically.

## Evidence on Hand

7 published books' worth of real chapter content (not placeholder text);
Chapter 1 of *The DBA Handbook* is the only chapter with an interactive game
built so far, live at `game/ch01.html`. No user testimonials, usage metrics,
or completion-rate data exist yet — this is a new, unvalidated feature.

## Product Principles

1. Active retention over passive reading — every interactive element should
   make a concept more memorable than reading the same sentence would, not
   just add visual interest.
2. Explain "what is what" as things move — motion should carry meaning
   (labeling which element represents which concept as it animates), not be
   decoration layered on top of a static explanation.
3. No cloud, no accounts, no telemetry — this constraint is load-bearing
   brand identity across the whole site, not just a technical default.
4. Facts trace to the source — dramatization for engagement is fine;
   presenting invented specifics as literal book content is not.
5. Additive, never destructive to existing content — the game layer must be
   removable without any loss to the underlying books.

## Accessibility & Inclusion

No explicit accessibility standard has been confirmed as a requirement yet.
The existing interactive scenes use plain DOM text/buttons (no custom
widgets), but lack `aria-live` regions for dynamically-swapped content and
proper tab/role semantics for the scene-navigation tabs — noted as a known
gap, not yet a confirmed requirement to fix.
