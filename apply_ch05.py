#!/usr/bin/env python3
"""Apply ch05 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch05-storage-models.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'

REPLACEMENTS = [
# --- B1 intro ---
("""PostgreSQL and SQL Server each take distinct approaches to organizing data on storage, and understanding those approaches at a fundamental level separates DBAs who tune by intuition from those who tune by understanding. This chapter covers how rows and pages are structured, how heap files and clustered indexes differ as storage strategies, how columnar storage changes the game for analytical workloads, and how both databases manage free space and page layout internally.""",
 """SQL Server takes a deliberate, layered approach to organizing data on storage, and understanding it at a fundamental level separates DBAs who tune by intuition from those who tune by understanding. This chapter covers how rows and pages are structured, how heaps and clustered indexes differ as storage strategies, how columnar storage changes the game for analytical workloads, and how the engine manages free space and page layout internally."""),

# --- B2 buffer pool ---
("""these blocks are what live in the shared buffer pool (PostgreSQL) or the buffer cache (SQL Server).""",
 """these blocks are what live in the buffer pool."""),

# --- B3 PG page size -> SQL Server pages/extents ---
("""<strong class="text-white">PostgreSQL</strong> uses a default page size of 8 KB, configurable at compile time (16 KB and 32 KB are common alternatives for analytical workloads). Every heap file — which is how PostgreSQL stores a table on disk — is divided into these 8 KB pages. The page count is tracked indirectly through the file system and internal catalog, not through a centralized allocation bitmap the way SQL Server does.""",
 """<strong class="text-white">SQL Server</strong> uses a fixed page size of 8 KB — not configurable, which simplifies every capacity calculation you will ever do. Pages are grouped into <strong class="text-white">extents</strong> of eight contiguous pages (64 KB), and allocation is tracked by a centralized metadata layer: PFS (Page Free Space) pages record how full each page is, GAM and SGAM pages track which extents are free or in use, and IAM (Index Allocation Map) pages record which extents belong to which object. Finding free space for an insert is a metadata lookup against this layer, never a scan."""),

# --- B4 section heading ---
(">PostgreSQL's Heap Storage and Page Layout<",
 ">SQL Server Heap Storage and Page Layout<"),

# --- B5 heap definition ---
("""PostgreSQL stores all tables as heap files — an unordered collection of pages where rows are inserted wherever free space is available. There is no physical ordering of rows on disk by default; the heap is a flat, unordered structure.""",
 """A SQL Server <strong class="text-white">heap</strong> is an unordered collection of pages where rows are inserted wherever free space is available. There is no physical ordering of rows on disk; the heap is a flat, unordered structure, and each row is located by its <strong class="text-white">RID</strong> — the combination of file ID, page ID, and slot number."""),

# --- B6 page anatomy ---
("""Each PostgreSQL page contains four distinct areas: a page header (24 bytes of metadata including the page LSN for WAL coordination), an item identifier array, free space in the middle, and the actual tuple data at the bottom. This layout is sometimes described as growing from both ends toward the middle. Item identifiers are 4-byte pointers stored from the top of the usable area downward, and tuple data is stored from the bottom of the page upward. When the two regions meet, the page is full.""",
 """Each SQL Server page contains three distinct areas: a 96-byte page header (metadata including page type, allocation status, and free-space pointers), the data rows themselves, and a row-offset array — the slot array — at the end of the page. Rows are addressed through the slot array rather than by physical byte offset, which lets the engine compact free space within a page without invalidating references. Data grows from the top of the usable area downward while the slot array grows from the bottom upward; when the two regions meet, the page is full."""),

# --- B7 figure caption ---
("""*Figure: Layout of a PostgreSQL heap page — item pointers grow down from the header while tuple data grows up from the bottom; the page is full when the two regions meet.*""",
 """*Figure: Layout of a SQL Server data page — the 96-byte header is followed by data rows growing downward, with the slot array growing up from the end of the page; the page is full when free space between the two regions is exhausted.*"""),

# --- B8 tuple/MVCC -> SQL Server row internals ---
("""Each row stored in a PostgreSQL heap is formally called a <strong class="text-white">tuple</strong>, and each tuple has a header that carries MVCC metadata: <code class="BG">xmin</code> (the transaction ID that inserted the row), <code class="BG">xmax</code> (the transaction ID that deleted or updated the row, if any), and the <code class="BG">ctid</code> (a physical location pointer in the form of page number and item offset). This MVCC structure means that an <code class="BG">UPDATE</code> in PostgreSQL does not modify the row in place — it inserts a new version of the tuple and marks the old version as dead. Dead tuples accumulate and must be reclaimed by <code class="BG">VACUUM</code>. This is a defining characteristic of PostgreSQL's storage model, with significant implications for table bloat and maintenance.""".replace('class="BG"', 'class="%s"' % C),
 """Each row stored in a SQL Server page carries a small record header with status bits, the record length, and — for rows under versioning — a 14-byte versioning tag pointing into tempdb's version store. An <code class="BG">UPDATE</code> modifies the row in place when the new version fits on the page; when a variable-length row outgrows its page, the engine forwards the row (in a heap, leaving a forwarding pointer behind) or splits the page (in a clustered index, moving half the rows to a new page). Forwarding pointers and page splits are the two fragmentation mechanisms that make index maintenance a routine DBA task rather than an occasional emergency.""".replace('class="BG"', 'class="%s"' % C)),

