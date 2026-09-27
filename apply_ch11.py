#!/usr/bin/env python3
"""Apply ch11 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch11-high-availability.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

FCI_SECTION = """<h3 class="text-lg font-semibold text-white mt-8 mb-3">Failover Cluster Instances and the WSFC Foundation</h3>

<p class="text-gray-300 leading-relaxed">Before Availability Groups, there was the <strong class="text-white">Failover Cluster Instance (FCI)</strong> — and it remains the right answer for a large class of workloads. An FCI is a single SQL Server instance installed across multiple WSFC nodes with shared storage. Only one node owns the instance at a time; on failure, the cluster moves the instance and its disks to a surviving node and restarts SQL Server there. Because the data files are shared, there is exactly one copy of the data — an FCI protects against server failure, not against storage failure or database corruption.</p>

<p class="text-gray-300 leading-relaxed">Everything in SQL Server HA sits on <strong class="text-white">Windows Server Failover Clustering (WSFC)</strong>, which provides cluster membership, heartbeat monitoring, and resource orchestration. The concept that matters most is <strong class="text-white">quorum</strong>: the cluster can only function when a majority of votes is reachable. Votes come from nodes plus an optional witness — a disk witness, file-share witness, or cloud witness. Lose quorum and the cluster stops everything rather than risk split-brain; this is by design. The most common HA outage pattern isn't a failed node, it's a failed quorum configuration — a two-node cluster with no witness goes down when either node fails, which is exactly when you needed it most.</p>

<p class="text-gray-300 leading-relaxed">The FCI vs. AG decision comes down to what you're protecting. Choose an FCI when you need instance-level protection (all databases, logins, and Agent jobs fail over together), when shared storage is already available, or when the workload includes databases that can't join an AG. Choose an AG when you need database-level failover, readable secondaries, no shared storage, or geographic distribution. Many estates run both: FCIs for the instance-level safety net, AGs for database-level granularity and read scale-out.</p>

<p class="text-gray-300 leading-relaxed">One operational note: FCI failover restarts the SQL Server service on the new node, so the buffer pool, plan cache, and tempdb are all cold — expect a warm-up period of slow queries after every failover. AG failover doesn't restart the service on the secondary (it's already running), so warm-up is limited to redo catch-up. Size your RTO estimates accordingly, and test both — a failover you've never rehearsed is a hope, not a plan.</p>
"""

REPLACEMENTS = [
# 1 intro
("""This chapter covers what high availability actually means for PostgreSQL and SQL Server environments, how each platform approaches the problem architecturally, and how to build, monitor, and maintain HA systems that survive the failures you expect and the ones you don't.""",
 """This chapter covers what high availability actually means for SQL Server environments, how the platform approaches the problem architecturally, and how to build, monitor, and maintain HA systems that survive the failures you expect and the ones you don't."""),

# 2 architectural histories
("""PostgreSQL and SQL Server approach HA differently because of their architectural histories. PostgreSQL is a single-primary system at its core — writes go to one node and are replicated to standbys. SQL Server grew up in a Windows-first, cluster-aware environment and has deeper integration with the Windows Server Failover Clustering (WSFC) infrastructure. Both platforms have mature HA solutions, but they make different tradeoffs, and understanding those tradeoffs is what separates a DBA who configures HA from one who truly operates it.""",
 """SQL Server approaches HA from its Windows-first, cluster-aware history, with deep integration into Windows Server Failover Clustering (WSFC). The platform offers two mature HA technologies — Failover Cluster Instances and Always On Availability Groups — that make different tradeoffs, and understanding those tradeoffs is what separates a DBA who configures HA from one who truly operates it."""),

# 3 replication foundations intro
("""Before configuring any HA solution, you need to understand how replication moves data from a primary to a standby, because every HA technology in both platforms is built on replication. The mechanism underneath determines your RPO, your failover characteristics, and your performance overhead.""",
 """Before configuring any HA solution, you need to understand how data gets to a standby, because every SQL Server HA technology is built on log-based replication or shared storage. The mechanism underneath determines your RPO, your failover characteristics, and your performance overhead."""),

# 4 WAL -> transaction log
("""PostgreSQL uses <strong class="text-white">Write-Ahead Logging (WAL)</strong> as the foundation for all replication. Every change made to the database — inserts, updates, deletes, DDL — is first written to the WAL before it is applied to the heap files. WAL is an ordered, sequential log. Streaming replication sends this WAL stream from the primary to one or more standby servers in near real time. The standby continuously applies WAL records, keeping its data files in sync with the primary. This is called <strong class="text-white">physical replication</strong> because the standby is a byte-for-byte copy of the primary — same data files, same tablespace layout, same PostgreSQL major version.""",
 """SQL Server's <strong class="text-white">transaction log</strong> is the foundation for log-based HA. Every change — inserts, updates, deletes, DDL — is first written to the transaction log before being applied to data files. In an Availability Group, log records stream from the primary to secondaries in near real time, and each secondary replays (redoes) them in order. A secondary holds a full copy of the participating databases — same data, independently readable, at the same SQL Server version."""),

