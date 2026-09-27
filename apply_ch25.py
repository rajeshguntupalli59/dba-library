#!/usr/bin/env python3
"""Apply ch25 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch25-replication.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
H3 = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">%s</h3>'

LOG_TRANSPORT_SECTION = (
H3 % "How Availability Groups Move Data: Log Transport Under the Hood" + "\n\n" +
P + "An Availability Group looks like magic from the outside — write on the primary, read on the secondary — but underneath it is a log-shipping engine with precise, observable mechanics. Understanding those mechanics is what lets you diagnose lag, size secondaries, and predict failover behavior instead of guessing.</p>\n\n" +
P + "Everything starts with the transaction log. When a transaction commits on the primary, its log records are hardened to the primary's log disk first — durability is never outsourced. Then, in parallel, the primary ships <strong class=\"text-white\">log blocks</strong> (batches of log records, compressed in transit) to every secondary. Each secondary hardens the blocks to its own log disk and then <strong class=\"text-white\">redoes</strong> them — replaying the changes into its data files. Hardening and redo are separate stages, and that separation is the key to reading every replication metric correctly.</p>\n\n" +
P + "With <strong class=\"text-white\">synchronous commit</strong>, the primary waits until each synchronous secondary has hardened the log blocks before acknowledging the commit to the client. Note what it waits for: hardening, not redo. The secondary has the data durably; it just may not have applied it to data pages yet. With <strong class=\"text-white\">asynchronous commit</strong>, the primary ships the blocks and moves on — the secondary can fall arbitrarily far behind under a write burst, which is exactly what the send and redo queues measure.</p>\n\n" +
P + "Two queues tell the whole story, both visible in " + code('sys.dm_hadr_database_replica_states') + ". The <strong class=\"text-white\">log send queue</strong> (" + code('log_send_queue_size') + ") is log that the primary has hardened but not yet shipped — it grows when the network can't keep up or the secondary stops acknowledging. The <strong class=\"text-white\">redo queue</strong> (" + code('redo_queue_size') + ") is log the secondary has received but not yet applied — it grows when the secondary's I/O or redo thread can't keep pace. A growing send queue points at the network or the primary; a growing redo queue points at the secondary. Diagnose accordingly.</p>\n\n" +
'<div class="my-6 bg-gray-900 border border-gray-800 rounded-xl p-5 overflow-x-auto"><pre class="mermaid">sequenceDiagram\\n    participant P as Primary\\n    participant S1 as Sync secondary\\n    participant S2 as Async secondary\\n    P->>P: Transaction commits to local log\\n    P->>S1: Ship log blocks\\n    S1->>S1: Harden to log disk\\n    S1-->>P: Acknowledge hardened\\n    P->>P: Commit confirmed to client\\n    P->>S2: Ship log blocks (async, no wait)\\n    S2->>S2: Harden + redo</pre></div>\n\n' +
P + "*Figure: AG log transport — the primary waits for a synchronous secondary to harden log blocks before confirming the commit, while an asynchronous secondary receives the same stream without blocking the primary.*</p>\n\n" +
"<pre class=\"bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5\"><code>-- AG replication health: send and redo queues per database\nSELECT\n    ar.replica_server_name,\n    dbrs.database_name,\n    dbrs.synchronization_state_desc,\n    dbrs.log_send_queue_size,\n    dbrs.redo_queue_size,\n    dbrs.estimated_data_loss_seconds\nFROM sys.dm_hadr_database_replica_states dbrs\nJOIN sys.availability_replicas ar\n    ON dbrs.replica_id = ar.replica_id\nORDER BY dbrs.redo_queue_size DESC;</code></pre>\n\n" +
P + "One more mechanic with outsized operational impact: the transaction log on the primary cannot be truncated past the oldest log needed by any secondary. If a secondary disconnects for a day, the primary's log grows for a day — check " + code('log_reuse_wait_desc') + " and you will see " + code('AVAILABILITY_REPLICA') + " staring back at you. This is by design (you asked for no data loss), but it means a dead secondary is a disk-full incident waiting to happen. Monitor it like one.</p>\n\n" +
P + "---</p>"
)

REPLACEMENTS = [
# 1 intro
("""This chapter covers the replication mechanisms available in PostgreSQL and SQL Server, explains how they differ philosophically and technically, and builds toward the real-world decisions — configuration choices, monitoring strategies, failure handling, and latency management — that determine whether your replication setup holds up under production load or quietly degrades until it fails you at the worst possible moment.""",
 """This chapter covers the replication mechanisms available in SQL Server — Always On Availability Groups, transactional replication, and log shipping — and builds toward the real-world decisions — configuration choices, monitoring strategies, failure handling, and latency management — that determine whether your replication setup holds up under production load or quietly degrades until it fails you at the worst possible moment."""),

# 2 models
("""Before touching a single configuration file or wizard, it helps to understand the landscape of replication models, because both PostgreSQL and SQL Server offer multiple mechanisms, and choosing the wrong one for your workload can cost you months of rework.""",
 """Before touching a single configuration dialog or script, it helps to understand the landscape of replication models, because SQL Server offers multiple mechanisms, and choosing the wrong one for your workload can cost you months of rework."""),

# 3 physical
("""<strong class="text-white">Physical replication</strong> is byte-for-byte faithful. The replica will match the primary exactly, including indexes, vacuum maps, and system catalog entries. This makes physical replicas fast to set up and simple to reason about — you never have to worry about schema divergence. The downside is that a physical replica must run the same major version of the database software, cannot have a different schema, and cannot be used to replicate selectively. You replicate everything or nothing.""",
 """<strong class="text-white">Log-based replication</strong> — the model behind Availability Groups — is byte-for-byte faithful. The replica matches the primary exactly, including indexes and system catalog entries, because both apply the same transaction log records. This makes replicas simple to reason about: you never worry about schema divergence. The downside is that a log-based replica cannot have a different schema and cannot replicate selectively. You replicate the whole database or nothing."""),

# 4 logical
("""<strong class="text-white">Logical replication</strong> offers far more flexibility. You can replicate a single table, replicate to a different PostgreSQL major version, filter rows, or even replicate between heterogeneous systems. The trade-off is additional overhead and more opportunities for things to go wrong: schema changes on the publisher are not automatically propagated, sequences are not replicated, and large objects require special handling.""",
 """<strong class="text-white">Row-based replication</strong> — SQL Server's transactional replication — offers far more flexibility. You can replicate a single table, filter rows, or feed heterogeneous subscribers. The trade-off is additional overhead and more opportunities for things to go wrong: schema changes on the publisher are not automatically propagated, and identity ranges need explicit management across publisher and subscribers."""),