# --- B9 PGDATA -> allocation units ---
("""PostgreSQL tables are physically stored as files in the data directory under <code class="BG">$PGDATA/base/<db_oid>/</code>. Each table gets one or more files named by its relfilenode. When a table grows beyond 1 GB, PostgreSQL automatically splits it into numbered segment files (e.g., <code class="BG">12345</code>, <code class="BG">12345.1</code>, <code class="BG">12345.2</code>). This segmentation is transparent to the query engine but is worth knowing when performing file-level backups or diagnosing disk layout issues.""".replace('class="BG"', 'class="%s"' % C),
 """SQL Server tables are physically stored as extents in the database's data files (<code class="BG">.mdf</code>/<code class="BG">.ndf</code>), organized by filegroup. Each table or index partition gets its own <strong class="text-white">allocation units</strong> — <code class="BG">IN_ROW_DATA</code> for regular rows, <code class="BG">LOB_DATA</code> for large values, <code class="BG">ROW_OVERFLOW_DATA</code> for variable-length columns pushed off-row. The <code class="BG">sys.allocation_units</code> catalog view exposes exactly how many pages each allocation unit consumes, which is the ground truth for every "where did my space go" investigation.""".replace('class="BG"', 'class="%s"' % C)),

# --- B10 no natural order ---
("""One consequence of the heap model is that PostgreSQL has no concept of a "natural" row order. If you write a query without an <code class="BG">ORDER BY</code>, rows can come back in any sequence — not necessarily insertion order, and certainly not always the same sequence on repeated runs, especially after VACUUMs and updates shift tuple positions.""".replace('class="BG"', 'class="%s"' % C),
 """One consequence of the heap model is that SQL Server heaps have no concept of a "natural" row order. If you write a query without an <code class="BG">ORDER BY</code>, rows can come back in any sequence — not necessarily insertion order, and not the same sequence on repeated runs, especially after rebuilds and new allocations shift row positions. Never rely on observed order without an explicit <code class="BG">ORDER BY</code>.""".replace('class="BG"', 'class="%s"' % C)),

# --- B11 PFS/FSM comparison tail ---
(""", forming an allocation metadata layer that PostgreSQL handles differently through its Free Space Map (FSM) — a dedicated fork of the heap file.""",
 """, forming an allocation metadata layer the engine consults on every insert — finding a page with free space is a metadata lookup, never a scan."""),

# --- B12 heap comparison ---
("""When a table does not have a clustered index, it is stored as a <strong class="text-white">heap</strong> in SQL Server — essentially the same concept as PostgreSQL's heap. SQL Server heaps come with their own maintenance concerns: forwarding pointers accumulate when variable-length rows grow and must be moved, and the only way to clean those up is to rebuild the heap or add a clustered index.""",
 """When a table does not have a clustered index, it is stored as a <strong class="text-white">heap</strong> — an unordered collection of pages with rows addressed by RID. Heaps come with their own maintenance concerns: forwarding pointers accumulate when variable-length rows grow and must be moved, and the only way to clean those up is to rebuild the heap (<code class="BG">ALTER TABLE ... REBUILD</code>) or add a clustered index.""".replace('class="BG"', 'class="%s"' % C)),

