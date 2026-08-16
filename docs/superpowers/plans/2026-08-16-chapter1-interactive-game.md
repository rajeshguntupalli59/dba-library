# Chapter 1 Interactive Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Chapter 1 of *The DBA Handbook* into a self-contained interactive game — animated concept walkthroughs, a production scenario, and a quiz — with XP/progress tracked in the browser via `localStorage`, without modifying any existing chapter file.

**Architecture:** A new `game/` directory at the repo root, sibling to `book/`. A tiny, storage-agnostic `progress-store.js` module (pure logic, unit-tested with Node's built-in test runner) tracks XP and scene completion. A `scene-player.js` module renders three scene types (`animation`, `scenario`, `quiz`) into the DOM, driven entirely by a plain-data content file (`content/ch01.js`). Two thin HTML pages (`game/index.html`, `game/ch01.html`) wire it together. Small additive links are added to `book.html` and `book/index.html` only.

**Tech Stack:** Vanilla JS (ES modules), Tailwind CDN (already used site-wide), Node's built-in `node:test` + `node:assert` for the pure-logic unit tests (zero new dependencies — this repo has no build step and this plan doesn't add one).

## Global Constraints

- No file under `book/`, `book2/`–`book7/` (any existing chapter content) may be modified. — from spec, "Hard constraint"
- Only `book.html` and `book/index.html` may receive small additive links; no other existing file is touched. — from spec
- Every fact shown in-game (animation labels, scenario prompts, quiz questions/explanations) must trace back to `book/ch01-introduction.html`'s five sections (ACID/relational model, PostgreSQL vs. SQL Server, what DBAs do, how to read the book, the mindset habits). — from spec
- No accounts, no backend — progress lives in `localStorage` only, with an in-memory fallback if `localStorage` is unavailable. — from spec
- Visual style must reuse the site's existing Tailwind CDN + dark theme (`bg-gray-950`, `text-gray-100`, blue accents). — from spec

---

### Task 1: Progress store (pure logic + unit tests)

**Files:**
- Create: `package.json`
- Create: `game/progress-store.js`
- Test: `tests/game/progress-store.test.js`

**Interfaces:**
- Consumes: nothing (first task).
- Produces (used by Tasks 3, 4, 5):
  - `STORAGE_KEY: string`
  - `parseProgress(raw: string|null|undefined): { xp: number, chapters: Record<string, Record<string, number>> }`
  - `serializeProgress(progress): string`
  - `createStorageAdapter(storageLike: {getItem, setItem, removeItem}): { read(): string|null, write(str: string): boolean }`
  - `createProgressStore(storageLike): { getProgress(), isSceneComplete(chapterId, sceneId): boolean, awardSceneXp(chapterId, sceneId, xp: number): object, getChapterStats(chapterId, totalScenes: number): {completedScenes, totalScenes, mastered: boolean}, getTotalXp(): number, getChaptersMasteredCount(chapterTotals: Record<string, number>): number }`

- [ ] **Step 1: Add `package.json` so Node treats `.js` files as ES modules**

```json
{
  "name": "https-rajeshguntupalli59-github-io",
  "private": true,
  "type": "module"
}
```

- [ ] **Step 2: Write the failing test file**

Create `tests/game/progress-store.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseProgress,
  serializeProgress,
  createStorageAdapter,
  createProgressStore,
} from '../../game/progress-store.js';

function makeFakeStorage(overrides = {}) {
  const store = new Map();
  return {
    getItem: overrides.getItem || ((key) => (store.has(key) ? store.get(key) : null)),
    setItem: overrides.setItem || ((key, value) => store.set(key, value)),
    removeItem: overrides.removeItem || ((key) => store.delete(key)),
  };
}

test('parseProgress returns default shape for null/invalid input', () => {
  assert.deepEqual(parseProgress(null), { xp: 0, chapters: {} });
  assert.deepEqual(parseProgress('not json'), { xp: 0, chapters: {} });
  assert.deepEqual(parseProgress(undefined), { xp: 0, chapters: {} });
});

test('parseProgress round-trips a valid serialized progress object', () => {
  const original = { xp: 42, chapters: { ch01: { 'acid-test': 20 } } };
  const raw = serializeProgress(original);
  assert.deepEqual(parseProgress(raw), original);
});

test('createStorageAdapter falls back to in-memory storage when localStorage throws', () => {
  const throwingStorage = makeFakeStorage({
    setItem: () => { throw new Error('QuotaExceededError'); },
  });
  const adapter = createStorageAdapter(throwingStorage);
  assert.equal(adapter.read(), null);
  const wrote = adapter.write('{"xp":5,"chapters":{}}');
  assert.equal(wrote, true);
  assert.equal(adapter.read(), '{"xp":5,"chapters":{}}');
});

test('createStorageAdapter uses real storage when available', () => {
  const realish = makeFakeStorage();
  const adapter = createStorageAdapter(realish);
  adapter.write('{"xp":9,"chapters":{}}');
  assert.equal(realish.getItem('dba-handbook-progress'), '{"xp":9,"chapters":{}}');
});

test('awardSceneXp adds xp once and is idempotent for the same scene', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'acid-test', 20);
  assert.equal(store.getTotalXp(), 20);
  assert.equal(store.isSceneComplete('ch01', 'acid-test'), true);
});

test('getChapterStats reports mastery once all scenes for a chapter are complete', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'two-paths', 15);
  let stats = store.getChapterStats('ch01', 4);
  assert.equal(stats.mastered, false);
  assert.equal(stats.completedScenes, 2);

  store.awardSceneXp('ch01', 'day-in-production', 20);
  store.awardSceneXp('ch01', 'mindset-check', 15);
  stats = store.getChapterStats('ch01', 4);
  assert.equal(stats.mastered, true);
  assert.equal(stats.completedScenes, 4);
});

test('getChaptersMasteredCount counts only fully mastered chapters', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'two-paths', 15);
  store.awardSceneXp('ch01', 'day-in-production', 20);
  store.awardSceneXp('ch01', 'mindset-check', 15);

  const count = store.getChaptersMasteredCount({ ch01: 4, ch02: 4 });
  assert.equal(count, 1);
});

test('progress persists across a new store instance backed by the same storage', () => {
  const storage = makeFakeStorage();
  const store1 = createProgressStore(storage);
  store1.awardSceneXp('ch01', 'acid-test', 20);

  const store2 = createProgressStore(storage);
  assert.equal(store2.getTotalXp(), 20);
  assert.equal(store2.isSceneComplete('ch01', 'acid-test'), true);
});
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `node --test tests/game/progress-store.test.js`
Expected: FAIL — `Cannot find module '../../game/progress-store.js'`

- [ ] **Step 4: Implement `game/progress-store.js`**

```js
// Pure, storage-agnostic progress tracking for the DBA Handbook interactive game.