# 5 menu
("""SQL Server approaches replication with a broader menu of named technologies: <strong class="text-white">Always On Availability Groups</strong>, <strong class="text-white">Transactional Replication</strong>, <strong class="text-white">Merge Replication</strong>, <strong class="text-white">Snapshot Replication</strong>, and <strong class="text-white">Log Shipping</strong>. PostgreSQL offers <strong class="text-white">Streaming Replication</strong> (physical), <strong class="text-white">Logical Replication</strong>, and the ecosystem of extensions like <strong class="text-white">pglogical</strong> and tools like <strong class="text-white">Patroni</strong> that build on top of these primitives. The core mechanisms are more alike than they appear on the surface, but the interfaces, configuration models, and failure behaviors differ significantly.""",
 """SQL Server approaches replication with a menu of named technologies, each with a distinct job. <strong class="text-white">Always On Availability Groups</strong> are the high-availability and read-scale-out workhorse: whole databases, automatic failover, readable secondaries. <strong class="text-white">Transactional Replication</strong> moves selected tables and filtered rows to subscribers with low latency — the reporting-feed and data-distribution tool. <strong class="text-white">Merge Replication</strong> handles bidirectional sync for occasionally-connected clients. <strong class="text-white">Snapshot Replication</strong> refreshes whole copies on a schedule. <strong class="text-white">Log Shipping</strong> is the simple, robust DR primitive: scheduled log backups restored on a standby. Pick the mechanism that matches the problem; they compose poorly when forced into each other's roles."""),

# 6 block16 tail
("""with data synchronized via the transaction log — conceptually parallel to WAL-based streaming in PostgreSQL.""",
 """with data synchronized via the transaction log, as described in the previous section."""),

