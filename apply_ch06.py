#!/usr/bin/env python3
"""Apply ch06 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch06-indexing.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'

REPLACEMENTS = [
# --- B1 intro ---
("""Both PostgreSQL and SQL Server are covered throughout, because while the concepts overlap significantly, the implementation details diverge in ways that matter in production.""",
 """The concepts are universal but the implementation details are SQL Server's throughout — and those details are what matter in production."""),

# --- B2 B-tree default ---
("""The default index type in both PostgreSQL and SQL Server is the B-tree (balanced tree).""",
 """The default index type in SQL Server is the B-tree (balanced tree)."""),
("""Each leaf node contains index entries and a pointer to the corresponding heap row (PostgreSQL) or row locator (SQL Server).""",
 """Each leaf node contains index entries and a pointer to the corresponding row locator — the clustered index key, or the RID for a heap."""),

# --- B3 pages ---
("""both databases store the index in pages (8KB by default in PostgreSQL, also 8KB by default in SQL Server).""",
 """SQL Server stores indexes in 8KB pages."""),

# --- B4 CLUSTER comparison -> key lookup deepening ---
("""In PostgreSQL, there is no native clustered index in the SQL Server sense. The <code class="BG">CLUSTER</code> command physically reorders a table's heap pages to match an index, but this ordering is not maintained on subsequent writes — it's a one-time operation, not an ongoing constraint.""".replace('class="BG"', 'class="%s"' % C),
 """A nonclustered index seek followed by a key lookup into the clustered index is the most common plan shape in OLTP — and the tipping point, where the optimizer abandons seek-plus-lookup for a straight scan, is exactly what covering indexes and <code class="BG">INCLUDE</code> columns exist to move in your favor.""".replace('class="BG"', 'class="%s"' % C)),

# --- B5 heap fetch comparison -> tipping point ---
("""This distinction has real consequences. In SQL Server, a range scan on the clustered index reads contiguous data pages, which is extremely efficient. In PostgreSQL, a range scan using any index must follow heap pointers from index leaf entries back to the heap, which may involve random I/O across many heap pages — a pattern PostgreSQL calls a heap fetch, and the cost of which depends heavily on how physically ordered the heap already is (tracked as the <strong class="text-white">correlation</strong> statistic in <code class="BG">pg_stats</code>).""".replace('class="BG"', 'class="%s"' % C),
 """This distinction has real consequences. A range scan on the clustered index reads contiguous data pages, which is extremely efficient. A nonclustered index seek that must then perform key lookups into the clustered index for each row pays random I/O per row — cheap for ten rows, ruinous for ten million. The optimizer's tipping-point math between seek-plus-lookup and a straight scan is driven by statistics, which is why stale statistics so often manifest as "the index is being ignored"."""),

# --- B6 optimizer ---
("""Both PostgreSQL and SQL Server use cost-based query optimizers that estimate the total cost of different execution plans and choose the cheapest one.""",
 """SQL Server uses a cost-based query optimizer that estimates the total cost of different execution plans and chooses the cheapest one."""),

# --- B7 statistics ---
("""In PostgreSQL, the <code class="BG">ANALYZE</code> command gathers these statistics and stores them in <code class="BG">pg_statistic</code>, exposed through the view <code class="BG">pg_stats</code>. In SQL Server, statistics are gathered automatically by default and stored in objects accessible via <code class="BG">sys.stats</code> and viewable with <code class="BG">DBCC SHOW_STATISTICS</code>.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, statistics are gathered automatically by default and stored in objects accessible via <code class="BG">sys.stats</code> and viewable with <code class="BG">DBCC SHOW_STATISTICS</code> — including the 200-step histogram the optimizer actually reasons with when it estimates how many rows your predicate will return.""".replace('class="BG"', 'class="%s"' % C)),

# --- B8 EXPLAIN ---
("""The <code class="BG">EXPLAIN</code> (PostgreSQL) and execution plan (SQL Server) outputs reveal what the planner chose and why. Reading these plans is one of the most important skills a DBA develops. The plan shows whether an index scan, index-only scan, bitmap index scan, or sequential scan was used, what the estimated vs. actual row counts were, and where in the plan execution time is concentrated.""".replace('class="BG"', 'class="%s"' % C),
 """Execution plan output reveals what the optimizer chose and why. Reading actual execution plans is one of the most important skills a DBA develops. The plan shows whether an index seek, index scan, key lookup, or table scan was used, what the estimated vs. actual row counts were, and where in the plan execution time is concentrated."""),