export const STORAGE_KEY = 'dba-handbook-progress';

export function parseProgress(raw) {
  if (typeof raw !== 'string') return { xp: 0, chapters: {} };
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return { xp: 0, chapters: {} };
    return {
      xp: typeof parsed.xp === 'number' ? parsed.xp : 0,
      chapters: parsed.chapters && typeof parsed.chapters === 'object' ? parsed.chapters : {},
    };
  } catch {
    return { xp: 0, chapters: {} };
  }
}

export function serializeProgress(progress) {
  return JSON.stringify(progress);
}

export function createStorageAdapter(storageLike) {
  const probeKey = '__dba_handbook_probe__';
  let usable = false;
  try {
    storageLike.setItem(probeKey, '1');
    storageLike.removeItem(probeKey);
    usable = true;
  } catch {
    usable = false;
  }

  if (usable) {
    return {
      read() {
        try {
          return storageLike.getItem(STORAGE_KEY);
        } catch {
          return null;
        }
      },
      write(str) {
        try {
          storageLike.setItem(STORAGE_KEY, str);
          return true;
        } catch {
          return false;
        }
      },
    };
  }

  let memory = null;
  return {
    read() {
      return memory;
    },
    write(str) {
      memory = str;
      return true;
    },
  };
}

export function createProgressStore(storageLike) {
  const adapter = createStorageAdapter(storageLike);
  let progress = parseProgress(adapter.read());

  function persist() {
    adapter.write(serializeProgress(progress));
  }

  return {
    getProgress() {
      return JSON.parse(JSON.stringify(progress));
    },

    isSceneComplete(chapterId, sceneId) {
      return Boolean(progress.chapters[chapterId] && progress.chapters[chapterId][sceneId] !== undefined);
    },

    awardSceneXp(chapterId, sceneId, xp) {
      if (!progress.chapters[chapterId]) progress.chapters[chapterId] = {};
      if (progress.chapters[chapterId][sceneId] !== undefined) {
        return this.getProgress();
      }
      progress.chapters[chapterId][sceneId] = xp;
      progress.xp += xp;
      persist();
      return this.getProgress();
    },

    getChapterStats(chapterId, totalScenes) {
      const scenes = progress.chapters[chapterId] || {};
      const completedScenes = Object.keys(scenes).length;
      return {
        completedScenes,
        totalScenes,
        mastered: completedScenes >= totalScenes,
      };
    },

    getTotalXp() {
      return progress.xp;
    },

    getChaptersMasteredCount(chapterTotals) {
      return Object.entries(chapterTotals).filter(([chapterId, totalScenes]) => {
        return this.getChapterStats(chapterId, totalScenes).mastered;
      }).length;
    },
  };
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `node --test tests/game/progress-store.test.js`
Expected: PASS — all 8 tests green.

- [ ] **Step 6: Commit**

```bash
git add package.json game/progress-store.js tests/game/progress-store.test.js
git commit -m "feat(game): add localStorage-backed progress store with unit tests"
```

---

### Task 2: Chapter 1 content data

**Fact-fidelity note (ruling, added post-review):** The `acid-test` scene dramatizes the chapter's one-sentence, abstract bank-transfer example with specific dollar figures and a crash/rollback demo, neither of which is literally stated in the chapter text. A task review flagged this against the spec's "every fact traces back to the chapter" constraint. The human ruled: keep the dramatization (it's a reasonable illustration of the chapter's own example, and the interactivity depends on having concrete numbers to animate), but label it clearly as a simulation via the `simulationNote` field below, rendered in Task 3. No other scene in this chapter needed this treatment — the `two-paths` timeline and `day-in-production` vignettes are sourced near-verbatim from the chapter and require no disclaimer.

**Files:**
- Create: `game/content/ch01.js`
- Test: `tests/game/ch01-content.test.js`

**Interfaces:**
- Consumes: nothing directly (standalone data module).
- Produces (used by Tasks 4, 5):
  - `chapterId: 'ch01'`
  - `chapterTitle: string`
  - `scenes: Array<AnimationScene | ScenarioScene | QuizScene>` — exactly 4 entries, ids `'acid-test'`, `'two-paths'`, `'day-in-production'`, `'mindset-check'`, each with `id`, `type`, `title`.
    - `AnimationScene` (ids `acid-test`, `two-paths`) additionally has `xp: number` and scene-specific fields consumed by the matching renderer in Task 3. `acid-test` also has `simulationNote: string` — a disclaimer, rendered by Task 3, that the scene's dollar figures and crash/rollback moment are an illustrative simulation built on the chapter's abstract example, not a literal chapter detail (see "Fact-fidelity note" below).
    - `ScenarioScene` (`day-in-production`) has `vignettes: Array<{id, category, prompt, options: Array<{text, correct: boolean, feedback}>}>`, exactly one `correct: true` per vignette.
    - `QuizScene` (`mindset-check`) has `xpPerCorrect: number` and `questions: Array<{id, prompt, choices: string[], correctIndex: number, explanation}>`.

- [ ] **Step 1: Write the failing structural test**

Create `tests/game/ch01-content.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { scenes } from '../../game/content/ch01.js';

test('chapter 1 has exactly 4 scenes with unique ids', () => {
  assert.equal(scenes.length, 4);
  const ids = scenes.map((s) => s.id);
  assert.equal(new Set(ids).size, 4);
});

test('acid-test scene has a valid crash step index, step balances, and a simulation-note disclaimer', () => {
  const scene = scenes.find((s) => s.id === 'acid-test');
  assert.ok(scene.crashStep >= 0 && scene.crashStep < scene.steps.length);
  assert.ok(typeof scene.simulationNote === 'string' && scene.simulationNote.length > 0);
  scene.steps.forEach((step) => {
    assert.equal(typeof step.balances.a, 'number');
    assert.equal(typeof step.balances.b, 'number');
    assert.ok(step.narration.length > 0);
  });
});

test('two-paths scene has two columns with markers that all have detail text', () => {
  const scene = scenes.find((s) => s.id === 'two-paths');
  assert.equal(scene.columns.length, 2);
  scene.columns.forEach((col) => {
    assert.ok(col.markers.length > 0);
    col.markers.forEach((marker) => {
      assert.ok(marker.detail.length > 0);
    });
  });
});

test('day-in-production scenario has 4 vignettes, each with exactly one correct option', () => {
  const scene = scenes.find((s) => s.id === 'day-in-production');
  assert.equal(scene.vignettes.length, 4);
  scene.vignettes.forEach((vignette) => {
    const correctCount = vignette.options.filter((o) => o.correct).length;
    assert.equal(correctCount, 1);
    vignette.options.forEach((option) => {
      assert.ok(option.feedback.length > 0);
    });
  });
});

test('mindset-check quiz has 4 questions, each with a valid correctIndex', () => {
  const scene = scenes.find((s) => s.id === 'mindset-check');
  assert.equal(scene.questions.length, 4);
  scene.questions.forEach((q) => {
    assert.ok(q.correctIndex >= 0 && q.correctIndex < q.choices.length);
    assert.ok(q.explanation.length > 0);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tests/game/ch01-content.test.js`
Expected: FAIL — `Cannot find module '../../game/content/ch01.js'`

- [ ] **Step 3: Implement `game/content/ch01.js`**

```js
// Scene content for Chapter 1 ("Introduction") of The DBA Handbook.
// Every fact here traces back to book/ch01-introduction.html.

export const chapterId = 'ch01';
export const chapterTitle = 'Chapter 1: Introduction';

export const scenes = [
  {
    id: 'acid-test',
    type: 'animation',
    title: 'The ACID Test',
    xp: 20,
    intro: "The chapter opens with an example: when a bank transfers money between accounts, the database must guarantee the operation either fully completes or does not happen at all. Walk through it step by step.",
    simulationNote: "The dollar figures and the crash/rollback moment below are an illustrative simulation built on the chapter's own example — the chapter itself describes the guarantee abstractly, without specific numbers or a step-by-step rollback.",
    crashStep: 1,
    crashNarration: "Crash simulated after debiting A but before crediting B. Atomicity guarantees this can never be left half-done — on restart, the database rolls back: Account A returns to $500, Account B stays at $200, exactly as if the transfer never happened.",
    steps: [
      { balances: { a: 500, b: 200 }, acidLetter: null, narration: "Account A has $500. Account B has $200. You initiate a transfer of $100 from A to B." },
      { balances: { a: 400, b: 200 }, acidLetter: 'A', narration: "Atomicity: the database debits Account A first — $100 leaves A. If anything fails right now, the whole operation must roll back as if it never started." },
      { balances: { a: 400, b: 200 }, acidLetter: 'C', narration: "Consistency: before committing, the database enforces that no balance can go negative and that the total money in the system stays the same — this transfer keeps the books balanced." },
      { balances: { a: 400, b: 200 }, acidLetter: 'I', narration: "Isolation: while this transfer is in progress, another concurrent transaction reading Account A or B does not see this half-finished state — it sees either the old balances or the new ones, never a partial update." },
      { balances: { a: 400, b: 300 }, acidLetter: null, narration: "Now the database credits Account B — $100 arrives." },
      { balances: { a: 400, b: 300 }, acidLetter: 'D', narration: "Durability: once committed, this result survives even a server crash the instant after — the same promise the chapter describes for a bank transfer, an airline seat, or a hospital medication dose." },
    ],
  },
  {
    id: 'two-paths',
    type: 'animation',
    title: 'Two Paths, One Discipline',
    xp: 15,
    intro: "PostgreSQL and SQL Server represent two very different paths to the same destination: a production-grade relational database organizations can stake their business on. Click each marker to reveal how they got there.",
    sharedGround: "Both implement SQL-92 and much of SQL:2016. Both support transactions, foreign keys, triggers, views, stored procedures, partitioning, replication, and full-text search.",
    closingNarration: "This book teaches both platforms in parallel — seeing how PostgreSQL and SQL Server solve the same problem differently reveals the design decisions underneath the syntax. That comparison is itself a learning tool.",
    columns: [
      {
        key: 'postgres', name: 'PostgreSQL', color: 'blue',
        markers: [
          { year: '1980s', label: 'Berkeley research project', detail: "PostgreSQL began as a university research project at UC Berkeley in the 1980s." },
          { year: 'Ongoing', label: 'Open-source community', detail: "Grew into an open-source community effort. License costs nothing, source code is open to inspection." },
          { year: 'Ongoing', label: 'Extension ecosystem', detail: "PostGIS for geospatial data, TimescaleDB for time-series, pgvector for machine learning embeddings." },
          { year: 'Yearly', label: 'Major release cadence', detail: "A global, highly active community releases a major version every year." },
          { year: 'Today', label: 'Default for startups/SaaS', detail: "Become the default choice for startups, SaaS companies, and enterprises that want power without vendor lock-in." },
        ],
      },
      {
        key: 'sqlserver', name: 'SQL Server', color: 'purple',
        markers: [
          { year: '1989', label: 'First released by Microsoft', detail: "SQL Server is a commercial product built by Microsoft, first released in 1989." },
          { year: 'Ongoing', label: 'Windows/Azure integration', detail: "Deeply integrated with the Windows and Azure ecosystems." },
          { year: 'Historically', label: 'Enterprise dominance', detail: "Historically dominated finance, healthcare, and manufacturing — industries valuing vendor relationships and Active Directory integration." },
          { year: 'Long-standing', label: 'SSMS tooling', detail: "SQL Server Management Studio and the broader BI stack have long been a reference point for DBA tooling UX." },
          { year: 'Recent years', label: 'Linux, containers, Azure SQL', detail: "Expanded to Linux and containers; Azure SQL Database made it a viable cloud-native platform." },
        ],
      },
    ],
  },
  {
    id: 'day-in-production',
    type: 'scenario',
    title: 'A Day in Production',
    intro: "A working DBA spends far less time writing CREATE TABLE statements than most textbooks suggest. Here are four situations pulled straight from the chapter. Pick your first move.",
    vignettes: [
      {
        id: 'perf',
        category: 'Performance investigation',
        prompt: "A query that ran in 200 milliseconds yesterday now takes 45 seconds. The application team says nothing changed. What do you check first?",
        options: [
          { text: "Immediately add an index to the table involved", correct: false, feedback: "Not yet — the chapter's mindset habit is to measure before you optimize. Adding an index without knowing the cause is a guess, not a diagnosis." },
          { text: "Check whether table statistics are stale, the execution plan changed, an index is being ignored, or a lock/maintenance job is involved", correct: true, feedback: "Right. The chapter lists exactly these possibilities — stale statistics, a parameter-sniffed plan change, an ignored index, lock waits, or a background job starving disk I/O." },
          { text: "Restart the database server", correct: false, feedback: "This treats the symptom, not the cause, and risks losing the evidence (execution plan, lock state) you need to diagnose the real problem." },
        ],
      },
      {
        id: 'schema',
        category: 'Schema evolution',
        prompt: "You need to add a column to a table with 800 million rows in a live system. What's the key risk to plan around?",
        options: [
          { text: "None — adding a column is always instant and safe", correct: false, feedback: "The chapter is explicit: adding a column to a table with 800 million rows is not a trivial operation." },
          { text: "Running the migration without taking the application offline requires careful, experienced sequencing", correct: true, feedback: "Right — the chapter calls this out directly as a skill that takes real experience, especially for large tables and columns with foreign key dependencies." },
          { text: "It only matters if the column has a default value", correct: false, feedback: "Default values matter, but the chapter's point is broader: scale and live-traffic sequencing are the real risk." },
        ],
      },
      {
        id: 'capacity',
        category: 'Capacity and growth planning',
        prompt: "Your current hardware handles today's load fine. What does the chapter say good capacity planning actually requires?",
        options: [
          { text: "Knowing when current hardware will stop being sufficient and what architectural changes to make before hitting the wall", correct: true, feedback: "Right — the chapter frames this as planning ahead of the wall, not reacting after hitting it." },
          { text: "Waiting until performance visibly degrades, then reacting", correct: false, feedback: "That's the opposite of the chapter's framing — good capacity planning happens before you hit the wall, not after." },
          { text: "Buying the largest hardware available up front to avoid ever thinking about it again", correct: false, feedback: "The chapter frames this as an ongoing discipline of tracking growth trajectories, not a one-time over-purchase." },
        ],
      },
      {
        id: 'reliability',
        category: 'Reliability and recovery',
        prompt: "Someone just ran an accidental DELETE against a production table. Which capability does the chapter say you need to have already built?",
        options: [
          { text: "The ability to recover the database to a point in time before the DELETE", correct: true, feedback: "Right — the chapter lists point-in-time recovery from an accidental DELETE as a core reliability/recovery responsibility, along with tested backups and understanding replication lag." },
          { text: "A way to ask the application team what changed", correct: false, feedback: "That won't undo a DELETE. Recovery capability has to already exist before the incident." },
          { text: "Nothing — this is unrecoverable by design", correct: false, feedback: "The chapter explicitly lists recovering to a point in time after an accidental DELETE as something a DBA should be able to do." },
        ],
      },
    ],
  },
  {
    id: 'mindset-check',
    type: 'quiz',
    title: 'The Mindset Check',
    intro: "Four questions covering what you just walked through — ACID, PostgreSQL vs. SQL Server, and the mindset habits from the chapter.",
    xpPerCorrect: 5,
    questions: [
      {
        id: 'q1',
        prompt: "In the bank-transfer example, which ACID property guarantees that a transfer either completes fully or doesn't happen at all?",
        choices: ['Atomicity', 'Consistency', 'Isolation', 'Durability'],
        correctIndex: 0,
        explanation: "Atomicity is the guarantee that an operation completes fully or not at all — the chapter's exact framing for the bank transfer, airline seat, and hospital dose examples.",
      },
      {
        id: 'q2',
        prompt: "According to the chapter, which property means a committed transaction survives a server crash?",
        choices: ['Isolation', 'Durability', 'Atomicity', 'Consistency'],
        correctIndex: 1,
        explanation: "Durability guarantees a committed transaction survives a server crash.",
      },
      {
        id: 'q3',
        prompt: "Which statement matches the chapter's description of PostgreSQL and SQL Server?",
        choices: [
          'PostgreSQL is commercial and Microsoft-built; SQL Server is open-source from Berkeley',
          'PostgreSQL began as a Berkeley research project and is open-source; SQL Server is a commercial Microsoft product first released in 1989',
          'Both were first released in 1989 by Microsoft',
          'Neither supports transactions or foreign keys',
        ],
        correctIndex: 1,
        explanation: "PostgreSQL began at UC Berkeley and is open-source; SQL Server is Microsoft's commercial product, first released in 1989. Both do support transactions and foreign keys.",
      },
      {
        id: 'q4',
        prompt: 'Per "The Mindset of a Database Engineer," what should a DBA do before optimizing a performance problem?',
        choices: [
          'Immediately try the most common fix',
          'Measure first — reach for monitoring data, query plans, and wait statistics before making changes',
          'Ask the application team to guess the cause',
          'Wait until the problem happens again to be sure',
        ],
        correctIndex: 1,
        explanation: "The chapter's first habit: measure before you optimize, since assumptions about root causes are usually wrong.",
      },
    ],
  },
];
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tests/game/ch01-content.test.js`
Expected: PASS — all 5 tests green.

- [ ] **Step 5: Commit**

```bash
git add game/content/ch01.js tests/game/ch01-content.test.js
git commit -m "feat(game): add Chapter 1 scene content with structural tests"
```

---

### Task 3: Scene player (DOM rendering)

**Files:**
- Create: `game/scene-player.js`

**Interfaces:**
- Consumes: nothing from earlier tasks directly (works against any object matching the scene shapes from Task 2, and any object matching the `createProgressStore()` return shape from Task 1).
- Produces (used by Task 4):
  - `renderScene(container: HTMLElement, scene: object, onComplete: (xp: number) => void): void`
  - `mountChapterGame(root: HTMLElement, opts: { chapterId: string, scenes: object[], store: ReturnType<typeof createProgressStore> }): void`

This task has no automated test — it is DOM-rendering code with no existing DOM test harness in this repo (no jsdom, no build step, per the spec's decision to keep this project dependency-free). Verification is manual, via Task 4's page once wired up.

- [ ] **Step 1: Implement `game/scene-player.js`**

```js
// Renders Chapter 1 scenes into a container. `renderScenarioScene` and
// `renderQuizScene` are generic and reusable by any future chapter; the two
// animation scenes are custom per concept, dispatched by scene id.

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderAcidTestScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.intro));
  if (scene.simulationNote) {
    container.appendChild(el('p', 'text-xs text-gray-500 italic mb-6', scene.simulationNote));
  }

  const badgeRow = el('div', 'flex gap-2 mb-6');
  const letters = ['A', 'C', 'I', 'D'];
  const badges = {};
  letters.forEach((letter) => {
    const badge = el('span', 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold', letter);
    badges[letter] = badge;
    badgeRow.appendChild(badge);
  });
  container.appendChild(badgeRow);

  const balancesRow = el('div', 'flex gap-6 mb-6');
  const boxA = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center');
  const boxB = el('div', 'flex-1 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-center');
  boxA.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account A'));
  boxB.appendChild(el('div', 'text-xs text-gray-500 mb-1', 'Account B'));
  const balA = el('div', 'text-2xl font-bold text-white');
  const balB = el('div', 'text-2xl font-bold text-white');
  boxA.appendChild(balA);
  boxB.appendChild(balB);
  balancesRow.appendChild(boxA);
  balancesRow.appendChild(boxB);
  container.appendChild(balancesRow);

  const narration = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[4.5rem]');
  container.appendChild(narration);

  const controls = el('div', 'flex items-center gap-3');
  const crashBtn = el('button', 'px-4 py-2 rounded-lg border border-red-800/60 text-red-300 hover:bg-red-900/30 transition text-sm', 'Simulate a crash here');
  const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Next');
  controls.appendChild(crashBtn);
  controls.appendChild(nextBtn);
  container.appendChild(controls);

  let stepIndex = 0;

  function paintBadges(activeLetter) {
    letters.forEach((letter) => {
      badges[letter].className = letter === activeLetter
        ? 'px-3 py-1 rounded-full border border-blue-500 bg-blue-600/20 text-blue-300 text-sm font-bold'
        : 'px-3 py-1 rounded-full border border-gray-700 text-gray-500 text-sm font-bold';
    });
  }

  function paintStep(step) {
    balA.textContent = `$${step.balances.a}`;
    balB.textContent = `$${step.balances.b}`;
    narration.textContent = step.narration;
    paintBadges(step.acidLetter);
    crashBtn.disabled = stepIndex !== scene.crashStep;
    crashBtn.classList.toggle('opacity-30', crashBtn.disabled);
    crashBtn.classList.toggle('cursor-not-allowed', crashBtn.disabled);
  }

  function finish() {
    controls.innerHTML = '';
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
    done.addEventListener('click', () => onComplete(scene.xp));
    controls.appendChild(done);
  }

  crashBtn.addEventListener('click', () => {
    if (stepIndex !== scene.crashStep) return;
    narration.textContent = scene.crashNarration;
    balA.textContent = `$${scene.steps[0].balances.a}`;
    balB.textContent = `$${scene.steps[0].balances.b}`;
    paintBadges('A');
    finish();
  });

  nextBtn.addEventListener('click', () => {
    stepIndex += 1;
    if (stepIndex >= scene.steps.length) {
      finish();
      return;
    }
    paintStep(scene.steps[stepIndex]);
  });

  paintStep(scene.steps[0]);
}

function renderTwoPathsScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const grid = el('div', 'grid grid-cols-2 gap-6 mb-6');
  const detail = el('p', 'text-gray-200 leading-relaxed mb-6 min-h-[3rem]', 'Click any marker to reveal what it means.');
  const viewed = new Set();
  const totalMarkers = scene.columns.reduce((sum, c) => sum + c.markers.length, 0);

  const controls = el('div', 'flex items-center gap-3');

  function maybeShowContinue() {
    if (viewed.size < totalMarkers || controls.dataset.shown) return;
    controls.dataset.shown = '1';
    const continueBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm', 'Continue');
    continueBtn.addEventListener('click', () => {
      container.innerHTML = '';
      container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-4', scene.sharedGround));
      container.appendChild(el('p', 'text-gray-200 leading-relaxed mb-6', scene.closingNarration));
      const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', `Finish scene (+${scene.xp} XP)`);
      done.addEventListener('click', () => onComplete(scene.xp));
      container.appendChild(done);
    });
    controls.appendChild(continueBtn);
  }

  scene.columns.forEach((col) => {
    const colEl = el('div', '');
    colEl.appendChild(el('h4', `text-sm font-bold mb-3 text-${col.color}-300`, col.name));
    col.markers.forEach((marker) => {
      const btn = el('button', 'block w-full text-left px-3 py-2 mb-2 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300');
      btn.appendChild(el('span', 'text-xs text-gray-500 mr-2', marker.year));
      btn.appendChild(document.createTextNode(marker.label));
      btn.addEventListener('click', () => {
        detail.textContent = marker.detail;
        viewed.add(col.key + ':' + marker.label);
        maybeShowContinue();
      });
      colEl.appendChild(btn);
    });
    grid.appendChild(colEl);
  });

  container.appendChild(grid);
  container.appendChild(detail);
  container.appendChild(controls);
}

function renderScenarioScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let vignetteIndex = 0;
  let earnedXp = 0;

  function paintVignette() {
    body.innerHTML = '';
    const vignette = scene.vignettes[vignetteIndex];
    body.appendChild(el('div', 'text-xs uppercase tracking-wide text-blue-400 mb-2', vignette.category));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', vignette.prompt));

    const optionsWrap = el('div', 'space-y-2 mb-4');
    const feedback = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      vignetteIndex === scene.vignettes.length - 1 ? 'See results' : 'Next situation');

    vignette.options.forEach((option) => {
      const btn = el('button', 'block w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', option.text);
      btn.addEventListener('click', () => {
        Array.from(optionsWrap.children).forEach((c) => (c.disabled = true));
        btn.className = option.correct
          ? 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'block w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        earnedXp += option.correct ? 6 : 2;
        feedback.textContent = option.feedback;
        feedback.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
      });
      optionsWrap.appendChild(btn);
    });

    body.appendChild(optionsWrap);
    body.appendChild(feedback);

    nextBtn.addEventListener('click', () => {
      vignetteIndex += 1;
      if (vignetteIndex >= scene.vignettes.length) finish();
      else paintVignette();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You earned ${earnedXp} XP across ${scene.vignettes.length} situations.`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(earnedXp));
    body.appendChild(done);
  }

  paintVignette();
}