# 5 log shipping / AG evolution
("""SQL Server's equivalent is <strong class="text-white">transaction log shipping</strong> and <strong class="text-white">log-based replication</strong>, but the more sophisticated HA mechanisms use <strong class="text-white">Always On Availability Groups</strong>, which also rely on the transaction log. Every write in SQL Server goes through the transaction log first. In an Availability Group, log records are sent from the primary replica to secondary replicas, which apply them in order. The log transport mechanism is similar in spirit to PostgreSQL streaming replication, but the implementation and configuration surface are quite different.""",
 """<strong class="text-white">Log shipping</strong> — scheduled transaction-log backups copied to a standby and restored on a schedule — is the simplest log-based HA: cheap, robust, but with failover measured in minutes and no automatic failover. <strong class="text-white">Always On Availability Groups</strong> are the sophisticated evolution: continuous log transport, automatic failover coordinated by WSFC, and readable secondaries. Everything that follows builds on the log-streaming foundation above."""),

# 6 sync replication WAL mention
("""With synchronous replication, a transaction on the primary does not commit until at least one standby has confirmed it has received and written (and in some modes, applied) the WAL or log records for that transaction.""",
 """With synchronous replication, a transaction on the primary does not commit until at least one standby has confirmed it has received and hardened the log records for that transaction."""),

# 7 async WAL mention
("""With asynchronous replication, the primary commits immediately after writing locally. The WAL is shipped to standbys in the background, and there is always a lag — however small — between the primary and the standby.""",
 """With asynchronous replication, the primary commits immediately after writing locally. Log records ship to secondaries in the background, and there is always a lag — however small — between the primary and the secondary."""),

# 8 pg_stat_replication -> DMV
("""The %s, %s, and %s columns in PostgreSQL's %s tell you different things. Write lag is the time from when a WAL record was sent until the standby confirmed writing it to its WAL files. Flush lag adds the requirement that the standby flushed it to durable storage. Replay lag is the time until the standby actually applied the change to its data files. For synchronous standbys, you care most about flush lag — that is what the primary waits for before committing. For asynchronous standbys, replay lag tells you how stale the standby's data is.""" % (code('write_lag'), code('flush_lag'), code('replay_lag'), code('pg_stat_replication')),
 """The %s DMV tells you the health of each replica database: %s (records waiting to leave the primary), %s, %s (records waiting to be redone on the secondary), and %s. For synchronous replicas, watch the send queue — that's what the primary waits on before committing. For asynchronous replicas, the redo queue tells you how stale the secondary's data is.""" % (code('sys.dm_hadr_database_replica_states'), code('log_send_queue_size'), code('log_send_rate'), code('redo_queue_size'), code('redo_rate'))),

# 9 lag subtlety
("""One subtlety that catches DBAs off guard in PostgreSQL: replication lag is not just about network bandwidth. The standby can fall behind because it cannot apply WAL records fast enough — this happens when the standby is under heavy query load (read replicas serving reports, for example) and the WAL apply process is competing for I/O. This is a performance problem, not a network problem, and the fix is different.""",
 """One subtlety that catches DBAs off guard: replication lag is not just about network bandwidth. A secondary can fall behind because it can't redo log records fast enough — this happens when a readable secondary is under heavy query load (serving reports) and redo competes for I/O, or when a long-running read query blocks redo. This is a performance problem, not a network problem, and the fix is different."""),

# 18 listener HAProxy comparison
("""This is the SQL Server equivalent of HAProxy routing to the Patroni leader, but it is built into the platform and managed by the cluster infrastructure.""",
 """This is built into the platform and managed by the cluster infrastructure — no proxy layer required. After a failover, the listener IP moves to the new primary, and applications reconnect to the same name without a configuration change."""),

# 19 read-intent PG comparison
("""One feature worth understanding that has no direct PostgreSQL equivalent is the <strong class="text-white">readable secondary with read-intent routing</strong>.""",
 """One feature worth understanding deeply is the <strong class="text-white">readable secondary with read-intent routing</strong>."""),

# 20 Patroni fencing -> WSFC fencing
("""In Patroni, the DCS lock mechanism provides the fencing guarantee. When the old primary cannot refresh its leader lock — because it crashed, lost network connectivity, or is running too slowly — the lock expires. At that moment, the old primary loses the ability to write to the DCS and therefore loses the right to be primary. If it comes back up and finds that another node holds the leader lock, it will not attempt to serve writes; it will demote itself and start replicating from the new primary. The DCS is the single source of truth about who the leader is, and Patroni trusts it unconditionally.""",
 """In WSFC, the fencing guarantee comes from quorum plus resource ownership. When a node stops heartbeating, the surviving nodes arbitrate: if they hold quorum, they take ownership of the AG resources and bring a secondary online as primary. The old primary — if it's actually alive but partitioned away — is fenced by losing cluster membership: without quorum it cannot bring resources online, so it cannot serve writes. The cluster is the single source of truth about who the primary is, and every replica trusts it unconditionally."""),