# 8 logical section -> transactional replication
("""Logical replication in PostgreSQL became a built-in feature in version 10, and it addresses use cases that physical streaming replication cannot — specifically, replicating a subset of tables, replicating between different major versions during an upgrade, and building custom data pipelines. SQL Server's Transactional Replication serves a similar function in the SQL Server ecosystem.""",
 """Transactional replication addresses use cases that Availability Groups cannot — replicating a subset of tables, filtering rows per subscriber, bridging versions during an upgrade, and feeding reporting servers or heterogeneous subscribers. Where an AG replicates whole databases for availability, transactional replication distributes selected data for consumption."""),

# 9 publisher/subscriber
("""PostgreSQL logical replication uses a <strong class="text-white">publisher/subscriber</strong> model. The publisher defines a <strong class="text-white">publication</strong> — a named collection of tables (or all tables in a schema) whose changes should be broadcast. The subscriber creates a <strong class="text-white">subscription</strong> pointing at a publisher's publication and begins consuming those changes.""",
 """Transactional replication uses a <strong class="text-white">publisher / distributor / subscriber</strong> model. The publisher defines <strong class="text-white">articles</strong> — tables or filtered row subsets — grouped into a <strong class="text-white">publication</strong>. The distributor (often co-located with the publisher) stores the changes; subscribers consume them. Two agents do the work: the <strong class="text-white">Log Reader Agent</strong> harvests committed transactions from the publication database's transaction log, and the <strong class="text-white">Distribution Agent</strong> applies them to each subscriber."""),

# 10 logical decoding
("""The mechanics behind PostgreSQL logical replication involve the <strong class="text-white">logical decoding</strong> infrastructure. When %s, PostgreSQL writes additional information into the WAL that makes it possible to reconstruct row-level changes rather than just page-level changes. The logical replication worker on the subscriber connects to the publisher, opens a replication slot, and receives a decoded stream of changes that it applies to local tables.""" % code('wal_level = logical'),
 """The Log Reader Agent scans the publication database's transaction log for marked transactions and writes them to the distribution database — it reads the log rather than using triggers, so the overhead on the publisher is modest. But the log cannot be truncated past the reader's position: a stalled Log Reader Agent grows the publisher's log, exactly like an AG secondary that stops receiving. Monitor the agent's latency and the log's reuse wait as a pair."""),

# 11 DDL
("""A key limitation to understand: logical replication in PostgreSQL does <strong class="text-white">not</strong> replicate DDL changes. If you %s on the publisher, that change must be manually applied on the subscriber before the replication stream attempts to apply rows with that column — otherwise the subscription will error out and stop. This is a fundamental operational difference from physical streaming replication, where DDL is just more WAL and gets replicated automatically.""" % code('ALTER TABLE orders ADD COLUMN discount_pct numeric'),
 """A key limitation to understand: schema changes are <strong class="text-white">not</strong> replicated by default. If you add a column on the publisher, apply it with %s / %s or enable schema-change replication on the publication — otherwise the subscriber's schema drifts and the Distribution Agent errors out on the first row referencing the new column. This is the fundamental operational difference from AGs, where DDL is just more log and replicates automatically.""" % (code('sp_repladdcolumn'), code('sp_repldropcolumn'))),

# 12 merge
("""Merge Replication, which SQL Server offers and PostgreSQL does not have a direct equivalent of, handles bidirectional synchronization where both publisher and subscriber can make changes that need to be reconciled.""",
 """Merge Replication handles bidirectional synchronization where both publisher and subscriber can make changes that need to be reconciled."""),

# 13 monitoring lag
("""The fundamental metric to watch is replication lag. In PostgreSQL, time-based lag (more meaningful than byte-based lag for most alerting purposes) became directly available in %s starting with PostgreSQL 10, in the %s, %s, and %s columns. These report how long ago the primary wrote data that the standby has yet to write, flush, or replay, respectively.""" % (code('pg_stat_replication'), code('write_lag'), code('flush_lag'), code('replay_lag')),
 """The fundamental metric to watch is replication lag. For AGs, %s exposes %s (log the primary hasn't shipped), %s (log the secondary hasn't applied), and %s for async replicas. Time-based alerting on redo-queue growth catches a struggling secondary before a failover becomes unsafe — a secondary with a ten-minute redo queue is ten minutes of potential data loss away from being a good failover target.""" % (code('sys.dm_hadr_database_replica_states'), code('log_send_queue_size'), code('redo_queue_size'), code('estimated_data_loss_seconds'))),

