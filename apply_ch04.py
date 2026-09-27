#!/usr/bin/env python3
"""Apply ch04 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch04-data-flow.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'

REPLACEMENTS = [
# --- B1: buffer layer intro ---
("""Both PostgreSQL and SQL Server sit a layer of abstraction above raw disk I/O. When a query reads rows, those pages are pulled from disk into memory — PostgreSQL calls this the shared buffer cache, SQL Server calls it the buffer pool. Writes don't go directly to disk either; they go to memory first, then are flushed to disk asynchronously based on checkpoint and write-ahead log (WAL) activity.""",
 """SQL Server sits a layer of abstraction above raw disk I/O. When a query reads rows, those pages are pulled from disk into the buffer pool. Writes don't go directly to disk either; they go to memory first, then are flushed to disk asynchronously by checkpoint activity — while every change is first recorded in the transaction log."""),
("""A naive bulk load that inserts rows one at a time forces thousands of individual page allocations and WAL entries.""",
 """A naive bulk load that inserts rows one at a time forces thousands of individual page allocations and transaction log records."""),

# --- B3: WAL terminology ---
("""The WAL (or transaction log in SQL Server's terminology) is particularly important here.""",
 """The transaction log is particularly important here."""),

# --- B4: log traffic ---
("""will generate far more WAL/log activity than the raw byte count of the data would suggest.""",
 """will generate far more transaction log activity than the raw byte count of the data would suggest."""),

# --- B5: bulk loading intro ---
("""The fastest way to move large amounts of data into a PostgreSQL or SQL Server database is to use the native bulk loading tools, not row-by-row INSERT statements from application code. Both platforms have dedicated mechanisms for this, and the performance difference can be several orders of magnitude.""",
 """The fastest way to move large amounts of data into a SQL Server database is to use the native bulk loading tools, not row-by-row INSERT statements from application code. SQL Server's BULK INSERT statement, the bcp command-line utility, and SSIS bulk destinations are dedicated mechanisms for this, and the performance difference can be several orders of magnitude."""),

# --- B6: COPY -> BULK INSERT deepening ---
("""In PostgreSQL, the COPY command is the workhorse of bulk loading. It reads data from a file or from standard input (including pipe input from another process) and loads it directly into a table with much less overhead than row-by-row INSERT statements from a client, mainly by avoiding per-statement parsing, planning, and network round-trip costs. Row-level triggers and per-row constraint checks (NOT NULL, CHECK, foreign keys) still fire the same way they do for INSERT. One genuine WAL optimization does apply: when the target table was created or truncated earlier in the same transaction and <code class="BG">wal_level</code> is <code class="BG">minimal</code>, PostgreSQL can skip most WAL logging for the load, because a crash would simply discard the whole transaction rather than needing to replay it.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, <strong class="text-white">BULK INSERT</strong> is the workhorse of bulk loading. It reads data from a file and loads it directly into a table with far less overhead than row-by-row INSERT statements — mainly by avoiding per-statement parsing, compilation, and network round-trip costs. The <strong class="text-white">bcp</strong> command-line utility does the same job from outside the engine and adds format files for fixed-width or delimited layouts. Row-level triggers and per-row constraint checks (NOT NULL, CHECK, foreign keys) still fire the same way they do for INSERT, unless you explicitly disable them — a decision to make deliberately, never accidentally. One genuine logging optimization applies: with the <code class="BG">TABLOCK</code> hint against an empty table (or an empty partition) in the SIMPLE or BULK_LOGGED recovery model, SQL Server can minimally log the load — writing only extent allocations to the log instead of every row — which is often an order of magnitude faster and keeps the transaction log from exploding mid-load.""".replace('class="BG"', 'class="%s"' % C)),

# --- B7: index drop before load ---
("""In PostgreSQL, if you're loading into a table that currently has no data (a fresh load), dropping indexes before the load and recreating them afterward is almost always faster than maintaining them during the insert.""",
 """If you're loading into a table that currently has no data (a fresh load), dropping nonclustered indexes before the load and recreating them afterward is almost always faster than maintaining them during the insert."""),