# 21 PG promotion sequence -> AG sequence
("""The promotion sequence in PostgreSQL streaming replication with Patroni looks like this in practice: the primary's health check fails, Patroni on all standby nodes detects the leader lock has expired (or is about to), each standby races to acquire the lock in the DCS, one wins, that node calls %s, PostgreSQL exits recovery mode on that node, Patroni updates the DCS with the new leader's connection information, and HAProxy or whatever proxy is in front routes new connections to the new primary. Applications using persistent connections will experience an interruption — their existing connections to the old primary are dead. Applications using connection pooling with retry logic will reconnect quickly. Applications without retry logic will fail until they are restarted.""" % code('pg_promote()'),
 """The promotion sequence in an AG looks like this in practice: WSFC detects the primary node's failure through missed heartbeats, the remaining nodes confirm they hold quorum, the cluster promotes a secondary to primary (rolling its databases forward or back as needed based on synchronization state), and the listener DNS/IP moves to the new primary. Applications using persistent connections will experience an interruption — their existing connections to the old primary are dead. Applications using connection pooling with retry logic reconnect to the listener name quickly. Applications without retry logic fail until they are restarted."""),

# 22 read replicas
("""Read replicas — standbys configured for read-only access — are one of the most effective ways to scale read-heavy workloads. In PostgreSQL, any standby with %s can accept SELECT queries. In SQL Server, readable secondaries in an AG serve the same purpose. The architectural win is that read replicas are essentially free from a data perspective — the replication cost exists anyway for HA, and allowing reads on the standby costs you only the compute and I/O on the standby node.""" % code('hot_standby = on'),
 """Read replicas — secondaries configured for read-only access — are one of the most effective ways to scale read-heavy workloads. In SQL Server, readable secondaries in an AG serve this purpose. The architectural win is that read replicas are essentially free from a data perspective — the replication cost exists anyway for HA, and allowing reads on the secondary costs you only the compute and I/O on the secondary node."""),

# 23 PG replica check -> DMV
("""In PostgreSQL, you can check whether a session is running on a replica and what the current replication lag is from inside application queries.""",
 """In SQL Server, %s exposes synchronization state and queue sizes per database, and %s with %s tells an application whether it's talking to the primary — useful for routing logic and failover smoke tests.""" % (code('sys.dm_hadr_database_replica_states'), code('DATABASEPROPERTYEX'), code("'Updateability'"))),

# 24 cascading -> distributed AGs
("""In PostgreSQL, cascading replication is configured by having one standby connect as a replication source for another standby. The intermediate standby generates no primary WAL — it passes through the WAL stream from the primary — so it works transparently.""",
 """For geographic distribution, <strong class="text-white">distributed Availability Groups</strong> link two independent AGs — each with its own WSFC cluster — across sites. The primary AG forwards log records to the secondary AG, which replays them locally. Unlike a single stretched cluster, a network partition between sites doesn't threaten quorum on either side; each site keeps its own witness and its own failure domain."""),

# 25 PgBouncer -> ADO.NET pooling
("""PgBouncer for PostgreSQL and connection pooling on the application side for SQL Server help absorb this shock by queuing and staggering reconnection attempts rather than letting every client hammer the new primary at once.""",
 """Connection pooling on the application side (ADO.NET pooling) helps absorb this shock by queuing and staggering reconnection attempts rather than letting every client hammer the new primary at once."""),

# 26 takeaway log foundation
("""**Both platforms build HA on top of their transaction log.** PostgreSQL streams WAL to standbys; SQL Server ships transaction log records to Availability Group replicas. Synchronous replication guarantees zero data loss at the cost of write latency; asynchronous replication avoids that latency at the cost of some data loss risk on failover.""",
 """**SQL Server builds HA on top of its transaction log.** Log records stream to Availability Group replicas (or shared storage backs a Failover Cluster Instance). Synchronous replication guarantees zero data loss at the cost of write latency; asynchronous replication avoids that latency at the cost of some data loss risk on failover."""),

# 27 takeaway split-brain
("""**Automated failover requires a mechanism to prevent split-brain.** Patroni relies on a distributed configuration store (etcd, Consul, ZooKeeper) and a leader lock; SQL Server's Always On relies on Windows Server Failover Clustering and quorum. Both exist to answer the same dangerous question correctly: is the primary really dead, or just unreachable?""",
 """**Automated failover requires a mechanism to prevent split-brain.** SQL Server's Always On relies on Windows Server Failover Clustering and quorum voting to answer the dangerous question correctly: is the primary really dead, or just unreachable? A two-node cluster with no witness can't answer it — configure the witness before you need it."""),
]

def main():
    lines = open(PATH).read().split('\n')
    # Replace the Patroni section (lines 105-136, 1-indexed) with the FCI section.
    # Verify boundaries first.
    assert 'PostgreSQL Streaming Replication and Patroni' in lines[104], lines[104][:80]
    assert lines[136].strip() == '<p class="text-gray-300 leading-relaxed">---</p>', repr(lines[136][:80])
    new_lines = lines[:104] + [FCI_SECTION] + lines[136:]
    text = '\n'.join(new_lines)
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch11: section replaced + all {len(REPLACEMENTS)} replacements applied')

main()