# --- B9 culprits ---
("""the common culprits are stale statistics, parameter sniffing (SQL Server), or plan caching effects. Running <code class="BG">ANALYZE</code> (PostgreSQL) or <code class="BG">UPDATE STATISTICS</code> (SQL Server) after significant data changes is often the first thing to try.""".replace('class="BG"', 'class="%s"' % C),
 """the common culprits are stale statistics, parameter sniffing, or plan caching effects. Running <code class="BG">UPDATE STATISTICS</code> after significant data changes is often the first thing to try.""".replace('class="BG"', 'class="%s"' % C)),

# --- B10 forcing mechanisms ---
("""PostgreSQL's <code class="BG">enable_indexscan</code> and <code class="BG">enable_seqscan</code> configuration parameters let you force the planner one way or another for testing purposes. In SQL Server, you can use query hints (<code class="BG">WITH (INDEX(...))</code>) to test the same. Never leave these forcing mechanisms in production code — use them only for investigation, then fix the underlying cause (usually statistics, index design, or the query itself).""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, you can use query hints (<code class="BG">WITH (INDEX(...))</code>, <code class="BG">OPTION (RECOMPILE)</code>, <code class="BG">OPTIMIZE FOR</code>) to test alternatives for investigation purposes. Never leave these forcing mechanisms in production code — use them only for diagnosis, then fix the underlying cause (usually statistics, index design, or the query itself).""".replace('class="BG"', 'class="%s"' % C)),

# --- B11 CONCURRENTLY -> ONLINE ---
("""In PostgreSQL, the <code class="BG">CREATE INDEX CONCURRENTLY</code> option builds the index without taking a full table lock. The build happens in multiple passes: first, it scans the table without blocking writes; then, it processes changes that occurred during the first scan; finally, it validates the index. The downside is that the build takes longer, and if the process is interrupted, it leaves behind an invalid index that must be manually dropped. Always check <code class="BG">pg_indexes</code> or <code class="BG">pg_stat_user_indexes</code> after a concurrent build to confirm the index is valid.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, <code class="BG">CREATE INDEX ... WITH (ONLINE = ON)</code> builds the index without taking a long-term table lock (Enterprise edition), letting reads and writes continue during the build. The build takes longer, uses more tempdb, and still needs brief locks at the start and end of the operation — so schedule large builds with that in mind. For very large tables, <strong class="text-white">resumable</strong> index builds (<code class="BG">WITH (ONLINE = ON, RESUMABLE = ON)</code>) let a multi-hour build be paused and resumed across maintenance windows instead of starting over when the window closes.""".replace('class="BG"', 'class="%s"' % C)),

# --- B12 maintenance strategy ---
("""In SQL Server, the standard guidance is to reorganize indexes with 10–30% fragmentation (a lightweight, online operation that defragments leaf pages in place) and rebuild indexes above 30% (which rewrites the entire index, reclaims space, and updates statistics). In PostgreSQL, index bloat is addressed with <code class="BG">REINDEX</code> or <code class="BG">REINDEX CONCURRENTLY</code> (PostgreSQL 12+). The autovacuum process helps prevent table bloat but doesn't rebuild indexes — periodic <code class="BG">REINDEX CONCURRENTLY</code> is still necessary for heavily updated tables.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, the standard guidance is to reorganize indexes with 10–30% fragmentation (a lightweight, online operation that defragments leaf pages in place) and rebuild indexes above 30% (which rewrites the entire index, reclaims space, and refreshes statistics with a full scan). Ola Hallengren's IndexOptimize remains the community-standard implementation — it encodes the rebuild-vs-reorganize decision, the online options, and statistics updates as one maintained solution rather than hand-rolled Agent jobs you have to debug at 2 a.m."""),

# --- B13 fill factor ---
("""A fill factor of 80 (SQL Server) or <code class="BG">fillfactor = 80</code> (PostgreSQL) leaves 20% of each page empty, providing room for future insertions without immediate page splits.""".replace('class="BG"', 'class="%s"' % C),
 """A fill factor of 80 leaves 20% of each page empty, providing room for future insertions without immediate page splits."""),

# --- B14 specialized intro ---
("""B-tree indexes handle the majority of workloads, but both PostgreSQL and SQL Server offer specialized index types that dramatically outperform B-trees for specific access patterns.""",
 """B-tree indexes handle the majority of workloads, but SQL Server offers specialized index types that dramatically outperform B-trees for specific access patterns."""),

# --- B15 hash indexes ---
("""In PostgreSQL, hash indexes store a hash of the indexed value and support only equality lookups — no ranges, no ordering, no LIKE. Before PostgreSQL 10, hash indexes were not WAL-logged and were unsafe for crash recovery. Since PostgreSQL 10, they are fully crash-safe and can be a good choice for equality-only lookups on wide columns (like long strings), since the hash reduces the index entry size. SQL Server also supports hash indexes, but only for memory-optimized (In-Memory OLTP) tables, where they are the dominant index type for equality access on in-memory data.""",
 """<strong class="text-white">Hash indexes</strong> store a hash of the indexed value and support only equality lookups — no ranges, no ordering. In SQL Server they exist for memory-optimized (In-Memory OLTP) tables, where they are the dominant index type for point lookups on in-memory data. The critical tuning knob is <code class="BG">bucket_count</code>: too few buckets creates long hash chains that serialize lookups, too many wastes memory — size it at roughly 1–2x the expected row count, and monitor for empty vs. chained buckets.""".replace('class="BG"', 'class="%s"' % C)),