# --- B8: ELT environments ---
("""but it works equally well in traditional PostgreSQL and SQL Server environments, especially as servers have grown more powerful and storage has become cheaper.""",
 """but it works equally well in SQL Server environments, especially as servers have grown more powerful and storage has become cheaper."""),

# --- B9: ELT lead-in ---
("""A typical ELT pattern in PostgreSQL might look like this:""",
 """A typical ELT pattern in SQL Server might look like this:"""),

# --- B10: CDC intro ---
("""Both PostgreSQL and SQL Server have native CDC mechanisms, and both are based on reading the transaction log rather than querying the actual tables.""",
 """SQL Server has native CDC mechanisms based on reading the transaction log rather than querying the actual tables."""),

# --- B11: PG logical replication -> SQL Server CDC ---
("""<strong class="text-white">PostgreSQL logical replication and decoding</strong> are the foundation of CDC in PostgreSQL. The server can be configured to publish changes from specific tables, and consumers (replication slots) can subscribe to that stream. Tools like Debezium connect to PostgreSQL's logical replication slot and translate the binary log stream into structured events (typically JSON on Kafka), which downstream systems consume.""",
 """<strong class="text-white">SQL Server Change Data Capture</strong> tracks inserts, updates, and deletes by having a capture job read the transaction log and write row versions to change tables you query with functions like <code class="BG">cdc.fn_cdc_get_all_changes_...</code>. For lighter-weight "what changed" tracking, <strong class="text-white">change tracking</strong> records only primary keys and version numbers — enough for synchronization without the storage cost of full row history. Tools like Debezium can tail SQL Server's CDC change tables and translate them into structured events (typically JSON on Kafka) for downstream consumers.""".replace('class="BG"', 'class="%s"' % C)),

# --- B12: logical replication lead-in ---
("""To enable and inspect logical replication in PostgreSQL:""",
 """To enable and inspect Change Data Capture in SQL Server:"""),

# --- B13: replication slot lag -> CDC capture lag ---
("""The most common production issue with CDC pipelines is <strong class="text-white">replication lag</strong> in PostgreSQL. If a replication slot's consumer is slow — maybe Debezium is restarting, or Kafka is backed up — PostgreSQL cannot discard WAL segments that the slot still needs. If this goes unchecked, the WAL directory fills up and the primary can become unavailable. Every DBA running logical replication should have an alert on replication slot lag. If it exceeds a defined threshold (often measured in bytes of WAL retained, or time delay), the on-call engineer should be paged.""",
 """The most common production issue with CDC pipelines is an unconsumed change backlog. SQL Server's capture job scans the transaction log continuously; if the job falls behind or stops — a SQL Agent job disabled during maintenance, a downstream consumer backed up for hours — the transaction log cannot truncate past the CDC scan point and grows until the disk fills and every write in the database halts. Every DBA running CDC should alert on capture job latency and watch <code class="BG">sys.databases.log_reuse_wait_desc</code> for a <code class="BG">REPLICATION</code> value. If the log starts growing because CDC cannot keep up, the on-call engineer should be paged.""".replace('class="BG"', 'class="%s"' % C)),

# --- B14: upsert ---
("""The most direct way to achieve idempotency in SQL is through upserts — the PostgreSQL <code class="BG">ON CONFLICT DO UPDATE</code> and the SQL Server <code class="BG">MERGE</code> statement shown earlier.""".replace('class="BG"', 'class="%s"' % C),
 """The most direct way to achieve idempotency in SQL is through upserts — the SQL Server <code class="BG">MERGE</code> statement shown earlier.""".replace('class="BG"', 'class="%s"' % C)),

# --- B15: pg_stat_activity ---
("""In PostgreSQL, <code class="BG">pg_stat_activity</code> lets you see active pipeline queries. In SQL Server, <code class="BG">sys.dm_exec_requests</code> combined with <code class="BG">sys.dm_exec_sql_text</code> serves the same purpose. Both platforms expose query duration and wait states, which makes it possible to determine whether a slow pipeline is blocked on locks, waiting on I/O, or simply doing more CPU-intensive work than expected.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, <code class="BG">sys.dm_exec_requests</code> combined with <code class="BG">sys.dm_exec_sql_text</code> lets you see active pipeline queries along with their wait states — which makes it possible to determine whether a slow pipeline is blocked on locks, waiting on I/O, or simply doing more CPU-intensive work than expected.""".replace('class="BG"', 'class="%s"' % C)),