# --- B13 CLUSTER comparison ---
("""The absence of a clustered index concept in PostgreSQL has one visible benefit: <code class="BG">CLUSTER</code> exists as a one-time physical reorganization command, but it is not self-maintaining. SQL Server's clustered index, by contrast, continuously maintains physical row order as data is inserted, updated, and deleted — at the cost of page splits when rows are inserted in non-sequential key order.""".replace('class="BG"', 'class="%s"' % C),
 """A clustered index continuously maintains physical row order as data is inserted, updated, and deleted — at the cost of page splits when rows arrive in non-sequential key order. This self-maintaining order is the clustered index's great strength and its great danger: it makes range scans on the key nearly free, and it makes a poor key choice (random GUIDs, wide volatile columns) a permanent tax on every write and every nonclustered index on the table."""),

# --- B14 PG columnar -> columnstore operations ---
("""<strong class="text-white">PostgreSQL</strong> does not include a native columnar storage format in the standard distribution. However, the <strong class="text-white">cstore_fdw</strong> extension (now largely superseded by <strong class="text-white">pg_mooncake</strong> and the <strong class="text-white">Hydra Columnar</strong> project) and the <strong class="text-white">TimescaleDB</strong> extension both provide columnar access paths. For production analytical workloads on PostgreSQL, many shops use PostgreSQL as the OLTP engine and route analytical queries to a separate columnar system (Redshift, DuckDB, ClickHouse) through foreign data wrappers, or they use partitioning combined with careful indexing to approximate columnar efficiency.""",
 """Operating a columnstore has its own discipline. Trickle inserts and singleton updates fight the format: small batches land in the <strong class="text-white">delta store</strong> (a rowstore staging area per rowgroup) and are only compressed into column segments when the rowgroup closes — a table fed one row at a time will sit in the delta store forever and perform like a bad rowstore. Bulk loads, by contrast, bypass the delta store and compress directly. <strong class="text-white">Segment elimination</strong> — skipping entire rowgroups using min/max metadata — is what makes columnstore scans fast, and it depends on data being ordered or at least correlated by the filtered columns; randomly ordered loads eliminate nothing. Monitor <code class="BG">sys.dm_db_column_store_row_group_physical_stats</code> for rowgroup health: many small OPEN or TRIMMED rowgroups are the signature of a load pattern fighting the format.""".replace('class="BG"', 'class="%s"' % C)),

# --- B15 FSM -> PFS ---
("""<strong class="text-white">PostgreSQL's Free Space Map (FSM)</strong> is a secondary file maintained alongside each heap file. When PostgreSQL needs to insert a new tuple, it consults the FSM to find a page with enough free space. The FSM does not track exact free space byte-by-byte; it approximates free space in 32-byte granularity buckets, which is efficient to store and fast to search. After a <code class="BG">VACUUM</code> runs, it updates the FSM so future insertions can reuse space from dead tuples.""".replace('class="BG"', 'class="%s"' % C),
 """<strong class="text-white">Page Free Space (PFS) pages</strong> are the allocation layer's answer to "where can I put this row". Each PFS page tracks roughly 8,000 data pages, recording how full each page is and whether it belongs to a mixed or uniform extent. When the engine needs space for an insert, it consults PFS rather than scanning — and <code class="BG">DBCC PAGE</code> can show you the PFS bytes for any page when you are diagnosing allocation anomalies at the physical level.""".replace('class="BG"', 'class="%s"' % C)),

# --- B16 VM -> fill factor ---
("""PostgreSQL's <strong class="text-white">Visibility Map (VM)</strong> is another companion file per heap, introduced for index-only scan optimization. The VM tracks which pages contain only tuples visible to all current transactions (all-visible pages). If a page is all-visible, an index-only scan can return index data without touching the heap at all, which is a significant I/O reduction for read-heavy workloads.""",
 """<strong class="text-white">Fill factor</strong> is the DBA's direct control over free space: <code class="BG">CREATE INDEX ... WITH (FILLFACTOR = 80)</code> leaves 20% of each leaf page empty at build time, reserving room for future inserts without immediate page splits. The right fill factor follows the write pattern — 100 (or 0, which means 100) for read-mostly tables, lower for random-insert workloads — and it applies only at index build or rebuild time; everyday inserts still fill pages toward 100% between maintenance windows. This is why rebuild cadence and fill factor are tuned together, never separately.""".replace('class="BG"', 'class="%s"' % C)),