# 14 wal_compression
("""%s in PostgreSQL is worth enabling in most environments. It compresses full-page images in WAL (which can be verbose immediately after a checkpoint) and reduces the bandwidth consumed by replication. The CPU cost is usually negligible compared to the bandwidth savings.""" % code('wal_compression'),
 """AG log transport compresses log blocks in flight, so cross-datacenter bandwidth is rarely the bottleneck — but the send queue still grows when a write burst outpaces the link. When it does, the fix is reducing the burst (batch the load) or increasing the pipe, not a compression knob: there isn't one to turn."""),

# 15 alert li
("""Replication lag (bytes and time) exceeding thresholds — PostgreSQL alerts at >30s, page at >5min is a reasonable starting point""",
 """Replication lag (redo queue growth / estimated data loss) exceeding thresholds — alert at >30s, page at >5min is a reasonable starting point"""),

# 16 slots li
("""Replication slots that are inactive or whose lag exceeds a WAL retention limit (e.g., 10 GB)""",
 """Log send queues growing without bound — a secondary that stops acknowledging holds the primary's log from truncating; alert on log_send_queue_size and on log_reuse_wait_desc = 'AVAILABILITY_REPLICA'"""),

# 17 exporter
("""For PostgreSQL environments, integrating with Prometheus via %s makes all the %s metrics available as time-series data, which is invaluable for understanding lag trends over time. A lag spike that lasts two minutes during a nightly batch run is normal and acceptable; a spike that lasts two minutes every hour at random is a symptom that needs investigation.""" % (code('postgres_exporter'), code('pg_stat_replication')),
 """For trend analysis, ship the AG DMV metrics into your monitoring system — the Prometheus sql_exporter, Telegraf, or SCOM all expose them. A redo-queue spike that lasts two minutes during a nightly batch run is normal and acceptable; a spike that lasts two minutes every hour at random is a symptom that needs investigation."""),

# 18 standby maintenance
("""Planned maintenance on a physical standby in PostgreSQL — patching the OS, upgrading hardware — is straightforward: take it out of the pool, do the work, and bring it back. The standby will reconnect and stream forward from where it paused, as long as the WAL it needs has not been recycled (use replication slots to guarantee this). After a long maintenance window, you may need to increase %s or rely on a slot to ensure the primary retained enough WAL.""" % code('wal_keep_size'),
 """Planned maintenance on an AG secondary — patching the OS, upgrading SQL Server — is straightforward: if it's the primary, fail over first; do the work; fail back. Rolling through the replicas this way gives you zero-downtime patching, and the secondary simply resumes log transport where it paused when it rejoins."""),

# 19 promote
("""In PostgreSQL, promoting a standby to primary is accomplished either by calling %s from a session connected to the standby, or by creating a %s trigger file in the data directory (the legacy method, still functional). After promotion, the standby exits recovery mode, begins accepting writes, generates a new timeline, and starts advancing its own WAL sequence.""" % (code('pg_promote()'), code('promote')),
 """A planned manual failover is %s — the primary and a synchronous secondary coordinate so no committed data is lost, and the AG listener follows the role change. Automatic failover does the same without human intervention when the cluster detects a primary failure and quorum agrees.""" % code('ALTER AVAILABILITY GROUP [ag] FAILOVER')),

# 20 timelines
("""The timeline mechanism is a critical safety feature. When a new primary is promoted, it starts writing WAL on a new timeline identifier. Any old standbys that were connected to the original primary will refuse to follow the new primary's WAL if they detect a timeline conflict, preventing the split-brain scenario where two instances both believe they are primary and both accept writes. The DBA must explicitly reconfigure old standbys to follow the new primary, which typically involves either running %s to resync the standby's WAL history or rebuilding the standby from a base backup.""" % code('pg_rewind'),
 """Forced failover — allowing data loss — is the disaster option: the secondary comes online without the primary's cooperation, and any log that never arrived is gone. The old primary must never accept writes afterward; the cluster enforces this by removing it from membership, because a resurrected old primary taking writes is the classic split-brain. After a forced failover, the old primary cannot simply rejoin as a secondary — its log chain diverged, so it must be re-seeded (automatic seeding or backup/restore) before rejoining the AG."""),

