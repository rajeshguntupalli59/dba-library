#!/usr/bin/env python3
"""Apply ch35 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch35-cost.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
("PostgreSQL on AWS RDS, Azure Database for PostgreSQL, or Google Cloud SQL all charge by instance size",
 "SQL Server on AWS RDS, Azure SQL Database / Managed Instance, or Google Cloud SQL all charge by instance size"),
("Every idle connection in PostgreSQL holds memory. Every connection spike in SQL Server creates thread overhead.",
 "Every idle connection holds a thread and memory. Every connection spike creates scheduler contention and thread overhead."),
("Both PostgreSQL and SQL Server expose usage statistics that let you see actual consumption versus available capacity.",
 "SQL Server exposes usage statistics that let you see actual consumption versus available capacity."),
("""In PostgreSQL, %s shows you what's running right now, but for historical utilization you typically rely on external monitoring (pg_activity, pgBadger, or cloud-native tools). What you *can* measure internally is memory pressure through shared buffer hit rates — a low buffer hit rate suggests you need more memory, while a consistently high rate with unused headroom suggests you can scale down.""" % code('pg_stat_activity'),
 """In SQL Server, %s shows you what's running right now, but for historical utilization you typically rely on external monitoring (Prometheus + sql_exporter, or cloud-native tools). What you *can* measure internally is memory pressure through the buffer cache hit ratio and page life expectancy — a low hit rate suggests you need more memory, while a consistently high rate with unused headroom suggests you can scale down.""" % code('sys.dm_exec_sessions')),
("For SQL Server specifically, right-sizing has a licensing dimension that PostgreSQL avoids entirely.",
 "Right-sizing has a licensing dimension unique to commercial databases."),
("""PostgreSQL's architecture creates a backend process per connection — running 500 direct connections means 500 processes with their own memory allocations. PgBouncer, Pgpool-II, or RDS Proxy (in AWS) reduces this to a managed pool. SQL Server handles connections with threads, which is lighter, but pooling at the application layer via connection pool settings in ADO.NET, JDBC, or equivalent still prevents expensive connection churn.""",
 """SQL Server handles connections with threads rather than processes, which is lighter — but 500 direct connections still means 500 threads with their own memory allocations. Pooling at the application layer via ADO.NET/SqlClient connection pool settings (or RDS Proxy in AWS) reduces this to a managed pool and prevents expensive connection churn."""),
("Databases accumulate dead tuples, orphaned indexes, oversized TOAST/LOB data, and historical records that nobody queries anymore.",
 "Databases accumulate fragmented indexes, orphaned indexes, oversized LOB data, and historical records that nobody queries anymore."),
("""<strong class="text-white">Dead tuple reclamation in PostgreSQL</strong> is handled by VACUUM. Every UPDATE and DELETE in PostgreSQL leaves behind dead tuples that occupy space until VACUUM runs. Autovacuum handles most of this automatically, but heavily updated tables can accumulate bloat faster than autovacuum keeps up, especially if autovacuum cost delay parameters are tuned too conservatively. Checking bloat proactively is a production habit worth building.""",
 """<strong class="text-white">Fragmentation reclamation in SQL Server</strong> is handled by index rebuilds and reorganizes. Every UPDATE and DELETE fragments indexes and leaves forwarded records in heaps. Scheduled maintenance handles most of this automatically, but heavily updated tables can accumulate fragmentation faster than the maintenance window keeps up — especially if maintenance is tuned too conservatively. Checking fragmentation proactively is a production habit worth building."""),
("CREATE INDEX CONCURRENTLY (PostgreSQL) or CREATE INDEX WITH (ONLINE=ON) (SQL Server) so you can rebuild if needed.",
 "CREATE INDEX WITH (ONLINE=ON) so you can rebuild if needed."),
("In PostgreSQL, declarative partitioning makes it straightforward to detach an old partition and attach it to a cold storage tablespace. In SQL Server, partition switching allows you to move old data to a separate filegroup that maps to a slower (cheaper) disk tier without a full table rebuild.",
 "In SQL Server, partition switching allows you to move old data to a separate filegroup that maps to a slower (cheaper) disk tier without a full table rebuild."),
("Both PostgreSQL and SQL Server have built-in views that expose cumulative execution statistics,",
 "SQL Server has built-in views that expose cumulative execution statistics,"),
("""<strong class="text-white">PostgreSQL's licensing model is, of course, free</strong> — which is one of its cost advantages and a reason many organizations migrate to PostgreSQL from SQL Server when the workload allows it. When evaluating a migration, the DBA should quantify the SQL Server licensing savings against the migration cost and ongoing operational difference. For a 32-core SQL Server Enterprise instance, that calculation often favors migration strongly.""",
 """<strong class="text-white">SQL Server licensing is a cost lever worth its own review.</strong> Azure Hybrid Benefit lets you bring existing licenses with Software Assurance to Azure SQL, cutting compute costs roughly in half versus license-included pricing. On RDS, the choice is license-included versus BYOL. And Standard versus Enterprise is a standing question: if you are paying Enterprise prices without using Enterprise features (partitioning, online rebuilds, availability groups), that is money left on the table — a 32-core Enterprise instance costs several times its Standard equivalent."""),
("Autovacuum in PostgreSQL and automatic statistics updates in SQL Server keep basic maintenance current.",
 "Automatic statistics updates and scheduled index maintenance in SQL Server keep basic maintenance current."),
("PostgreSQL supports TOAST compression for large column values automatically, and table-level compression via PGLZ or LZ4 (in PostgreSQL 14+). SQL Server offers row, page, and columnstore compression",
 "SQL Server offers row, page, and columnstore compression"),
("Pull the top-20 queries by total resource consumption from `pg_stat_statements` or `sys.dm_exec_query_stats` and review for obvious index gaps or N+1 patterns.",
 "Pull the top-20 queries by total resource consumption from `sys.dm_exec_query_stats` or Query Store and review for obvious index gaps or N+1 patterns."),
("identified through `pg_stat_statements` or `sys.dm_exec_query_stats` — often delays or eliminates an instance tier upgrade",
 "identified through `sys.dm_exec_query_stats` or Query Store — often delays or eliminates an instance tier upgrade"),
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
    print(f'ch35: all {len(REPLACEMENTS)} replacements applied')

main()
