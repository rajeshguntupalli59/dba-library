#!/usr/bin/env python3
"""Apply ch16 second-pass rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch16-integrations.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# NOTIFY/LISTEN PG paragraph -> Service Broker lead
("""<strong class="text-white">NOTIFY/LISTEN in PostgreSQL</strong> is a lightweight publish-subscribe mechanism built directly into the database. Applications can %s on a named channel and receive notifications sent by %s — either from application code or from triggers. This is useful for event-driven architectures where downstream consumers need to react to database changes without polling. A common pattern is a trigger that fires a %s when a new job row is inserted into a work queue table, waking up a worker process immediately rather than waiting for the next polling interval.""" % (code('LISTEN'), code('NOTIFY'), code('NOTIFY')),
 """SQL Server's <strong class="text-white">Service Broker</strong> is an asynchronous messaging system built directly into the engine: reliable message queuing, conversation-based messaging, and activation (stored procedures that fire automatically when messages arrive on a queue). A common pattern is a trigger or procedure that sends a message when a new job row lands in a work queue table, waking up a worker immediately rather than waiting for the next polling interval."""),
# Service Broker follow-up
("""SQL Server's equivalent for application event notification is <strong class="text-white">Service Broker</strong>, an asynchronous messaging system built into the engine. Service Broker supports reliable message queuing, conversation-based messaging, and activation (stored procedures that fire automatically when messages arrive on a queue). It is more powerful than PostgreSQL's NOTIFY/LISTEN but also substantially more complex to set up and operate. In practice, many teams bypass Service Broker in favor of external message queues (RabbitMQ, Azure Service Bus, Amazon SQS) that integrate with both their database and non-database components.""",
 """Service Broker is powerful but substantially more complex to set up and operate than an external queue. The choice comes down to transactional scope: Service Broker messages participate in the database transaction — the row and the message commit together or neither does — while an external queue cannot offer that guarantee. If you need atomic enqueue with the data change, Service Broker earns its complexity; otherwise, prefer an external message queue (RabbitMQ, Azure Service Bus, Amazon SQS) that integrates with both database and non-database components."""),
# ODBC/JDBC
("""Both PostgreSQL and SQL Server have ODBC and JDBC drivers that work reliably with this ecosystem.""",
 """SQL Server's first-party ODBC and JDBC drivers work reliably with this ecosystem."""),
# pg_stat_statements
("""%s in PostgreSQL and Query Store in SQL Server are your primary tools for identifying which integration endpoints are responsible for expensive queries.""" % code('pg_stat_statements'),
 """Query Store is your primary tool for identifying which integration endpoints are responsible for expensive queries — filter by application name or host to attribute cost per consumer."""),
# Flyway
("""For PostgreSQL, these tools typically connect via standard JDBC/psycopg2 and execute migration scripts in transaction blocks, with a metadata table tracking which migrations have been applied. For SQL Server, the same tools work via JDBC or ODBC.""",
 """These tools connect via JDBC or ODBC and execute migration scripts with a metadata table tracking which migrations have been applied. Prefer migrations that are online-safe (see Chapter 15) and make every migration re-runnable — a migration that fails halfway must be safe to run again, not a manual cleanup exercise."""),
# Takeaway PgBouncer
("""Connection poolers like PgBouncer are essential for PostgreSQL in production; always use transaction pooling mode for OLTP workloads, but understand the constraints it places on session-level features like prepared statements and advisory locks.""",
 """Driver-level connection pooling (SqlClient/ADO.NET) is essential in production; keep connection strings identical so pooling actually shares, size Max Pool Size against your whole app fleet, and keep pooled work stateless — `sp_reset_connection` clears most session state between checkouts."""),
# Takeaway FDW
("""Foreign data wrappers (PostgreSQL) and linked servers (SQL Server) enable cross-database querying, but they are operational tools — building application logic that depends on them at high frequency creates reliability and performance risks that are difficult to manage.""",
 """Linked servers enable cross-database querying, but they are operational tools — building application logic that depends on them at high frequency creates reliability and performance risks that are difficult to manage."""),
# Takeaway CDC
("""Change Data Capture, built on reading the transaction log rather than polling with `updated_at` columns, is the foundation of modern near-real-time pipelines; it requires deliberate configuration and monitoring (`wal_level = logical` and replication slot health in PostgreSQL, CDC cleanup jobs in SQL Server) or it silently degrades into a disk-filling or data-loss risk.""",
 """Change Data Capture, built on reading the transaction log rather than polling with `updated_at` columns, is the foundation of modern near-real-time pipelines; it requires deliberate configuration and monitoring (CDC cleanup jobs and capture latency) or it silently degrades into a disk-filling or data-loss risk."""),
# Takeaway cloud pub/sub
("""Cloud-managed database services change some integration mechanics — direct filesystem access for bulk loads is typically unavailable, replaced by cloud-native paths like `aws_s3` on RDS or external data sources on Azure SQL — and lightweight in-database pub/sub (`NOTIFY`/`LISTEN` in PostgreSQL, Service Broker in SQL Server) is appropriate for low-volume coordination but not a substitute for a real message queue at scale.""",
 """Cloud-managed database services change some integration mechanics — direct filesystem access for bulk loads is typically unavailable, replaced by cloud-native paths like Azure Blob Storage external sources — and lightweight in-database pub/sub (Service Broker) is appropriate for low-volume coordination but not a substitute for a real message queue at scale."""),
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
    print(f'ch16b: all {len(REPLACEMENTS)} replacements applied')

main()