# 21 pg_rewind
("""%s is a tool that compares the diverged standby's WAL history against the new primary and rewinds the standby's data directory to the point of divergence, then lets streaming replication fill in the gap. It is faster than a full base backup for standbys that are not far behind, but it requires that %s is enabled on the primary, or that checksums were enabled at initdb time.""" % (code('pg_rewind'), code('wal_log_hints')),
 """Automatic seeding handles the common case: when a replica rejoins after a divergence, SQL Server streams the database across and rebuilds it. For very large databases or slow links, seed from a backup instead — restore WITH NORECOVERY on the secondary and join it to the AG; log transport takes it from there."""),

# 22 promote code block -> T-SQL failover
("""-- PostgreSQL: Promote a standby to primary programmatically
-- (Connect to the standby)
SELECT pg_promote(wait := true, wait_seconds := 60);""",
 """-- Planned manual failover of an availability group (no data loss)
-- Run on the intended new primary (a synchronous secondary)
ALTER AVAILABILITY GROUP [ProductionAG] FAILOVER;

-- Forced failover after a primary disaster (allows data loss)
-- ALTER AVAILABILITY GROUP [ProductionAG] FORCE_FAILOVER_ALLOW_DATA_LOSS;"""),

# 23 checklist intro
("""For PostgreSQL, the post-failover checklist includes:""",
 """The post-failover checklist includes:"""),

# 24 checklist connection strings
("""1. <strong class="text-white">Update connection strings</strong> — application connection strings, pgBouncer or other pooler configurations, and monitoring agents must point to the new primary.""",
 """1. <strong class="text-white">Verify the listener follows</strong> — with the AG listener this is normally automatic, but direct-connect strings, linked servers, and monitoring agents that bypass the listener must point at the new primary."""),

# 25 checklist standbys
("""2. <strong class="text-white">Reconfigure or rebuild old standbys</strong> — use %s or a fresh base backup to bring old standbys into the new topology as followers of the new primary.""" % code('pg_rewind'),
 """2. <strong class="text-white">Re-seed the old primary</strong> — after a forced failover, rejoin it as a secondary via automatic seeding or a restored backup before trusting the topology again."""),

# 26 checklist WAL archiving
("""5. <strong class="text-white">Verify WAL archiving</strong> — if you use continuous archiving, ensure the archive_command or archive_library is correctly configured and functioning on the new primary.""",
 """5. <strong class="text-white">Verify log backups</strong> — ensure transaction log backup jobs are running against the new primary; a failover that nobody told the backup jobs about is how you discover gaps in the log chain during the next restore drill."""),

# 27 schema section intro
("""Schema changes in a replicated environment deserve their own section because they are the source of a disproportionate number of replication outages. The behavior of DDL under replication is fundamentally different between physical and logical replication, and between PostgreSQL and SQL Server.""",
 """Schema changes in a replicated environment deserve their own section because they are the source of a disproportionate number of replication outages. The behavior of DDL under replication is fundamentally different between Availability Groups and transactional replication."""),

# 28 physical DDL
("""Under <strong class="text-white">physical streaming replication</strong> in PostgreSQL, DDL is fully replicated — because physical replication copies WAL byte-for-byte and DDL is recorded in WAL just like DML. You can run %s, %s, or %s on the primary and it will automatically propagate to all physical standbys. There is no special handling required. The only subtlety is that long-running DDL on the primary may hold locks that block reads on the standby if the standby is being used for read queries, because the standby must replay the WAL including the lock acquisition.""" % (code('ALTER TABLE'), code('CREATE INDEX CONCURRENTLY'), code('DROP TABLE')),
 """Under <strong class="text-white">Availability Groups</strong>, DDL is fully replicated — AGs ship transaction log records, and DDL is logged just like DML. You can run %s, %s (including %s), or %s on the primary and it propagates to all secondaries automatically. There is no special handling required. The only subtlety is that long-running DDL holds schema locks that also block redo on the secondaries — a big index build can stall readable-secondary queries until it finishes.""" % (code('ALTER TABLE'), code('CREATE INDEX'), code('ONLINE'), code('DROP TABLE'))),

