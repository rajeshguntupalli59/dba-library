#!/usr/bin/env python3
"""Apply ch22 prose rewrites. Fails loudly on any non-unique match."""
import re, sys

PATH = '/home/hatch/workspace/dba-library/book/ch22-distributed.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
H3 = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">%s</h3>'
PRE_OPEN = '<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>'

def para_start(text, idx):
    return text.rindex(P, 0, idx)

def main():
    text = open(PATH).read()

    # ---- A. Replication section: consolidate to SQL Server, re-embed the two existing pre blocks ----
    h3_rep = text.index('Replication Architecture in PostgreSQL and SQL Server')
    h3_start = text.rindex('<h3', 0, h3_rep)
    op_para = text.index('One important operational distinction')
    op_start = para_start(text, op_para)
    seg = text[h3_start:op_start]
    pres = re.findall(r'<pre class="bg-gray-900.*?</code></pre>', seg, re.DOTALL)
    assert len(pres) == 2, f'expected 2 pre blocks in replication section, found {len(pres)}'
    new_rep = (
        H3 % "Replication Architecture in SQL Server" + "\n\n" +
        P + "Replication is the foundation of most distributed database deployments. SQL Server offers several replication types plus Availability Groups, and choosing between them depends on the workload and failure model.</p>\n\n" +
        P + "<strong class=\"text-white\">Transactional replication</strong> is the workhorse for low-latency data propagation. The Log Reader Agent reads committed transactions from the publication database's transaction log and stores them in the distribution database; Distribution Agents then deliver those changes to subscribers. Unlike log-level replication, transactional replication is selective — specific tables, columns, or even filtered rows can be included in a publication. Monitor delivery latency in " + code('distribution.dbo.MSdistribution_status') + ":</p>\n\n" +
        pres[0] + "\n\n" +
        P + "<strong class=\"text-white\">Always On Availability Groups</strong> replicate at the log block level: an AG groups databases together and synchronizes them to secondary replicas. Readable secondaries allow read workloads to be offloaded via " + code('ApplicationIntent=ReadOnly') + " routing. Automatic failover can be configured for synchronous replicas within the same data center, while asynchronous replicas in remote data centers serve as disaster recovery targets. Monitor send/redo queues per database per replica — growing queues are your early warning:</p>\n\n" +
        pres[1] + "\n\n"
    )
    text = text[:h3_start] + new_rep + text[op_start:]

    # ---- B. Mermaid: Citus coordinator -> shard-map router ----
    old_mermaid = '''    Client["Application"] --> Coordinator["Coordinator / Router\\n(Citus coordinator, shard map)"]
    Coordinator -->|shard key hash 0-33| Shard1[("Shard 1\\nusers 1-1M")]
    Coordinator -->|shard key hash 34-66| Shard2[("Shard 2\\nusers 1M-2M")]
    Coordinator -->|shard key hash 67-100| Shard3[("Shard 3\\nusers 2M-3M")]
    Coordinator -.->|cross-shard query:\\nscatter-gather| Shard1
    Coordinator -.-> Shard2
    Coordinator -.-> Shard3'''
    new_mermaid = '''    App["Application"] --> Router["Shard map / router\\n(shard key → shard DB)"]
    Router -->|customer_id 1-1M| Shard1[("Shard DB 1")]
    Router -->|customer_id 1M-2M| Shard2[("Shard DB 2")]
    Router -->|customer_id 2M-3M| Shard3[("Shard DB 3")]
    Router -.->|cross-shard query:\\nscatter-gather| Shard1
    Router -.-> Shard2
    Router -.-> Shard3'''
    assert text.count(old_mermaid) == 1
    text = text.replace(old_mermaid, new_mermaid, 1)

    # ---- C. 'PostgreSQL and Sharding' subsection -> shard-map pattern ----
    idx = text.index('<strong class="text-white">PostgreSQL and Sharding</strong>')
    start = para_start(text, idx)
    idx_next = text.index('PostgreSQL (with declarative partitio')
    end = para_start(text, idx_next)
    new_shard = (
        P + "<strong class=\"text-white\">Sharding with SQL Server: the Shard-Map Pattern</strong></p>\n\n" +
        P + "SQL Server has no native sharding, so sharded designs use the <strong class=\"text-white\">shard-map pattern</strong>: a small metadata database maps each shard-key range to a shard database, and the application (or data-access library) resolves the shard per request. Azure SQL's Elastic Database client library implements this with shard maps, and elastic jobs run schema changes and maintenance across all shards. The honest guidance stands: you probably don't need sharding — a single well-tuned primary handles enormous write throughput, and most systems never reach its limit.</p>\n\n" +
        P + "When you do shard, the shard key is the entire design. Every hot-path query must filter on the shard key so it resolves to exactly one shard; queries that can't are scatter-gather across all shards and don't scale. Co-locate related tables on the same key (orders and order_items both sharded by customer_id) so joins stay single-shard. And design for re-sharding from day one — a split/merge procedure that moves a key range to a new shard — because your initial shard boundaries will be wrong.</p>\n\n"
    )
    text = text[:start] + new_shard + text[end:]

    # ---- D. PG sharding code example -> T-SQL shard-map example ----
    idx = text.index('PostgreSQL (with declarative partitioning as a foundation for sharding logic):')
    start = para_start(text, idx)
    pre_s = text.index('<pre class=', start)
    pre_e = text.index('</code></pre>', pre_s) + len('</code></pre>')
    new_example = (
        P + "<strong class=\"text-white\">T-SQL shard-map example:</strong></p>\n\n" +
        PRE_OPEN + """-- Shard map: which key ranges live on which shard database
CREATE TABLE dbo.ShardMap (
    ShardID      INT NOT NULL PRIMARY KEY,
    ShardName    SYSNAME NOT NULL,   -- connection target for this shard
    KeyRangeLow  BIGINT NOT NULL,
    KeyRangeHigh BIGINT NOT NULL,
    IsOnline     BIT NOT NULL DEFAULT (1)
);

-- Resolve the shard for a customer (called by the data-access layer)
CREATE FUNCTION dbo.GetShardForCustomer(@CustomerID BIGINT)
RETURNS SYSNAME
AS BEGIN
    RETURN (SELECT TOP (1) ShardName
            FROM dbo.ShardMap
            WHERE @CustomerID BETWEEN KeyRangeLow AND KeyRangeHigh
              AND IsOnline = 1);
END;</code></pre>\n\n"""
    )
    text = text[:start] + new_example + text[pre_e:]

    # ---- E. PG Prepared Transactions -> in-doubt/MSDTC recovery ----
    idx = text.index('<strong class="text-white">PostgreSQL Prepared Transactions</strong>')
    start = para_start(text, idx)
    idx_next = text.index('SQL Server Distributed Transactions')
    end = para_start(text, idx_next)
    new_2pc = (
        P + "<strong class=\"text-white\">In-Doubt Transactions and MSDTC Recovery</strong></p>\n\n" +
        P + "The failure mode that pages DBAs is the in-doubt transaction: the coordinator crashed after prepare but before the commit decision reached every participant, leaving locks held indefinitely. In " + code('sys.dm_tran_active_transactions') + " these show a non-null " + code('dtc_state') + " that never advances. The MSDTC coordinator normally recovers them on restart by replaying its log — so the first response is to check whether the coordinator host is actually down, not to kill things. If the coordinator is permanently gone, the DBA must determine the correct outcome from application logs and resolve each transaction manually; there is no safe automatic choice between commit and rollback, which is exactly why 2PC is a last resort.</p>\n\n"
    )
    text = text[:start] + new_2pc + text[end:]

    # ---- F. PG network-partition subsection -> AG partition behavior ----
    idx = text.index('PostgreSQL: Checking for Network Partition Effects')
    start = para_start(text, idx)
    idx_next = text.index('SQL Server: Detecting AG Communicatio')
    end = para_start(text, idx_next)
    new_part = (
        P + "In SQL Server, the same instability shows up in " + code('sys.dm_hadr_availability_replica_states') + ": replicas flap between CONNECTED and DISCONNECTED, " + code('last_connect_error_number') + " records the cause, and " + code('synchronization_health_desc') + " degrades. A replica that can't be reached holds its log send queue — on the primary, watch " + code('log_send_queue_size') + " grow as the backpressure signal. The diagnostic query in the SQL Server subsection below surfaces exactly this.</p>\n\n"
    )
    text = text[:start] + new_part + text[end:]

    # ---- G. Citus co-location example -> Synapse distribution example ----
    idx = text.index('<strong class="text-white">Citus co-location example:</strong>')
    start = para_start(text, idx)
    pre_s = text.index('<pre class=', start)
    pre_e = text.index('</code></pre>', pre_s) + len('</code></pre>')
    new_coloc = (
        P + "<strong class=\"text-white\">Synapse distribution example:</strong></p>\n\n" +
        PRE_OPEN + """-- Hash-distribute both tables on customer_id: joins stay local per distribution
CREATE TABLE dbo.orders
WITH (DISTRIBUTION = HASH(customer_id))
AS SELECT * FROM staging.orders;

CREATE TABLE dbo.order_items
WITH (DISTRIBUTION = HASH(customer_id))
AS SELECT * FROM staging.order_items;

-- This join executes locally on each distribution - no cross-node data movement
SELECT o.order_id, o.order_date,
       SUM(oi.quantity * oi.unit_price) AS total
FROM dbo.orders o
JOIN dbo.order_items oi ON o.order_id = oi.order_id
                       AND o.customer_id = oi.customer_id
WHERE o.customer_id = 98765
GROUP BY o.order_id, o.order_date;</code></pre>\n\n"""
    )
    text = text[:start] + new_coloc + text[pre_e:]

    # ---- H. 'For PostgreSQL workloads' managed subsection -> SQL Server options ----
    idx = text.index('<strong class="text-white">For PostgreSQL workloads</strong>')
    start = para_start(text, idx)
    idx_next = text.index('<strong class="text-white">For SQL Server workloads</strong>')
    end = para_start(text, idx_next)
    new_managed = (
        P + "For SQL Server workloads, the managed options span a spectrum: <strong class=\"text-white\">Azure SQL Database Hyperscale</strong> for storage-compute separation with fast failover, <strong class=\"text-white\">elastic pools</strong> for multi-tenant SaaS scale, and <strong class=\"text-white\">Azure SQL Managed Instance</strong> for near-on-premises parity (including AG-like HA) without managing the cluster. Choose by control needs: Hyperscale for elastic growth, Managed Instance for lift-and-shift with minimal re-architecture.</p>\n\n"
    )
    text = text[:start] + new_managed + text[end:]

    REPLACEMENTS = [
    # 1 intro
    ("""This chapter examines how PostgreSQL and SQL Server approach distributed architectures:""",
     """This chapter examines how SQL Server approaches distributed architectures:"""),
    # 2 CAP
    ("""PostgreSQL's native streaming replication sits toward the CP end when synchronous commit is required: the primary waits for at least one standby to acknowledge a WAL record before confirming the transaction to the client.""",
     """SQL Server's Availability Groups sit toward the CP end when synchronous commit is required: the primary waits for at least one synchronous secondary to harden the log record before confirming the transaction to the client."""),
    # 7 active-active BDR
    ("""PostgreSQL does not natively support active-active multi-master replication. The ecosystem solutions are BDR (Bi-Directional Replication), provided by EDB (EnterpriseDB), and Citus. BDR implements last-write-wins (LWW) conflict resolution by default, with hooks for custom conflict handlers. It uses logical replication extended to propagate changes in both directions between nodes. Conflicts are detected by comparing transaction timestamps from a clock synchronization layer.""",
     """SQL Server has no native multi-master: the supported patterns are conflict-avoidance designs — shard-per-region (each region owns its writes), or distributed availability groups with a single global primary. True active-active with conflict resolution belongs in the application layer, not the database."""),
    # 34 multi-region PG
    ("""PostgreSQL achieves this with streaming replication across regions. The primary is in one availability zone or data center; standbys in each remote region connect and replay WAL. A connection pooler or load balancer in each region routes read queries to the local standby and write queries to the primary.""",
     """Tune the tradeoff per replica: synchronous commit within a region for zero data loss, asynchronous across regions for latency — and treat the async replica's send queue as your RPO meter. A listener or traffic manager in each region routes reads to the local secondary and writes to the primary."""),
    # 36 Citus/Synapse
    ("""Citus (PostgreSQL) and Azure Synapse Analytics (SQL Server's distributed analytics engine) both implement distributed query planners that optimize this problem.""",
     """Azure Synapse Analytics (SQL Server's distributed analytics engine) implements a distributed query planner that optimizes this problem."""),
    # 38 coordinator bottleneck
    ("""When queries cannot be co-located — for example, a report that aggregates across all customers — Citus parallelizes execution across all workers and merges results on the coordinator.""",
     """When queries cannot be co-located — for example, a report that aggregates across all customers — Synapse parallelizes execution across all distributions and merges results on the control node."""),
    # 39 both platforms
    ("""The consistent theme across both platforms is that distributed query processing requires the DBA and data architect to deeply understand where data lives""",
     """The consistent theme is that distributed query processing requires the DBA and data architect to deeply understand where data lives"""),
    # 40 PG ALTER TABLE
    ("""PostgreSQL's %s with a default value that requires a table rewrite was historically a long-blocking operation. Since PostgreSQL 11, adding a column with a non-volatile default does not require a table rewrite and takes only a brief lock. This makes expand operations much faster. However, adding a NOT NULL constraint without a default still requires scanning the entire table.""" % code('ALTER TABLE ... ADD COLUMN'),
     """SQL Server's %s with a default is a metadata-only operation — the default is stored, not written to every row — which makes expand operations fast. However, adding a NOT NULL constraint without a default still scans the entire table: add the column nullable, backfill in batches, then alter to NOT NULL.""" % code('ALTER TABLE ... ADD COLUMN')),
    # 41 pg_repack
    ("""Tools like %s and %s-based online migrations are commonly used in Citus or manual sharding deployments to apply schema changes with minimal downtime.""" % (code('pg_repack'), code('pglogical')),
     """For large tables, ONLINE index rebuilds and resumable operations apply schema changes with minimal downtime; in sharded deployments, roll the change out shard by shard behind the shard map so a bad migration can be halted before it reaches every shard."""),
    # 43 tracing
    ("""In a distributed application, a single user request may touch a connection pooler, the coordinator node of a Citus cluster, multiple worker nodes, and then an application server. Understanding the latency breakdown requires distributed tracing — each component emitting spans that can be correlated by a shared trace ID. OpenTelemetry is the emerging standard for this. PostgreSQL itself does not yet emit OpenTelemetry spans natively, but instrumentation can be added at the connection pooler layer (PgBouncer, pgcat) and at the application layer.""",
     """In a distributed application, a single user request may touch a connection pool, the shard router, multiple shard databases, and then an application server. Understanding the latency breakdown requires distributed tracing — each component emitting spans that can be correlated by a shared trace ID. OpenTelemetry is the emerging standard for this: instrument at the driver/pooler layer and the application layer, and use Extended Events and Query Store for the database-side spans."""),
    # STONITH
    ("""**STONITH (Shoot The Other Node In The Head)**: Physically power off or network-isolate the old primary before promotion proceeds. Used in Linux Pacemaker clusters with PostgreSQL.""",
     """**Node isolation via WSFC**: the cluster service fences the failed node so it cannot accept writes; a former primary that recovers without quorum stays offline rather than coming back as a rogue primary."""),
    # lease-based fencing / Patroni
    ("""**Lease-based fencing**: The primary holds a time-limited lease from a consensus system (like etcd or ZooKeeper). Patroni, the most widely deployed PostgreSQL HA solution, uses this approach. If the primary cannot renew its lease, it fences itself by stopping write acceptance.""",
     """**Lease-based fencing**: The primary holds a time-limited lease; if it cannot renew, it fences itself by stopping write acceptance. AGs achieve the same effect through quorum — a primary that loses quorum takes its databases offline rather than accepting writes it can't replicate."""),
    # Patroni architecture
    ("""Patroni's architecture is worth understanding in detail because it represents production-grade PostgreSQL HA. Patroni uses etcd, Consul, or ZooKeeper as a distributed consensus store. The current primary continuously updates a key in that store. If the primary fails to update the key within a configurable TTL, standby nodes race to acquire the leader key. The winner promotes itself to primary. The loser becomes a standby of the new primary. The former primary, if it recovers, finds that it cannot acquire the leader key and fences itself by refusing connections. No human intervention is required for a clean failover, typically completing in 10–30 seconds.""",
     """AG automatic failover is worth understanding in detail because it represents production-grade SQL Server HA. It requires synchronous commit, automatic failover configured on the replicas, and a healthy WSFC quorum. When the primary's heartbeat fails, the cluster verifies quorum majority, then the chosen synchronous secondary transitions to primary — typically completing in 10–30 seconds with no human intervention. The former primary, if it recovers, cannot accept writes: without quorum it stays offline, which is the fencing."""),
    # pg_stat_replication lag
    ("""The %s view on PostgreSQL (shown earlier) exposes the LSN positions of every connected standby. The difference between the primary's current WAL position and a standby's replay LSN is the lag, expressed in bytes. Dividing this by the replication rate gives an estimate in time, though replication rate is variable.""" % code('pg_stat_replication'),
     """SQL Server's %s exposes %s and %s per database per replica — the lag in bytes. Dividing by %s / %s estimates the lag in time, though replication rate is variable; alert on the byte counts directly, since they don't lie.""" % (code('sys.dm_hadr_database_replica_states'), code('log_send_queue_size'), code('redo_queue_size'), code('log_send_rate'), code('redo_rate'))),
    # RYW LSN
    ("""PostgreSQL provides %s on the primary and %s on standbys. Application-level RYW logic can capture the LSN at write time and wait until a chosen replica reaches that LSN before redirecting reads.""" % (code('pg_current_wal_lsn()'), code('pg_last_wal_replay_lsn()')),
     """For application-level read-your-writes, capture the primary's commit time at write time and poll the secondary's %s in %s until it catches up before redirecting reads there — or simpler, route read-after-write requests to the primary for a short window.""" % (code('last_commit_time'), code('sys.dm_hadr_database_replica_states'))),
    # causal consistency
    ("""CockroachDB and YugabyteDB (both PostgreSQL-compatible distributed databases) implement causal consistency at the engine level. PostgreSQL itself, when used with a single primary, provides full linearizability for transactions on that primary; it is only in the multi-primary or replica-read path that these weaker consistency models become relevant.""",
     """SQL Server, when used with a single primary, provides full linearizability for transactions on that primary; it is only in the replica-read path that these weaker consistency models become relevant — which is why read-your-writes routing matters for user-facing reads after writes."""),
    ]

    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)

    # ---- PG code block 42 (ALTER TABLE orders ADD COLUMN ...) ----
    idx = text.index('-- PostgreSQL: Add column safely')
    start = text.rindex('<pre class=', 0, idx)
    pre_e = text.index('</code></pre>', start) + len('</code></pre>')
    new_col = (
        PRE_OPEN + """-- SQL Server: add a NOT NULL column to a large table without a long blocking scan
-- Step 1: add as nullable (metadata-only)
ALTER TABLE dbo.orders ADD priority_level INT NULL;

-- Step 2: backfill in batches to avoid log explosion
WHILE (1 = 1)
BEGIN
    UPDATE TOP (10000) dbo.orders
    SET priority_level = 0
    WHERE priority_level IS NULL;
    IF @@ROWCOUNT = 0 BREAK;
END;

-- Step 3: enforce NOT NULL once no nulls remain
ALTER TABLE dbo.orders ALTER COLUMN priority_level INT NOT NULL;</code></pre>"""
    )
    text = text[:start] + new_col + text[pre_e:]

    open(PATH, 'w').write(text)
    print(f'ch22: surgeries + all {len(REPLACEMENTS)} replacements applied')

main()
