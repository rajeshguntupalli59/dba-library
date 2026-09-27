#!/usr/bin/env python3
"""Rewrite ch39 maintenance chapter as SQL Server-only. Fails loudly on non-unique matches."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch39-maintenance.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x):
    return '<code class="%s">%s</code>' % (C, x)

R = []

R.append((
    "This chapter brings together the recurring tasks that keep PostgreSQL and SQL Server healthy\u2014vacuuming and statistics gathering,",
    "This chapter brings together the recurring tasks that keep SQL Server healthy\u2014statistics gathering,",
))

R.append((
    "PostgreSQL and SQL Server approach the maintenance problem differently, and those differences shape the playbooks you'll build. PostgreSQL uses a multi-version concurrency control (MVCC) model that leaves dead row versions in place until VACUUM reclaims them. Without regular vacuuming, tables bloat, sequential scans slow down, and in the worst case, transaction ID wraparound halts the entire cluster. SQL Server uses a row-versioning or locking model depending on isolation level, and its equivalent maintenance concerns center on page fragmentation inside the B-tree structures it calls clustered and nonclustered indexes, as well as statistics staleness that causes the query optimizer to make poor plan choices.",
    "SQL Server's maintenance concerns center on page fragmentation inside the B-tree structures it calls clustered and nonclustered indexes, statistics staleness that causes the query optimizer to make poor plan choices, and transaction log growth that can fill a disk when backups and log management are not disciplined. These three areas shape the playbooks you will build.",
))

R.append((
    "Both platforms have auto-maintenance mechanisms built in\u2014PostgreSQL's autovacuum and SQL Server's auto-update statistics\u2014but neither should be treated as a complete solution on its own. Autovacuum is designed for steady-state workloads. It will fall behind on tables that receive large batch loads or suffer from high update rates. SQL Server's automatic statistics updates fire based on a row-modification threshold that doesn't scale linearly with table size; a billion-row table needs a change to twenty percent of rows before an automatic update triggers, which almost never happens. Manual maintenance jobs fill in the gaps that automation leaves.",
    "SQL Server has auto-update statistics built in, but it should not be treated as a complete solution on its own. Automatic statistics updates fire based on a row-modification threshold that doesn't scale linearly with table size; a billion-row table needs a change to twenty percent of rows before an automatic update triggers, which almost never happens. Manual maintenance jobs fill in the gaps that automation leaves.",
))

R.append((
    "validating physical data integrity with DBCC CHECKDB or pg_filechecksum-based monitoring,",
    "validating physical data integrity with DBCC CHECKDB,",
))

R.append((
    "Building the Vacuum and Statistics Playbook for PostgreSQL",
    "Building the Statistics Playbook",
))

R.append((
    "In PostgreSQL, VACUUM is not optional\u2014it is a fundamental part of how the storage engine functions. VACUUM reclaims space occupied by dead tuples, updates the visibility map so that index-only scans can work correctly, and advances the freeze horizon to prevent transaction ID wraparound. ANALYZE collects column statistics that the planner uses to estimate row counts and choose join strategies. In most shops, AUTOVACUUM handles both of these continuously in the background, but the DBA needs to understand its behavior well enough to know when to intervene manually.",
    "In SQL Server, the optimizer's statistics are the maintenance item most DBAs underestimate. Statistics tell the optimizer how many rows to expect at each step of a plan; stale statistics produce bad estimates, and bad estimates produce bad plans. The " + code('AUTO_UPDATE_STATISTICS') + " option keeps most statistics current, but the update is synchronous by default\u2014a plan compilation can stall while statistics refresh on a huge table. Enabling " + code('AUTO_UPDATE_STATISTICS_ASYNC') + " decouples the refresh from plan compilation: the optimizer uses the existing statistics for the current query while the refresh happens in the background.",
))

R.append((
    "The first sign that autovacuum is falling behind is usually bloat. A table that should occupy 2 GB on disk starts using 8 GB. Queries that were fast start doing far more I/O than expected. You can observe this by comparing the live tuple count to the dead tuple count in " + code('pg_stat_user_tables') + ".",
    "The first sign of stale statistics is usually plan regression: a query that was fast starts doing far more I/O than expected. You can observe this by comparing the estimated row counts in an execution plan to the actual row counts\u2014a large gap points at statistics that no longer describe the data.",
))

R.append((
    "When you find a table with a dead tuple percentage above ten or fifteen percent, autovacuum should have already addressed it\u2014if it hasn't, the first question is whether autovacuum is running at all, and the second is whether the table has storage parameters that override the default thresholds. Tables with a very high row velocity sometimes need custom autovacuum settings applied directly to them.",
    "When you find a table where " + code('STATS_DATE') + " shows statistics weeks old while the row count has changed dramatically, auto-update should have already addressed it\u2014if it hasn't, the first question is whether auto-update statistics is enabled at all, and the second is whether the table's change pattern falls below the auto-update threshold. Large tables that change a little at a time often need scheduled manual statistics updates.",
))

R.append((
    "For the manual vacuum playbook, the key distinction is between " + code('VACUUM') + " and " + code('VACUUM FULL') + ". Regular VACUUM reclaims dead space for reuse by future inserts but doesn't return space to the operating system\u2014the file size stays the same.",
    "For the manual statistics playbook, the key distinction is between " + code('UPDATE STATISTICS') + " with sampling and " + code('WITH FULLSCAN') + ". The default update samples the table, which is fast but can misrepresent skewed distributions. " + code('UPDATE STATISTICS ... WITH FULLSCAN') + " scans every row\u2014accurate but I/O-heavy on large tables. In practice, the sampling default is fine for most tables; reserve full scans for tables where plan regressions have been traced to sampling error.",
))

R.append((
    "A safer alternative to " + code('VACUUM FULL') + " for reducing table size without extended locking is the " + code('pg_repack') + " extension, which rebuilds tables in the background using triggers to capture concurrent changes, swapping the old and new versions at the end with only a brief lock.",
    "A safer alternative to blocking plan compilation during a statistics refresh is " + code('AUTO_UPDATE_STATISTICS_ASYNC') + ": the refresh happens in the background and queries proceed with the existing statistics instead of waiting. The tradeoff is a brief window of suboptimal plans, which is usually cheaper than blocking.",
))

R.append((
    "Transaction ID wraparound deserves its own attention in any PostgreSQL maintenance playbook. Every row in PostgreSQL is stamped with the transaction ID (XID) that inserted it. XIDs are 32-bit unsigned integers, meaning they wrap around after about 4 billion transactions. PostgreSQL tracks how far the oldest unfrozen XID is from the wraparound limit, and if the gap falls below the " + code('autovacuum_freeze_max_age') + " threshold (default 200 million transactions), it will force an aggressive VACUUM on affected tables. If the gap falls below " + code('vacuum_freeze_min_age') + ", PostgreSQL will begin freezing rows during regular vacuums. The DBA's job is to make sure this never becomes an emergency.",
    "Transaction log growth deserves its own attention in any SQL Server maintenance playbook. Every modification is logged, and in the full recovery model the log is not truncated until a log backup occurs. If log backups stop\u2014or never existed\u2014the log grows until the disk fills and the database goes read-only. The DBA's job is to make sure this never becomes an emergency: monitor log size, verify that log backup jobs are succeeding, and know which databases legitimately run in simple recovery.",
))

R.append((
    "A " + code('pct_toward_wraparound') + " above fifteen percent should be a monitored alert. Above thirty percent, you should be scheduling manual VACUUM FREEZE runs during off-peak hours on the oldest tables in each affected database.",
    "A transaction log above seventy percent of its allocated space with no recent log backup should be a monitored alert. At ninety percent, you should be taking a log backup immediately and investigating why the regular job stopped.",
))

R.append((
    "For statistics, the maintenance playbook should include a scheduled " + code('ANALYZE') + " run after any significant batch load or ETL job, because autovacuum's ANALYZE pass may not fire quickly enough for the query planner to produce good plans for the next batch of work. A simple approach is to ANALYZE the tables that were modified as part of the batch job script itself, immediately after the data load completes.",
    "For statistics, the maintenance playbook should include a scheduled " + code('UPDATE STATISTICS') + " run after any significant batch load or ETL job, because the auto-update threshold may not fire quickly enough for the optimizer to produce good plans for the next batch of work. A simple approach is to update statistics on the tables that were modified as part of the batch job script itself, immediately after the data load completes.",
))

R.append((
    "Index Maintenance Playbooks for Both Platforms",
    "Index Maintenance Playbook",
))

R.append((
    "In PostgreSQL, the fragmentation story is different. PostgreSQL's B-tree indexes can accumulate dead index entries that point to dead heap tuples, which inflate the index without providing any value. Regular VACUUM reclaims these dead index entries as part of its normal operation. There is no equivalent to SQL Server's REORGANIZE\u2014the main tool for reclaiming index space is " + code('REINDEX') + ",",
    "In SQL Server, fragmentation is measured at the page level. " + code('sys.dm_db_index_physical_stats') + " reports average fragmentation and page density; the standard playbook reorganizes lightly fragmented indexes (" + code('REORGANIZE') + " compacts pages online) and rebuilds heavily fragmented ones (" + code('REBUILD') + " creates a fresh index structure). The main tool for reclaiming index space is " + code('ALTER INDEX') + ",",
))

R.append((
    "In practice, most PostgreSQL indexes don't need manual reindexing if autovacuum is running properly. The cases where reindexing helps are heavily updated indexes where many deleted entries accumulate faster than vacuum can reclaim them, or indexes that have grown significantly through one-time bulk inserts and now have structural imbalance.",
    "In practice, most indexes don't need rebuilds on a fixed schedule if fragmentation is monitored and addressed adaptively. The cases where rebuilds help are heavily updated indexes where page splits accumulate faster than reorganization can tidy them, or indexes that have grown significantly through one-time bulk inserts and now have structural imbalance.",
))

R.append((
    "Both platforms maintain statistics about how frequently each index is accessed, but there's an important caveat: SQL Server's index usage stats reset when the service restarts, and PostgreSQL's reset when " + code('pg_stat_reset()') + " is called or the server restarts.",
    "SQL Server maintains index usage statistics in " + code('sys.dm_db_index_usage_stats') + ", but there's an important caveat: the stats reset when the service restarts.",
))

R.append((
    "PostgreSQL doesn't have a built-in equivalent to CHECKDB, which is one of the more significant operational gaps between the two platforms. The closest built-in tool is " + code('VACUUM VERBOSE') + ", which reports any page-level errors it encounters while scanning tables, but it doesn't actively validate B-tree index consistency. The " + code('amcheck') + " extension, available in PostgreSQL 10 and later, provides functions to check B-tree index structural integrity without any locking.",
    "DBCC CHECKDB is the built-in integrity validator for SQL Server. It checks page allocation, index linkage, and data-page consistency across the whole database. Run it on a regular schedule\u2014weekly for critical databases\u2014and understand that it is I/O-heavy: on very large databases, splitting CHECKDB across a longer window or running it against a restored backup copy are the standard adaptations.",
))

R.append((
    "For table-level data verification in PostgreSQL, the " + code('pg_filechecksum') + " utility introduced in PostgreSQL 12 (when data checksums are enabled at cluster initialization with " + code('initdb --data-checksums') + ") detects block-level corruption by verifying stored checksums against computed checksums when pages are read. Data checksums should be enabled on all new PostgreSQL clusters\u2014the performance overhead is typically one to two percent, and the early detection capability is worth far more than that.",
    "SQL Server can also detect block-level corruption through page checksums: the " + code('PAGE_VERIFY') + " option (" + code('CHECKSUM') + " is the default) stores a checksum on every page and verifies it on read. Verify that " + code('PAGE_VERIFY') + " is set to " + code('CHECKSUM') + " on all databases\u2014a database upgraded long ago may still carry " + code('TORN_PAGE_DETECTION') + " or " + code('NONE') + ", which leave corruption undetectable until something reads the bad page.",
))

R.append((
    "For SQL Server, this means periodically restoring a backup to a test server and running CHECKDB against the restored copy. For PostgreSQL, it means testing " + code('pg_restore') + " or base backup recovery on a non-production server at regular intervals. The backup that has never been tested is not a backup\u2014it's a hope.",
    "This means periodically restoring a backup to a test server and running CHECKDB against the restored copy. The backup that has never been tested is not a backup\u2014it's a hope.",
))

R.append((
    "Both platforms provide native scheduling mechanisms. SQL Server Agent is the standard scheduler for SQL Server environments, with job steps, schedules, alerts, and notifications built in. PostgreSQL has no built-in scheduler; the common choices are " + code('pg_cron') + " (a PostgreSQL extension that provides cron-syntax scheduling inside the database), external system cron, or dedicated job scheduling tools like pgAgent. In containerized or cloud environments, Kubernetes CronJobs or cloud-native schedulers often take over this role.",
    "SQL Server Agent is the standard scheduler for SQL Server environments, with job steps, schedules, alerts, and notifications built in. In containerized or cloud environments, Kubernetes CronJobs or cloud-native schedulers such as Azure Elastic Jobs often take over this role.",
))

R.append((
    "A VACUUM ANALYZE on a non-critical table might run during business hours with minimal impact. A VACUUM FULL that holds an exclusive lock for forty minutes needs a maintenance window agreement with application owners.",
    "A statistics update on a non-critical table might run during business hours with minimal impact. An offline index rebuild that holds locks for forty minutes needs a maintenance window agreement with application owners.",
))

R.append((
    "Both SQL Server Agent and pg_cron have mechanisms for detecting running jobs and preventing duplicate execution, but verifying that these protections are in place\u2014rather than assuming they are\u2014is part of good operational hygiene.",
    "SQL Server Agent will happily start a second instance of a job that is already running, so guard against overlap by checking " + code('msdb.dbo.sysjobactivity') + " in the first job step and exiting if the job is already active. Verifying that this protection is in place\u2014rather than assuming it is\u2014is part of good operational hygiene.",
))

R.append((
    "And in high-availability environments\u2014Always On Availability Groups, Patroni clusters, streaming replicas\u2014maintenance activities on the primary can have unexpected effects on secondaries.",
    "And in high-availability environments\u2014Always On Availability Groups with readable secondaries\u2014maintenance activities on the primary can have unexpected effects on secondaries.",
))

R.append((
    "For PostgreSQL at scale, the equivalent strategy is tuning autovacuum aggressiveness per table rather than running manual VACUUM jobs across the board. Tables with high transaction rates need lower autovacuum thresholds so that vacuum fires more frequently with smaller accumulated dead tuples. Tables with very low write rates can have higher thresholds so autovacuum doesn't spend cycles on them unnecessarily.",
    "For SQL Server at scale, the strategy is adaptive fragmentation maintenance: query " + code('sys.dm_db_index_physical_stats') + " at runtime and rebuild only indexes above a meaningful fragmentation threshold. Cycling rebuilds across every table uniformly wastes resources and can blow past the maintenance window.",
))

R.append((
    "<code>-- PostgreSQL: Set aggressive autovacuum for a high-write table\nALTER TABLE public.events\nSET (\n    autovacuum_vacuum_scale_factor = 0.01,    -- vacuum when 1% of rows are dead\n    autovacuum_analyze_scale_factor = 0.005,  -- analyze when 0.5% of rows changed\n    autovacuum_vacuum_cost_delay = 2           -- reduce IO throttling for this table\n);</code>",
    "<code>-- SQL Server: adaptive index maintenance based on live fragmentation\nSELECT\n    OBJECT_SCHEMA_NAME(ips.object_id) AS schema_name,\n    OBJECT_NAME(ips.object_id) AS table_name,\n    i.name AS index_name,\n    ips.avg_fragmentation_in_percent,\n    ips.page_count,\n    CASE\n        WHEN ips.avg_fragmentation_in_percent &gt;= 30 THEN N'REBUILD'\n        WHEN ips.avg_fragmentation_in_percent &gt;= 5  THEN N'REORGANIZE'\n        ELSE N'SKIP'\n    END AS recommended_action\nFROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips\nJOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id\nWHERE ips.page_count &gt; 1000   -- fragmentation stats are meaningless on tiny indexes\n  AND ips.avg_fragmentation_in_percent &gt;= 5;</code>",
))

R.append((
    "PostgreSQL streaming replicas are similarly affected by heavy write operations during maintenance. A VACUUM FULL or REINDEX CONCURRENTLY generates WAL that must be shipped and replayed on standbys. In some configurations, particularly with synchronous replication, this can stall the primary if standbys can't keep up. Monitoring replication lag before and during maintenance operations is good practice, with documented thresholds at which the DBA should pause or throttle maintenance work.",
    "Availability group secondaries are similarly affected by heavy write operations during maintenance. An offline index rebuild generates transaction log that must be shipped and replayed on secondaries. Monitoring the redo queue before and during maintenance operations is good practice, with documented thresholds at which the DBA should pause or throttle maintenance work.",
))

R.append((
    "**Autovacuum and auto-statistics are starting points, not complete solutions.** Both PostgreSQL and SQL Server provide background automation for common maintenance tasks, but manual playbooks are required to handle batch loads, high-volume tables, and workloads that exceed what background processes can keep up with.",
    "**Auto-update statistics is a starting point, not a complete solution.** SQL Server provides background automation for statistics maintenance, but manual playbooks are required to handle batch loads, high-volume tables, and workloads that exceed what the background process can keep up with.",
))

R.append((
    "**Transaction ID wraparound in PostgreSQL is a hard limit, not a soft warning.** Monitoring `age(datfrozenxid)` and scheduling aggressive VACUUM FREEZE runs when the age climbs toward dangerous thresholds is a non-negotiable part of any PostgreSQL maintenance playbook.",
    "**Transaction log management in the full recovery model is non-negotiable.** Monitoring log size and verifying that log backup jobs succeed is a non-negotiable part of any SQL Server maintenance playbook\u2014without log backups, the log grows until the disk fills.",
))

R.append((
    "**Maintenance operations in high-availability environments must account for replication effects.** Index rebuilds, VACUUM FULL, and CHECKDB all generate I/O and log volume that affects secondaries and replicas. Monitor replication lag during maintenance windows and have documented thresholds at which work should be paused or throttled to protect secondary availability.",
    "**Maintenance operations in high-availability environments must account for replication effects.** Index rebuilds and CHECKDB all generate I/O and log volume that affects secondaries. Monitor the redo queue and replication lag during maintenance windows and have documented thresholds at which work should be paused or throttled to protect secondary availability.",
))

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(R):
        count = text.count(old)
        if count != 1:
            print('FAIL replacement %d: found %d occurrences' % (i, count))
            print('OLD SNIPPET:', old[:160])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print('ch39: all %d replacements applied' % len(R))

main()