# 29 logical DDL
("""Under <strong class="text-white">logical replication</strong> in PostgreSQL, DDL is not replicated at all. The subscriber maintains its own schema independently. This means you must apply schema changes manually to the subscriber before the change is applied on the publisher — or at least before any DML arrives that references the new schema. The safe sequence for an additive change (adding a column) is:""",
 """Under <strong class="text-white">transactional replication</strong>, DDL is not replicated by default. The subscriber maintains its own schema, so apply schema changes with %s / %s or enable schema-change replication on the publication — before any DML arrives that references the new schema. The safe sequence for an additive change (adding a column) is:""" % (code('sp_repladdcolumn'), code('sp_repldropcolumn'))),

# 30 subscription status code -> tracer tokens
("""-- PostgreSQL: Check logical replication subscription status and errors
SELECT
    subname,
    subenabled,
    subslotname,
    subpublications,
    subconninfo
FROM pg_subscription;

-- Check for replication worker errors
SELECT
    pid,
    relid::regclass AS target_table,
    received_lsn,
    last_msg_send_time,
    last_msg_receipt_time,
    latest_end_lsn,
    latest_end_time
FROM pg_stat_subscription;""",
 """-- Post a tracer token to measure end-to-end replication latency
DECLARE @token INT;
EXEC sp_posttracertoken
    @publication = N'MyPublication',
    @tracer_token_id = @token OUTPUT;

-- Read back how long the token took through each agent
EXEC sp_helptracertokenhistory
    @publication = N'MyPublication',
    @tracer_id = @token;"""),

# 31 cascading
("""PostgreSQL supports cascading streaming replication natively. A standby in %s mode can itself act as a WAL sender to other standbys, as long as %s (or %s) is set on the upstream instance. This is particularly useful when the primary is bandwidth-constrained or geographically distant from a group of standbys: a single regional relay standby receives WAL from the primary and re-streams it locally to a cluster of readers, reducing the transcontinental bandwidth requirements.""" % (code('hot_standby'), code('wal_level = replica'), code('logical')),
 """AGs do not cascade: a secondary cannot forward log blocks to another secondary. For fan-out across sites, use a <strong class="text-white">distributed availability group</strong> — an AG of AGs, where a forwarder secondary on the remote site receives log blocks and feeds the remote AG's primary, which then fans out locally. One transcontinental stream instead of one per replica."""),

# 32 cascading code -> distributed AG check
("""-- PostgreSQL: A cascading standby's primary_conninfo points to an intermediate standby,
-- not the original primary. Check that the cascading standby is receiving WAL:
SELECT
    pg_is_in_recovery() AS is_standby,
    pg_last_wal_receive_lsn() AS received_lsn,
    pg_last_wal_replay_lsn() AS replayed_lsn,
    pg_wal_lsn_diff(
        pg_last_wal_receive_lsn(),
        pg_last_wal_replay_lsn()
    ) AS receive_replay_diff_bytes,
    now() - pg_last_xact_replay_timestamp() AS replay_lag
FROM pg_stat_replication -- run on the intermediate standby to see its downstreams
LIMIT 1;""",
 """-- On the distributed AG forwarder: confirm log is flowing to the remote AG
SELECT
    ar.replica_server_name,
    dbrs.database_name,
    dbrs.synchronization_state_desc,
    dbrs.log_send_queue_size,
    dbrs.redo_queue_size
FROM sys.dm_hadr_database_replica_states dbrs
JOIN sys.availability_replicas ar
    ON dbrs.replica_id = ar.replica_id
WHERE ar.replica_server_name = N'RemoteForwarder';"""),