function renderQuizScene(container, scene, onComplete) {
  container.innerHTML = '';
  container.appendChild(el('p', 'text-gray-300 leading-relaxed mb-6', scene.intro));

  const body = el('div');
  container.appendChild(body);

  let qIndex = 0;
  let correctCount = 0;

  function paintQuestion() {
    body.innerHTML = '';
    const q = scene.questions[qIndex];
    body.appendChild(el('div', 'text-xs text-gray-500 mb-2', `Question ${qIndex + 1} of ${scene.questions.length}`));
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', q.prompt));

    const choicesWrap = el('div', 'space-y-2 mb-4');
    const explanation = el('p', 'text-gray-300 leading-relaxed mb-4 hidden');
    const nextBtn = el('button', 'px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm hidden',
      qIndex === scene.questions.length - 1 ? 'See results' : 'Next question');

    q.choices.forEach((choiceText, i) => {
      const btn = el('button', 'block w-full text-left px-4 py-3 rounded-lg border border-gray-800 bg-gray-900/40 hover:bg-gray-800/60 transition text-sm text-gray-300', choiceText);
      btn.addEventListener('click', () => {
        Array.from(choicesWrap.children).forEach((c) => (c.disabled = true));
        const isCorrect = i === q.correctIndex;
        btn.className = isCorrect
          ? 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm'
          : 'block w-full text-left px-4 py-3 rounded-lg border border-red-800 bg-red-900/20 text-red-200 text-sm';
        if (isCorrect) correctCount += 1;
        else {
          choicesWrap.children[q.correctIndex].className = 'block w-full text-left px-4 py-3 rounded-lg border border-emerald-600 bg-emerald-900/30 text-emerald-200 text-sm';
        }
        explanation.textContent = q.explanation;
        explanation.classList.remove('hidden');
        nextBtn.classList.remove('hidden');
      });
      choicesWrap.appendChild(btn);
    });

    body.appendChild(choicesWrap);
    body.appendChild(explanation);

    nextBtn.addEventListener('click', () => {
      qIndex += 1;
      if (qIndex >= scene.questions.length) finish();
      else paintQuestion();
    });
    body.appendChild(nextBtn);
  }

  function finish() {
    body.innerHTML = '';
    const xp = correctCount * scene.xpPerCorrect;
    body.appendChild(el('p', 'text-gray-200 leading-relaxed mb-4', `You got ${correctCount} of ${scene.questions.length} correct (+${xp} XP).`));
    const done = el('button', 'px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition text-sm', 'Finish scene');
    done.addEventListener('click', () => onComplete(xp));
    body.appendChild(done);
  }

  paintQuestion();
}