# --- B16: partitioning ---
("""<strong class="text-white">Partition-aware loading</strong> is one of the highest-leverage techniques in large-scale pipelines. Both PostgreSQL and SQL Server support table partitioning, and when bulk loads target a specific partition (or set of partitions), the database can skip constraint checking and index maintenance on other partitions entirely.""",
 """<strong class="text-white">Partition-aware loading</strong> is one of the highest-leverage techniques in large-scale pipelines. SQL Server supports table partitioning, and when bulk loads target a specific partition (or set of partitions), the database can skip constraint checking and index maintenance on other partitions entirely."""),

# --- B17: partition elimination lead-in ---
("""In PostgreSQL, partition elimination applies automatically when your load targets rows that fall into a single partition range. You can verify this with <code class="BG">EXPLAIN ANALYZE</code>:""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, partition elimination applies automatically when your load targets rows that fall into a single partition range. You can verify it in the actual execution plan — look for a partitioned range scan with a seek predicate on the partitioning column rather than a scan touching every partition:"""),

# --- B18: parallelism ---
("""<strong class="text-white">Parallelism</strong> is another lever. Both PostgreSQL and SQL Server can parallelize query execution, and both can be tuned to use parallelism more or less aggressively for pipeline workloads. PostgreSQL's <code class="BG">max_parallel_workers_per_gather</code> and <code class="BG">parallel_tuple_cost</code> settings influence whether the planner chooses parallel plans for INSERT...SELECT and similar operations. SQL Server's <code class="BG">MAXDOP</code> hint or configuration setting controls degree of parallelism.""".replace('class="BG"', 'class="%s"' % C),
 """<strong class="text-white">Parallelism</strong> is another lever. SQL Server parallelizes query execution across worker threads, governed by the <code class="BG">MAXDOP</code> hint or the server-level max degree of parallelism setting, with cost threshold for parallelism deciding which queries qualify. For <code class="BG">INSERT...SELECT</code> pipeline work, parallelism can multiply throughput — but on a busy OLTP instance, an aggressive parallel load will steal schedulers from latency-sensitive queries, so schedule heavy pipeline parallelism in maintenance windows or cap it with <code class="BG">MAXDOP</code> hints.""".replace('class="BG"', 'class="%s"' % C)),

# --- B19: compression ---
("""Compressed tables in PostgreSQL (using <code class="BG">TOAST</code> for large columns) and SQL Server (row or page compression) store less data on disk, meaning that bulk loads write fewer pages — which is faster.""".replace('class="BG"', 'class="%s"' % C),
 """Compressed tables in SQL Server (row or page compression, columnstore for analytics) store less data on disk, meaning that bulk loads write fewer pages — which is faster."""),

# --- takeaways ---
("""Native bulk load tools (`COPY` in PostgreSQL, `BULK INSERT` in SQL Server) can be orders of magnitude faster than row-by-row inserts; staging tables with no indexes or constraints are the right landing zone for high-volume loads.""",
 """Native bulk load tools (`BULK INSERT`, `bcp`) can be orders of magnitude faster than row-by-row inserts; staging tables with no indexes or constraints are the right landing zone for high-volume loads, and `TABLOCK` with minimal logging keeps the transaction log from exploding mid-load."""),

("""CDC (Change Data Capture) is log-based and carries minimal overhead on the source database, but requires monitoring for lag — unmonitored replication slot lag in PostgreSQL can fill disk and take down the primary server.""",
 """CDC (Change Data Capture) is log-based and carries minimal overhead on the source database, but requires monitoring for lag — an unconsumed CDC backlog prevents log truncation, fills the disk, and halts all writes."""),

# --- leftover: change data capture heading area check (CDC vs Debezium PG mention) ---
]

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch04: all {len(REPLACEMENTS)} replacements applied')

main()