# --- B19 filtered ---
("""Both PostgreSQL and SQL Server support partial indexes (called filtered indexes in SQL Server). A partial index is built only over rows that satisfy a WHERE condition. This is one of the most powerful indexing techniques available, and it's underused in most production systems.""",
 """SQL Server supports <strong class="text-white">filtered indexes</strong> — built only over rows that satisfy a <code class="BG">WHERE</code> condition. This is one of the most powerful indexing techniques available, and it's underused in most production systems.""".replace('class="BG"', 'class="%s"' % C)),

# --- B20 covering ---
("""the engine never has to follow a pointer back to the heap (PostgreSQL) or clustered index (SQL Server). This eliminates what PostgreSQL calls a heap fetch and SQL Server calls a key lookup, both of which can be expensive under high concurrency.""",
 """the engine never has to follow a pointer back to the clustered index. This eliminates the <strong class="text-white">key lookup</strong> — random I/O per row that is cheap for ten rows and ruinous for ten million under high concurrency."""),

# --- B21 index-only scan -> seek without lookup ---
("""In PostgreSQL, the Index-Only Scan is the plan node you want to see when you've built a covering index. The plan will confirm whether the index-only scan is being used, and the BUFFERS output will show whether heap pages are still being fetched (which happens when the visibility map indicates that not all heap pages are fully visible — a consequence of autovacuum lag). Running <code class="BG">VACUUM</code> on the table after bulk operations brings the visibility map current and allows index-only scans to skip heap fetches entirely.""".replace('class="BG"', 'class="%s"' % C),
 """In the execution plan, the shape you want for a covering index is an index seek with <em>no</em> key lookup — every column the query needs comes from the index's leaf pages (key columns plus <code class="BG">INCLUDE</code> columns). When you see a seek followed by thousands of key lookups, the index is almost-covering: adding the missing columns as <code class="BG">INCLUDE</code> (which don't affect key order, size limits aside) converts random I/O into a pure index operation. This is the highest-ROI index tuning move in OLTP.""" .replace('class="BG"', 'class="%s"' % C)),

# --- B22 pg_stat_statements -> Query Store ---
("""In PostgreSQL, there's no built-in equivalent, but <code class="BG">pg_stat_statements</code> combined with <code class="BG">EXPLAIN</code> automation gives a similar picture. Many organizations run automated pipelines that collect slow query logs, analyze query plans, and flag sequential scans on large tables where a viable index predicate exists.""".replace('class="BG"', 'class="%s"' % C),
 """<strong class="text-white">Query Store</strong> complements the missing-index DMVs with the history they lack: it persists query plans and runtime statistics across restarts, so you can correlate a missing-index suggestion with the actual workload it would serve and verify the improvement after creating the index. Many organizations run automated pipelines over Query Store data that flag regressed queries and candidate indexes together — turning index tuning from archaeology into a repeatable process."""),

# --- B23 unused indexes ---
("""In PostgreSQL, <code class="BG">pg_stat_user_indexes</code> tracks index scans since the last statistics reset. An index with zero or near-zero <code class="BG">idx_scan</code> after weeks of normal workload is a strong candidate for removal — but verify against your pg_stat_statements data and consider whether the index might be heavily used during period batch jobs that haven't run during your observation window.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, <code class="BG">sys.dm_db_index_usage_stats</code> tracks index seeks, scans, lookups, and updates since the last restart. An index with zero reads after weeks of normal workload is a strong candidate for removal — but verify against Query Store history and consider whether the index serves monthly batch jobs that haven't run during your observation window. Every unused index is pure write overhead: it costs on every <code class="BG">INSERT</code>, <code class="BG">UPDATE</code>, and <code class="BG">DELETE</code> and buys nothing.""".replace('class="BG"', 'class="%s"' % C)),

# --- B24 duplicate detection ---
("""Detecting these requires querying index metadata and comparing column lists. There is no single built-in tool for this in either database, but the query is straightforward to write against <code class="BG">pg_index</code>/<code class="BG">pg_attribute</code> in PostgreSQL or <code class="BG">sys.index_columns</code>/<code class="BG">sys.columns</code> in SQL Server.""".replace('class="BG"', 'class="%s"' % C),
 """Detecting these requires querying index metadata and comparing column lists. There is no single built-in tool for it, but the query is straightforward to write against <code class="BG">sys.index_columns</code> and <code class="BG">sys.columns</code> — look for indexes whose leading key columns are identical prefixes of another index's key.""" .replace('class="BG"', 'class="%s"' % C)),