const ANIMATION_RENDERERS = {
  'acid-test': renderAcidTestScene,
  'two-paths': renderTwoPathsScene,
};

export function renderScene(container, scene, onComplete) {
  if (scene.type === 'animation') {
    const renderer = ANIMATION_RENDERERS[scene.id];
    if (!renderer) throw new Error(`No animation renderer registered for scene id "${scene.id}"`);
    renderer(container, scene, onComplete);
  } else if (scene.type === 'scenario') {
    renderScenarioScene(container, scene, onComplete);
  } else if (scene.type === 'quiz') {
    renderQuizScene(container, scene, onComplete);
  } else {
    throw new Error(`Unknown scene type "${scene.type}"`);
  }
}

export function mountChapterGame(root, { chapterId, scenes, store }) {
  root.innerHTML = '';

  const header = el('div', 'flex items-center justify-between mb-8');
  const xpLabel = el('div', 'text-sm text-gray-400');
  const chapterLabel = el('div', 'text-sm text-gray-400');
  header.appendChild(xpLabel);
  header.appendChild(chapterLabel);
  root.appendChild(header);

  const nav = el('div', 'flex gap-2 mb-8 flex-wrap');
  root.appendChild(nav);

  const sceneContainer = el('div', 'rounded-2xl border border-gray-800 bg-gray-900/40 p-6');
  root.appendChild(sceneContainer);

  function navButtonClass(scene, isActive) {
    if (isActive) return 'px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium';
    return store.isSceneComplete(chapterId, scene.id)
      ? 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium'
      : 'px-3 py-1.5 rounded-lg bg-gray-800 text-gray-400 text-xs font-medium hover:text-white transition';
  }

  function refreshHeader() {
    xpLabel.textContent = `⚡ ${store.getTotalXp()} XP`;
    const stats = store.getChapterStats(chapterId, scenes.length);
    chapterLabel.textContent = stats.mastered
      ? 'Chapter mastered ✓'
      : `${stats.completedScenes} / ${stats.totalScenes} scenes complete`;
  }

  function selectScene(scene) {
    Array.from(nav.children).forEach((btn) => {
      btn.className = navButtonClass(scene, btn.dataset.sceneId === scene.id);
    });
    renderScene(sceneContainer, scene, (xp) => {
      store.awardSceneXp(chapterId, scene.id, xp);
      refreshHeader();
      const navBtn = Array.from(nav.children).find((btn) => btn.dataset.sceneId === scene.id);
      if (navBtn) navBtn.className = 'px-3 py-1.5 rounded-lg bg-gray-800 text-emerald-300 text-xs font-medium';
    });
  }

  scenes.forEach((scene) => {
    const btn = el('button', navButtonClass(scene, false), scene.title);
    btn.dataset.sceneId = scene.id;
    btn.addEventListener('click', () => selectScene(scene));
    nav.appendChild(btn);
  });

  refreshHeader();
  selectScene(scenes[0]);
}
```

- [ ] **Step 2: Commit**

```bash
git add game/scene-player.js
git commit -m "feat(game): add scene player rendering animation, scenario, and quiz scenes"
```

---

### Task 4: Chapter 1 game page

**Files:**
- Create: `game/ch01.html`

**Interfaces:**
- Consumes: `createProgressStore` from `game/progress-store.js` (Task 1), `mountChapterGame` from `game/scene-player.js` (Task 3), `chapterId`/`scenes` from `game/content/ch01.js` (Task 2).
- Produces: a working page at `game/ch01.html`, linked to from Task 5 and Task 6.

- [ ] **Step 1: Create `game/ch01.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Play Chapter 1: Introduction — The DBA Handbook</title>
  <meta name="description" content="Interactive game version of Chapter 1 of The DBA Handbook — animated ACID walkthrough, PostgreSQL vs SQL Server timeline, a production scenario challenge, and a mindset quiz." />
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 font-sans antialiased">
  <nav class="fixed top-0 left-0 right-0 z-50 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-md">
    <div class="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
      <a href="../index.html" class="flex items-center gap-2 group">
        <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
        </div>
        <span class="text-sm font-bold text-white group-hover:text-blue-300 transition">Rajesh Guntupalli</span>
      </a>
      <div class="flex items-center gap-1 text-xs">
        <a href="../index.html" class="px-3 py-1.5 text-gray-400 hover:text-white hover:bg-gray-800/60 rounded-md transition">Home</a>
        <a href="../book.html" class="px-3 py-1.5 text-gray-400 hover:text-white hover:bg-gray-800/60 rounded-md transition">Books</a>
        <a href="index.html" class="px-3 py-1.5 text-white bg-gray-800 rounded-md">Play</a>
      </div>
    </div>
  </nav>

  <main class="pt-28 pb-24 px-6 max-w-3xl mx-auto">
    <div class="mb-6">
      <a href="../book/ch01-introduction.html" class="text-xs text-blue-400 hover:text-blue-300 transition">← Read this chapter as text</a>
    </div>
    <div class="flex items-center gap-3 mb-8">
      <span class="px-2.5 py-1 bg-blue-900/40 border border-blue-800/40 text-blue-300 text-xs rounded-full font-medium">Chapter 1 of 40</span>
      <h1 class="text-xl font-bold text-white">Chapter 1: Introduction — Interactive</h1>
    </div>
    <div id="game-root"></div>
  </main>

  <script type="module">
    import { createProgressStore } from './progress-store.js';
    import { mountChapterGame } from './scene-player.js';
    import { chapterId, scenes } from './content/ch01.js';

    const store = createProgressStore(window.localStorage);
    mountChapterGame(document.getElementById('game-root'), { chapterId, scenes, store });
  </script>