# 33 fan-out
("""Fan-out topologies — where many subscribers consume from a single publisher — are straightforward in PostgreSQL logical replication. Each subscriber opens its own replication slot on the publisher and receives the same change stream independently. The concern with large fan-out is that each active slot consumes a WAL sender process (controlled by %s) and that all active slots must be kept current to prevent WAL accumulation. A publication with fifty subscribers, all of which must stay reasonably current, requires careful sizing of %s and %s.""" % (code('max_wal_senders'), code('max_wal_senders'), code('max_replication_slots')),
 """Fan-out topologies — where many subscribers consume from a single publisher — are straightforward in transactional replication, and subscribers can republish to build a tree. The concern with large fan-out is that each subscriber adds a Distribution Agent and another copy of the data to keep current. Keep trees shallow: every level adds latency and another distribution database to monitor."""),

# 34 zero-downtime upgrades
("""One of the most practically valuable applications of logical replication is enabling <strong class="text-white">zero-downtime major version upgrades</strong> of PostgreSQL. Because logical replication can stream changes between different major versions (subject to the subscriber running at least the minimum version that supports the relevant protocol), you can run the old and new versions in parallel and cut over with minimal downtime.""",
 """One of the most practically valuable patterns is the <strong class="text-white">rolling upgrade</strong> of an Availability Group. Patch the secondaries first, fail over, then patch the old primary: zero downtime, zero data movement, and the AG keeps serving throughout."""),

# 35 PG versions
("""1. Set up the new-version PostgreSQL instance (e.g., PostgreSQL 16) alongside the existing instance (e.g., PostgreSQL 14).""",
 """1. For a major version upgrade (e.g., SQL Server 2019 to 2022), build the new-version replicas alongside the existing AG and join them with a distributed availability group — the AG protocol supports mixed versions during the migration window."""),

# 36 pg_dump
("""2. Copy the initial data to the new instance using %s / %s or %s followed by a %s.""" % (code('pg_dump'), code('pg_restore'), code('pg_basebackup'), code('pg_upgrade')),
 """2. Seed the new replicas from a backup (restore WITH NORECOVERY) or automatic seeding, then let log transport keep them current until cutover."""),

# 37 wal_level logical
("""3. Set %s on the old primary and create a publication covering all tables to be migrated.""" % code('wal_level = logical'),
 """3. Fail over to the new version, verify the workload, then decommission the old side. Transactional replication can bridge the same gap for databases that can't take an AG: replicate from the old publisher to the new subscriber and cut over when lag is near zero."""),

# 38 split-brain PG
("""PostgreSQL's physical streaming replication by itself does not provide automatic failover. A standby will promote itself only if you tell it to (via %s or a trigger file), which means that if you are doing manual failover, split-brain requires human error — running promotion on the standby while the primary is actually still alive and reachable by clients. With automated failover managers like <strong class="text-white">Patroni</strong>, <strong class="text-white">repmgr</strong>, or <strong class="text-white">pg_auto_failover</strong>, split-brain prevention depends on the fencing mechanism the tool uses. Patroni, for example, uses a distributed consensus store (etcd, Consul, or ZooKeeper) to ensure that only one node holds the primary lease at any given time. If a node cannot reach the consensus store, it will demote itself rather than risk split-brain.""" % code('pg_promote()'),
 """AGs never fail over on replication state alone — failover decisions belong to the Windows Server Failover Cluster. Automatic failover requires synchronous commit plus cluster quorum; without quorum, no failover happens, which is the safe direction to fail. Manual failover during a real outage is how split-brain starts: forcing a secondary online while the old primary is still reachable by clients."""),

# 39 STONITH
("""A critically important Patroni concept is <strong class="text-white">STONITH</strong> ("Shoot The Other Node In The Head") or more generally <strong class="text-white">fencing</strong>: the ability to forcibly shut down or isolate a node that might still believe it is primary. Without fencing, even with a consensus store, there is a window during which the old primary might continue to accept writes from clients who have not yet learned of the failover. Fencing closes that window by ensuring the old primary is definitively stopped before the new primary begins accepting writes.""",
 """The cluster's equivalent of fencing: when a node loses quorum or fails its health check, the cluster evicts it from membership and the AG role moves. A node that cannot see quorum cannot become primary — this is what prevents split-brain during a network partition. The dangerous window is the one you create yourself with forced failover; treat %s as the break-glass it is, and re-establish quorum before trusting the topology again.""" % code('FORCE_FAILOVER_ALLOW_DATA_LOSS')),