# --- B17 PG bloat -> SQL Server bloat ---
("""<strong class="text-white">Table bloat</strong> in PostgreSQL is the accumulation of dead tuples from updates and deletes. If <code class="BG">VACUUM</code> does not run frequently enough — or if a long-running transaction prevents it from cleaning old tuple versions — dead tuples pile up, pages fill with non-reclaimable rows, and effective table size grows without the row count growing. Bloated tables cause sequential scans to read more pages than necessary and indexes to become sparse.""".replace('class="BG"', 'class="%s"' % C),
 """<strong class="text-white">Bloat</strong> in SQL Server takes three familiar forms. <strong class="text-white">Ghost records</strong> from deletes linger until the ghost cleanup task sweeps them, so a table can report more pages than its live rows justify. <strong class="text-white">Forwarded records</strong> in heaps accumulate when variable-length rows outgrow their page — each forward adds a page hop to every read of that row. And <strong class="text-white">index fragmentation</strong> — logical order diverging from physical order through page splits — degrades range scans until a rebuild or reorganize restores order. <code class="BG">sys.dm_db_index_physical_stats</code> reports all of it; the maintenance question is always rebuild versus reorganize, keyed off fragmentation percentage and page count.""".replace('class="BG"', 'class="%s"' % C)),

# --- B18 TOAST heading ---
(">TOAST, Row Overflow, and Large Object Handling<",
 ">Row Overflow and Large Object Handling<"),

# --- B19 TOAST -> row overflow/LOB ---
("""<strong class="text-white">TOAST (The Oversized-Attribute Storage Technique)</strong> is PostgreSQL's solution. A PostgreSQL row must ultimately fit on a single 8 KB page, but TOAST does not wait until a row is that large — by default it starts trying to compress or move a value out-of-line once a single field pushes the tuple past roughly 2 KB, so that several tuples can still fit per page. When a column value crosses that threshold, PostgreSQL automatically stores the value out-of-line in a companion TOAST table. Each regular table that has any potentially-large columns has a corresponding TOAST table in <code class="BG">pg_toast</code>.""".replace('class="BG"', 'class="%s"' % C),
 """<strong class="text-white">Row overflow and LOB storage</strong> are SQL Server's answer to oversized values. A row must fit on a single 8 KB page, but variable-length columns (<code class="BG">varchar</code>, <code class="BG">nvarchar</code>, <code class="BG">varbinary</code>) that push the row past ~8,060 bytes are moved off-row into <code class="BG">ROW_OVERFLOW_DATA</code> allocation units, leaving only a 24-byte pointer behind. True large values — <code class="BG">varchar(max)</code>, <code class="BG">nvarchar(max)</code>, <code class="BG">varbinary(max)</code>, <code class="BG">xml</code> — live in <code class="BG">LOB_DATA</code> allocation units as a tree of pages per value. For values that are really files, <code class="BG">FILESTREAM</code> and FileTable store the bytes in the NTFS filesystem while keeping them transactionally consistent with the database.""".replace('class="BG"', 'class="%s"' % C)),

# --- B20 four strategies list ---
("""PostgreSQL applies one of four storage strategies to large values:""",
 """SQL Server applies one of four storage strategies to large values:"""),
("""1. <strong class="text-white">PLAIN:</strong> No compression, no out-of-line storage. Used for fixed-size types that can never overflow.""",
 """1. <strong class="text-white">In-row:</strong> Values that keep the row under ~8,060 bytes live on the data page itself — the fastest access path, and the reason narrow rows matter."""),
("""2. <strong class="text-white">EXTENDED (default for text, bytea, jsonb, etc.):</strong> Try compression first; if the compressed value still doesn't fit, move it out-of-line.""",
 """2. <strong class="text-white">Row-overflow:</strong> Variable-length values that push the row past the limit move to <code class="BG">ROW_OVERFLOW_DATA</code> pages, leaving a pointer. The <code class="BG">large value types out of row</code> table option can force even small (max) values off-row.""".replace('class="BG"', 'class="%s"' % C)),
("""3. <strong class="text-white">EXTERNAL:</strong> Store out-of-line without compression. Useful when the data is already compressed (e.g., PNG or GZIP content) and re-compression wastes CPU.""",
 """3. <strong class="text-white">LOB:</strong> <code class="BG">(max)</code> types and <code class="BG">xml</code> live in <code class="BG">LOB_DATA</code> allocation units — a B-tree of pages per value, efficient for large documents, expensive for small ones.""".replace('class="BG"', 'class="%s"' % C)),