</body>
</html>
```

- [ ] **Step 2: Manual verification**

Serve the repo root with any static file server (e.g. `npx serve .` or `python -m http.server`) and open `/game/ch01.html`:
- All 4 scene tabs are visible and clickable.
- "The ACID Test": the `simulationNote` disclaimer is visible below the intro before any steps are taken; clicking Next steps through all 6 steps with balances/narration updating; clicking "Simulate a crash here" only works on the debit step and shows the rollback narration; either path ends with a "Finish scene (+20 XP)" button that updates the XP counter in the header and turns that scene's tab green.
- "Two Paths, One Discipline": clicking all 10 markers reveals their detail text; after all are viewed, "Continue" appears and finishing awards +15 XP.
- "A Day in Production": each of the 4 vignettes shows feedback after a choice is picked, and the scene finishes with a total XP summary.
- "The Mindset Check": each of the 4 questions shows the correct answer highlighted plus an explanation, and finishes with a score summary.
- Reload the page: header XP total and green tab states persist (backed by `localStorage`).

- [ ] **Step 3: Commit**

```bash
git add game/ch01.html
git commit -m "feat(game): add Chapter 1 interactive game page"
```

---

### Task 5: Game landing page

**Files:**
- Create: `game/index.html`

**Interfaces:**
- Consumes: `createProgressStore` from `game/progress-store.js` (Task 1).
- Produces: a working page at `game/index.html`, linked to from Task 6.

- [ ] **Step 1: Create `game/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Play — The DBA Handbook Interactive</title>
  <meta name="description" content="Play through The DBA Handbook chapter by chapter — animated concept walkthroughs, production scenarios, and quizzes." />
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-gray-100 font-sans antialiased">
  <nav class="fixed top-0 left-0 right-0 z-50 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-md">
    <div class="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
      <a href="../index.html" class="flex items-center gap-2 group">
        <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
        </div>
        <span class="text-sm font-bold text-white group-hover:text-blue-300 transition">Rajesh Guntupalli</span>
      </a>
      <div class="flex items-center gap-1 text-xs">
        <a href="../index.html" class="px-3 py-1.5 text-gray-400 hover:text-white hover:bg-gray-800/60 rounded-md transition">Home</a>
        <a href="../book.html" class="px-3 py-1.5 text-gray-400 hover:text-white hover:bg-gray-800/60 rounded-md transition">Books</a>
        <a href="index.html" class="px-3 py-1.5 text-white bg-gray-800 rounded-md">Play</a>
      </div>
    </div>
  </nav>

  <main class="pt-28 pb-24 px-6 max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-white mb-2">The DBA Handbook — Interactive</h1>
    <p class="text-gray-400 text-sm mb-8" id="progress-summary">Loading progress…</p>
    <div class="rounded-2xl border border-gray-800 bg-gray-900/40 p-5 flex items-center justify-between">
      <div>
        <div class="text-white font-semibold mb-1">Chapter 1: Introduction</div>
        <div class="text-gray-500 text-xs" id="ch01-status">Not started</div>
      </div>
      <a href="ch01.html" class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition text-sm">Play →</a>
    </div>
  </main>

  <script type="module">
    import { createProgressStore } from './progress-store.js';

    const store = createProgressStore(window.localStorage);
    const stats = store.getChapterStats('ch01', 4);

    document.getElementById('progress-summary').textContent =
      `⚡ ${store.getTotalXp()} XP · ${store.getChaptersMasteredCount({ ch01: 4 })} / 1 chapters mastered so far`;

    document.getElementById('ch01-status').textContent = stats.mastered
      ? 'Mastered ✓'
      : stats.completedScenes > 0
        ? `${stats.completedScenes} / ${stats.totalScenes} scenes complete`
        : 'Not started';
  </script>