# 40 Patroni check code -> AG role check
("""-- PostgreSQL: Check Patroni-managed cluster state (via REST API or patronictl)
-- From SQL, you can check whether the instance believes it is primary:
SELECT
    pg_is_in_recovery() AS is_replica,
    pg_postmaster_start_time() AS instance_start_time,
    inet_server_addr() AS listening_addr,
    current_setting('cluster_name') AS cluster_name;""",
 """-- Check what role each replica currently holds and its health
SELECT
    ar.replica_server_name,
    ars.role_desc,
    ars.operational_state_desc,
    ars.connected_state_desc
FROM sys.dm_hadr_availability_replica_states ars
JOIN sys.availability_replicas ar
    ON ars.replica_id = ar.replica_id;"""),

# 41 takeaway physical/logical
("""**Physical replication** (PostgreSQL streaming replication, SQL Server AG log shipping) replicates byte-level changes and produces identical replicas automatically, including DDL — but requires the same major version and schema on all nodes. **Logical replication** replicates row-level changes selectively, enabling cross-version upgrades and partial replication, but requires explicit DDL management on subscribers and does not replicate sequences.""",
 """**Log-based replication** (Availability Groups) ships transaction log records and produces identical replicas automatically, including DDL — but every replica shares the database's schema and version family. **Row-based replication** (transactional replication) replicates selectively and can bridge versions, but requires explicit DDL management and has no automatic failover."""),

# 42 takeaway lag
("""**Replication lag** is the central operational metric for any replicated environment. Monitor it in time-based units (PostgreSQL's `write_lag`, `flush_lag`, `replay_lag`; SQL Server's `estimated_data_loss_seconds` and `redo_queue_size`), alert on thresholds appropriate for your RPO, and investigate systematically — spikes trace to write bursts, standby I/O saturation, or network bandwidth constraints.""",
 """**Replication lag** is the central operational metric for any replicated environment. Monitor log_send_queue_size, redo_queue_size, and estimated_data_loss_seconds; alert on thresholds appropriate for your RPO; and investigate systematically — spikes trace to write bursts, secondary I/O saturation, or network bandwidth constraints."""),

# 43 takeaway slots
("""**Replication slots** in PostgreSQL guarantee WAL retention for downstream consumers but introduce a disk-filling risk if a slot consumer goes offline. Always monitor slot lag with alerting, and consider whether unmonitored slots should be dropped rather than left dormant indefinitely.""",
 """**A stalled secondary holds the primary's log hostage.** Whether it's an AG secondary that stopped receiving or a Log Reader Agent that stopped reading, log_reuse_wait_desc tells you who is blocking truncation. Alert on it — an unmonitored stall fills the log disk."""),

# 44 takeaway split-brain
("""**Split-brain prevention requires a fencing or quorum mechanism** beyond replication itself. PostgreSQL deployments using automated failover tools like Patroni depend on a distributed consensus store and STONITH/fencing to ensure only one primary is active at any time. SQL Server AGs rely on WSFC quorum. Understanding how your specific tooling prevents split-brain — and what happens to it during a partial network partition — is not optional knowledge for a DBA responsible for a high-availability database.""",
 """**Split-brain prevention requires quorum, not just replication.** AG automatic failover depends on WSFC quorum — understand what happens to failover during a partial network partition before it happens to you in production."""),
]

def main():
    text = open(PATH).read()
    # Surgery 1: replace PG streaming section with AG log-transport section.
    idx_a = text.index('Streaming Replication in PostgreSQL')
    start = text.rindex('<h3', 0, idx_a)
    idx_b = text.index('Always On Availability Groups in SQL Server')
    end = text.rindex('<h3', 0, idx_b)
    text = text[:start] + LOG_TRANSPORT_SECTION + '\n\n' + text[end:]
    # Surgery 2: remove the redundant PG "equivalent" code block.
    idx_c = text.index('-- PostgreSQL equivalent: check streaming replication state')
    pre_start = text.rindex('<pre', 0, idx_c)
    pre_end = text.index('</code></pre>', idx_c) + len('</code></pre>')
    text = text[:pre_start] + text[pre_end:]
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch25: 2 surgeries + all {len(REPLACEMENTS)} replacements applied')

main()