# --- B25 UUID intro ---
("""One of the most common performance problems in PostgreSQL and SQL Server systems that use UUID (universally unique identifier) primary keys is extreme index fragmentation.""",
 """One of the most common performance problems in SQL Server systems that use UUID (universally unique identifier) primary keys is extreme index fragmentation."""),

# --- B26 UUID solutions ---
("""In PostgreSQL, using <code class="BG">gen_random_uuid()</code> (which produces UUID v4, fully random) as a primary key creates this problem. The practical solutions are: use a sequential surrogate key (<code class="BG">BIGSERIAL</code>) with the UUID as an alternate key, use UUID v7 (time-ordered UUIDs, available in PostgreSQL 17 via <code class="BG">uuidv7()</code> or installable via extensions), or use <code class="BG">pg_idkit</code> for ordered ID generation. In SQL Server, <code class="BG">NEWSEQUENTIALID()</code> generates UUIDs in sequential order suitable for clustered index keys, while <code class="BG">NEWID()</code> produces random UUIDs that cause the same fragmentation problem.""".replace('class="BG"', 'class="%s"' % C),
 """In SQL Server, <code class="BG">NEWID()</code> produces random UUIDs that scatter inserts across the B-tree and fragment it relentlessly, while <code class="BG">NEWSEQUENTIALID()</code> generates sequential GUIDs suitable for clustered index keys. The practical solutions are: use an <code class="BG">IDENTITY</code> surrogate key with the GUID as an alternate key, use <code class="BG">NEWSEQUENTIALID()</code> for the clustered key, or — if the GUID must be the clustered key — accept the fragmentation and maintain it with aggressive rebuilds and a lower fill factor.""".replace('class="BG"', 'class="%s"' % C)),

# --- takeaways ---
("""B-tree indexes are the default in both PostgreSQL and SQL Server, storing values in sorted order so the engine can support equality lookups, range scans, and ORDER BY without a separate sort — but the query planner only uses an index when its cost estimate, driven by table and column statistics, comes out cheaper than a sequential/table scan.""",
 """B-tree indexes are the default in SQL Server, storing values in sorted order so the engine can support equality lookups, range scans, and ORDER BY without a separate sort — but the optimizer only uses an index when its cost estimate, driven by table and column statistics, comes out cheaper than a scan."""),

("""Building indexes without disrupting production traffic is possible on both platforms — `CREATE INDEX CONCURRENTLY` in PostgreSQL and `WITH (ONLINE = ON)` in SQL Server (Enterprise Edition) — but each has real trade-offs in build time and failure handling that a DBA must plan for.""",
 """Building indexes without disrupting production traffic is possible with `WITH (ONLINE = ON)` (Enterprise Edition), and multi-hour builds can be made resumable — but online builds still take longer, use more tempdb, and need brief locks at start and end, so plan the maintenance window honestly."""),

("""Beyond the default B-tree, PostgreSQL offers specialized index types (hash, GIN, GiST, BRIN) suited to equality-only lookups, multi-value columns, spatial/full-text search, and naturally-ordered large tables respectively; SQL Server's closest equivalents are hash indexes for memory-optimized tables and columnstore/full-text indexes for their respective use cases.""",
 """Beyond the default B-tree, SQL Server offers hash indexes for memory-optimized tables, full-text indexes for document search, spatial indexes for geometry/geography, and columnstore for analytics — each dramatically outperforming B-trees on its home workload and useless outside it."""),

("""Partial indexes (PostgreSQL) and filtered indexes (SQL Server), along with covering indexes using `INCLUDE`, let you build smaller, faster indexes tailored to the queries that actually run — reducing both index size and write overhead compared to indexing an entire table.""",
 """Filtered indexes and covering indexes using `INCLUDE` let you build smaller, faster indexes tailored to the queries that actually run — reducing both index size and write overhead compared to indexing entire tables."""),

("""Index maintenance is an ongoing responsibility, not a one-time task: monitor for fragmentation (SQL Server) or bloat (PostgreSQL), remove unused and redundant indexes using usage statistics, and order composite index columns to match real query filter and sort patterns rather than guessing.""",
 """Index maintenance is an ongoing responsibility, not a one-time task: monitor fragmentation with `sys.dm_db_index_physical_stats`, remove unused and redundant indexes using usage statistics, and order composite index columns to match real query filter and sort patterns rather than guessing."""),
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
    print(f'ch06: all {len(REPLACEMENTS)} replacements applied')

main()