</body>
</html>
```

- [ ] **Step 2: Manual verification**

Open `/game/index.html`:
- Before playing: shows "0 XP · 0 / 1 chapters mastered so far" and "Not started".
- After completing all 4 scenes on `/game/ch01.html` and returning: shows the accumulated XP total, "1 / 1 chapters mastered so far", and "Mastered ✓".

- [ ] **Step 3: Commit**

```bash
git add game/index.html
git commit -m "feat(game): add game landing page listing playable chapters"
```

---

### Task 6: Discoverability links on book.html and book/index.html

**Files:**
- Modify: `book.html:218-219`
- Modify: `book/index.html:40`

**Interfaces:**
- Consumes: `game/index.html` (Task 5) and `game/ch01.html` (Task 4) as link targets.
- Produces: nothing consumed by later tasks (final integration point).

- [ ] **Step 1: Add a "Play" link to `book.html`**

In `book.html`, the DBA Handbook card's action-button row currently ends with (around line 214-223):

```html
            <a href="downloads/The-DBA-Handbook.pdf" download
               class="px-7 py-3 border border-blue-700/60 hover:border-blue-400 text-blue-300 hover:text-white font-semibold rounded-xl text-sm transition text-center flex items-center justify-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download PDF
            </a>
            <a href="http://localhost:5175" target="_blank"
               class="px-7 py-3 border border-blue-700/60 hover:border-blue-400 text-blue-300 hover:text-white font-semibold rounded-xl text-sm transition text-center flex items-center justify-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
              Study with AI Quizzes
            </a>
