#!/usr/bin/env python3
"""Apply ch22 second-pass rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch22-distributed.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
PRE = '<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>'

REPLACEMENTS = [
# 1 edition cost
("""One important operational distinction: PostgreSQL streaming replication is built into the database engine and is free. SQL Server Always On Availability Groups require Enterprise Edition or, in limited form, Standard Edition.""",
 """One important operational distinction: Always On Availability Groups require Enterprise Edition or, in limited form, Standard Edition (basic AGs: one database per group, no readable secondaries)."""),

# 2 lag intro
("""Both PostgreSQL and SQL Server provide views to monitor this, and both should be feeding alerting systems continuously.""",
 """%s and %s expose it continuously, and both should be feeding alerting systems.""" % (code('sys.dm_hadr_database_replica_states'), code('sys.dm_hadr_availability_replica_states'))),

# 3 quorum voters
("""Adding a third node — or a lightweight quorum witness (an etcd node, a file share witness in WSFC, or Patroni's third etcd node) — breaks the tie and makes automatic failover safe.""",
 """Adding a third node — or a lightweight quorum witness (a file share witness or cloud witness in WSFC) — breaks the tie and makes automatic failover safe."""),

# 4 LSN pre block -> AG lag query
("""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- On standby: wait until the replica has replayed past a given LSN
-- pg_wal_lsn_diff returns 0 or negative when standby has caught up
SELECT pg_wal_lsn_diff('0/1A3F2C0'::pg_lsn, pg_last_wal_replay_lsn()) AS bytes_behind;</code></pre>""",
 PRE + """-- On a secondary: how far behind is this replica right now?
SELECT DB_NAME(database_id) AS db_name,
       log_send_queue_size AS send_queue_kb,
       redo_queue_size AS redo_queue_kb,
       last_commit_time
FROM sys.dm_hadr_database_replica_states
WHERE is_local = 1
  AND is_primary_replica = 0;</code></pre>"""),

# 5 log_line_prefix
("""PostgreSQL's %s should include %s (timestamp), %s (PID), %s (application name), and %s (database name) at minimum. In a distributed deployment, adding the hostname is essential.""" % (code('log_line_prefix'), code('%t'), code('%p'), code('%a'), code('%d')),
 """Ensure every node's Error Log and XEvent output is tagged with timestamp, hostname, and application name at minimum. In a distributed deployment, the hostname tag is essential — without it, cross-node correlation is guesswork."""),

# 6 postgresql.conf pre -> filebeat snippet
("""<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># postgresql.conf: structured log prefix for distributed environments
log_line_prefix = '{"time":"%t","pid":%p,"user":"%u","db":"%d","app":"%a","host":"%h"} '</code></pre>""",
 PRE + """# Ship each node's SQL Server Error Log with a host tag (Filebeat example)
filebeat.inputs:
- type: log
  paths: ['C:\\Program Files\\Microsoft SQL Server\\MSSQL*\\MSSQL\\Log\\ERRORLOG*']
  fields: { host.name: 'sql-node-01', log.type: 'sql-errorlog' }</code></pre>"""),

# 7 postgres_exporter
("""Prometheus with %s is the standard metrics pipeline for PostgreSQL clusters. In a distributed deployment, each node — primary, standbys, Citus workers — runs its own exporter.""" % code('postgres_exporter'),
 """A Prometheus exporter (or Azure Monitor / a third-party agent) is the standard metrics pipeline for SQL Server clusters. In a distributed deployment, each node — primary, secondaries — runs its own collector."""),

# 8 WAL generation
("""<span class="text-blue-400">→</span> WAL generation rate on the primary</li>""",
 """<span class="text-blue-400">→</span> Transaction log generation rate on the primary</li>"""),

# 9 replication slot retention
("""<span class="text-blue-400">→</span> Replication slot WAL retention (to catch runaway slots)</li>""",
 """<span class="text-blue-400">→</span> Log send queue size per secondary (to catch a replica falling behind)</li>"""),

# 10 max_connections
("""<span class="text-blue-400">→</span> Connection count vs. `max_connections` per node</li>""",
 """<span class="text-blue-400">→</span> Connection count vs. worker-thread pressure per node</li>"""),

# 11 takeaway replication
("""**Replication is the foundation of every distributed PostgreSQL and SQL Server deployment**, but replication type — physical vs. logical in PostgreSQL, transactional vs. AG-based in SQL Server — determines what operations are possible, what consistency guarantees apply, and what the operational overhead looks like.""",
 """**Replication is the foundation of every distributed SQL Server deployment**, but replication type — transactional vs. AG-based — determines what operations are possible, what consistency guarantees apply, and what the operational overhead looks like."""),

# 12 takeaway fencing
("""Quorum-based solutions (Patroni with etcd, WSFC with quorum) are the standard approach.""",
 """Quorum-based solutions (WSFC with quorum) are the standard approach."""),

# 13 takeaway observability
("""Replication lag, WAL retention by replication slots, cross-node query latency, and schema migration status across all nodes must be continuously monitored and alerted upon. The invisible failure — a replica quietly falling behind, a stale replication slot slowly filling the disk — is the distributed system's most insidious threat.""",
 """Replication lag, log send/redo queue growth, cross-node query latency, and schema migration status across all nodes must be continuously monitored and alerted upon. The invisible failure — a replica quietly falling behind, an unconsumed change feed slowly filling the disk — is the distributed system's most insidious threat."""),
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
    print(f'ch22b: all {len(REPLACEMENTS)} replacements applied')

main()
