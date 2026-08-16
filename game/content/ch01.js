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