```

Insert a new link between the "Download PDF" `</a>` and the "Study with AI Quizzes" `<a>` (do not modify or remove the existing "Study with AI Quizzes" link — it is an unrelated, already-existing element, out of scope for this plan):

```html
            <a href="game/ch01.html"
               class="px-7 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-sm transition text-center flex items-center justify-center gap-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Play Chapter 1 (Interactive)
            </a>
```

- [ ] **Step 2: Add a "Play" link to `book/index.html`**

In `book/index.html`, the chapter 1 row currently reads (line 40):

```html
<a href="ch01-introduction.html" class="flex items-center gap-4 p-4 bg-gray-900/60 border border-gray-800 rounded-xl hover:border-blue-700/50 hover:bg-gray-900 transition group"><span class="w-8 h-8 shrink-0 rounded-lg bg-blue-900/40 border border-blue-800/40 text-blue-300 text-xs font-bold flex items-center justify-center">1</span><span class="text-sm text-gray-200 group-hover:text-white transition">Introduction</span><span class="ml-auto text-xs text-blue-400">Read →</span></a>
```

Replace it with the same row plus an adjacent "Play" pill link (the existing `<a>` element and its contents are unchanged; only a sibling `<a>` is added after it):

```html
<a href="ch01-introduction.html" class="flex items-center gap-4 p-4 bg-gray-900/60 border border-gray-800 rounded-xl hover:border-blue-700/50 hover:bg-gray-900 transition group"><span class="w-8 h-8 shrink-0 rounded-lg bg-blue-900/40 border border-blue-800/40 text-blue-300 text-xs font-bold flex items-center justify-center">1</span><span class="text-sm text-gray-200 group-hover:text-white transition">Introduction</span><span class="ml-auto text-xs text-blue-400">Read →</span></a>
<a href="../game/ch01.html" class="flex items-center justify-center gap-1.5 p-2 mt-1 mb-2 bg-emerald-900/20 border border-emerald-700/40 text-emerald-300 text-xs font-medium rounded-lg hover:bg-emerald-900/40 transition">▶ Play the interactive version</a>
```

- [ ] **Step 3: Manual verification**

- Open `book.html`, scroll to the DBA Handbook card, confirm the new green "Play Chapter 1 (Interactive)" button appears and links to `game/ch01.html`; confirm "Download PDF" and "Study with AI Quizzes" links are unchanged.
- Open `book/index.html`, confirm chapter 1's row still links to `ch01-introduction.html` unchanged, and the new "▶ Play the interactive version" pill appears below it and links to `../game/ch01.html`.
- Run `git diff book.html book/index.html` and confirm only additive `<a>` elements were inserted — no existing lines were altered or removed.
- Run `git status` and confirm no file under `book/` other than `book/index.html` shows as modified, and no file under `book2/`–`book7/` is touched.

- [ ] **Step 4: Commit**

```bash
git add book.html book/index.html
git commit -m "feat(game): link the interactive Chapter 1 game from the books pages"
```

---

### Task 7: Full end-to-end verification pass

**Files:** none (verification only, per the spec's "Testing / verification" checklist).

- [ ] **Step 1: Run the full automated test suite**

Run: `node --test`
Expected: PASS — all tests from Tasks 1 and 2 green (13 tests total).

- [ ] **Step 2: Manual smoke test in a private/incognito window**

With `localStorage` behaving normally: play through all 4 scenes on `/game/ch01.html` start to finish, confirm the running XP total in the header increases after each scene, confirm `/game/index.html` reflects "Mastered ✓" afterward, and confirm a page reload mid-chapter preserves progress already earned.

- [ ] **Step 3: Confirm the localStorage-unavailable fallback**

In a browser dev console on `/game/ch01.html`, run:

```js
Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });
```

Then reload and complete one scene — the game should run normally (no crash), just without persisting across reloads, because `createProgressStore` falls back to its in-memory adapter when `storageLike.setItem` throws.

- [ ] **Step 4: Fact-check every claim against the chapter source**

Open `book/ch01-introduction.html` side by side with `game/content/ch01.js`. For each of the 4 scenes, confirm every narration line, marker detail, vignette prompt/feedback, and quiz question/explanation is directly traceable to one of the chapter's five sections (ACID/relational model, PostgreSQL vs. SQL Server, what DBAs do, how to read the book, the mindset habits) — no invented facts, dates, or claims. This spec requirement is satisfied by construction (Task 2's content was authored directly from quoted chapter text), but re-check it here as a final gate before calling the pilot done.

- [ ] **Step 5: Final diff review**

Run `git diff main --stat` (or `git log --stat` over this plan's commits) and confirm the only files touched across all commits are: `package.json`, everything under `game/`, everything under `tests/game/`, `book.html`, `book/index.html`, and the two docs files from the spec/plan. No file under `book/ch*.html` or `book2/`–`book7/` appears.

- [ ] **Step 6: Commit the plan status (if any fixes were needed during verification)**

If Steps 1-4 required any fixes, commit them individually with descriptive messages before considering this task complete. If no fixes were needed, no commit is required for this task.