("""4. <strong class="text-white">MAIN:</strong> Compress but try to keep in-line; only move out-of-line as a last resort.""",
 """4. <strong class="text-white">FILESTREAM / FileTable:</strong> For values that are really files — documents, images, video — bytes live in the filesystem under transactional control, queryable with T-SQL but streamed without dragging them through the buffer pool."""),

# --- B21 TOAST perf cost ---
("""TOAST is largely transparent, but it has a visible performance cost: accessing a TOASTed column requires an additional fetch from the TOAST relation, which is an extra heap read. Queries that select <code class="BG">SELECT *</code> on a table with large TOAST columns read dramatically more data than queries that select only the small columns. This is one of the most common sources of unexpected I/O in PostgreSQL — <code class="BG">SELECT *</code> on a table with a <code class="BG">jsonb</code> payload column can be orders of magnitude slower than selecting the specific non-TOAST columns you actually need.""".replace('class="BG"', 'class="%s"' % C),
 """Off-row storage is largely transparent, but it has a visible performance cost: accessing an overflow or LOB column requires additional page reads beyond the data page. Queries that select <code class="BG">SELECT *</code> on a table with large <code class="BG">nvarchar(max)</code> or <code class="BG">varbinary(max)</code> columns read dramatically more data than queries that select only the small columns. This is one of the most common sources of unexpected I/O — <code class="BG">SELECT *</code> on a table with a multi-megabyte JSON payload column can be orders of magnitude slower than selecting the specific columns the query actually needs.""".replace('class="BG"', 'class="%s"' % C)),

# --- B22 lead-in ---
("""You can identify tables with significant TOAST usage in PostgreSQL:""",
 """You can identify tables with significant LOB or row-overflow usage:"""),

# --- B23 vertical partitioning ---
("""This is not premature optimization; it is sound physical design that PostgreSQL's TOAST and SQL Server's LOB architecture do not automatically compensate for.""",
 """This is not premature optimization; it is sound physical design that the engine's overflow architecture does not automatically compensate for."""),

# --- takeaways ---
("""**The 8 KB page is the fundamental unit of I/O** in both PostgreSQL and SQL Server.""",
 """**The 8 KB page is the fundamental unit of I/O** in SQL Server."""),
("""**PostgreSQL stores all tables as unordered heaps**, which means physical row order is never guaranteed and dead tuples from MVCC accumulate over time, requiring regular `VACUUM` to reclaim space. SQL Server defaults to a clustered index structure where the leaf level of the B-tree *is* the table, making the choice of clustering key one of the most impactful physical design decisions on that platform.""",
 """**SQL Server stores tables as heaps or clustered indexes**: heaps carry no physical row order and accumulate forwarded records; clustered indexes make the B-tree leaf level *the table itself* — making clustering-key selection (narrow, static, ever-increasing) one of the most impactful physical design decisions you will make."""),
("""**Columnar storage fundamentally changes the I/O pattern for analytical queries**, reading only the columns referenced rather than entire rows. SQL Server's clustered and nonclustered columnstore indexes are production-ready for HTAP and warehouse workloads; PostgreSQL users typically rely on external columnar engines or specialized extensions for equivalent performance.""",
 """**Columnar storage fundamentally changes the I/O pattern for analytical queries**, reading only the columns referenced rather than entire rows; watch rowgroup health in `sys.dm_db_column_store_row_group_physical_stats`, because trickle-fed delta stores and untrimmed rowgroups silently destroy the segment elimination that makes columnstore fast."""),
("""**TOAST (PostgreSQL) and LOB/overflow pages (SQL Server)** transparently handle large column values, but they carry a real access cost: fetching a TOASTed or LOB column means an extra read beyond the main data page, so `SELECT *` on a table with large JSON, text, or binary columns can be far slower than selecting only the columns a query actually needs. Splitting rarely-accessed large columns into a separate table is a legitimate physical design pattern on both platforms, not premature optimization.""",
 """**LOB and row-overflow pages** transparently handle large column values, but they carry a real access cost: fetching an off-row column means extra reads beyond the data page, so `SELECT *` on a table with large JSON, text, or binary columns can be far slower than selecting only the columns a query needs. Splitting rarely-accessed large columns into a separate table is a legitimate physical design pattern, not premature optimization."""),
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
    print(f'ch05: all {len(REPLACEMENTS)} replacements applied')

main()
