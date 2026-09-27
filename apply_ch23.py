#!/usr/bin/env python3
"""Apply ch23 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch23-load-balancing.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
H3 = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">%s</h3>'

TOOLS_SECTION = (
H3 % "Where an External Load Balancer Still Fits" + "\n\n" +
P + "The AG listener covers SQL-aware routing, but it doesn't cover everything. Cross-datacenter traffic shaping, TLS termination, non-SQL-aware health checks, and blue/green listener cutovers are jobs for a TCP load balancer (HAProxy, Azure Load Balancer, F5) sitting <em>in front of</em> the listener VIP — not in place of it. The balancer health-checks each SQL Server node with a lightweight T-SQL probe; only the primary's listener accepts connections, so routing stays correct through failovers.</p>\n\n" +
P + "What you don't need is a query-parsing proxy. Read/write splitting in SQL Server is a connection-string property (" + code('ApplicationIntent') + "), not something a middlebox infers by parsing SQL — which removes an entire category of parsing bugs and latency. And connection pooling stays in the driver (SqlClient), so the proxy tier never has to multiplex sessions.</p>\n\n" +
P + "The production pattern, end to end: application → SqlClient pooling → TCP load balancer (optional, for cross-site or traffic policy) → AG listener → primary or readable secondary by ApplicationIntent, with retry logic for failover drain. Every layer has exactly one job.</p>\n\n" +
'<div class="my-6 bg-gray-900 border border-gray-800 rounded-xl p-5 overflow-x-auto"><pre class="mermaid">graph LR\\n    App["Application"] --> Pool["SqlClient pooling\\\\n(per app process)"]\\n    Pool --> LB["TCP load balancer\\\\n(optional, cross-site)"]\\n    LB --> Listener["AG Listener VIP\\\\n(ApplicationIntent routing)"]\\n    Listener -->|ReadWrite| Primary[("Primary")]\\n    Listener -->|ReadOnly| Sec1[("Readable secondary")]\\n    Listener -->|ReadOnly| Sec2[("Readable secondary")]</pre></div>\n\n' +
P + "*Figure: Integrated SQL Server load balancing — SqlClient pools at the application tier, an optional TCP balancer handles traffic policy, and the AG listener routes by ApplicationIntent to the primary or readable secondaries.*</p>\n\n" +
P + "---</p>"
)

REPLACEMENTS = [
# 1 intro
("""This chapter walks through the mechanics of load balancing for both PostgreSQL and SQL Server — from the foundational concepts that justify why you need it, through the tools and configurations that implement it, to the production edge cases that will make or break your setup under real traffic.""",
 """This chapter walks through the mechanics of load balancing for SQL Server — from the foundational concepts that justify why you need it, through the tools and configurations that implement it, to the production edge cases that will make or break your setup under real traffic."""),

# 2 replication foundations
("""PostgreSQL and SQL Server approach the replication layer that underlies load balancing quite differently. PostgreSQL uses streaming replication with standby servers that can serve read queries, and a rich ecosystem of third-party tools handles the routing layer above it. SQL Server has Always On Availability Groups, which include readable secondary replicas and a listener endpoint that abstracts the current primary from the application. Understanding these foundations sets the stage for everything that follows.""",
 """SQL Server's load balancing foundation is Always On Availability Groups: readable secondary replicas plus the AG listener endpoint, which abstracts the current primary from the application and routes read-intent connections to secondaries automatically. Understanding this foundation sets the stage for everything that follows."""),

# 3 replication lag
("""The challenge is replication lag. Replicas in PostgreSQL streaming replication and SQL Server Always On both apply changes asynchronously by default (synchronous replication is available but carries a write latency penalty).""",
 """The challenge is replication lag. AG secondaries apply changes asynchronously by default (synchronous commit is available but carries a write latency penalty)."""),

# 4 connection resources
("""Before discussing dedicated load balancer tools, it is worth recognizing that connection pooling and load balancing are deeply intertwined. Each database connection consumes memory and a process (in PostgreSQL) or a thread (in SQL Server). PostgreSQL's process-per-connection model means that 1,000 concurrent connections consume significant memory and create scheduler contention long before the CPU is saturated with actual query work. SQL Server handles connections more efficiently with a thread pool, but unconstrained connection counts still hurt.""",
 """Before discussing dedicated load balancer tools, it is worth recognizing that connection pooling and load balancing are deeply intertwined. Each database connection consumes memory and a worker thread: a thousand concurrent connections create scheduler contention long before the CPU is saturated with actual query work. SQL Server's thread pool handles concurrency better than process-per-connection designs, but unconstrained connection counts still hurt — which is why pooling is the foundation load balancing stands on."""),

# 5 PgBouncer -> SqlClient pooling
("""<strong class="text-white">PgBouncer</strong> is the standard connection pooler for PostgreSQL. It operates in three modes: session pooling (one backend connection per client session, released when the client disconnects), transaction pooling (the backend connection is returned to the pool after each transaction), and statement pooling (the connection is released after each statement, which is incompatible with most applications). Transaction pooling is the production standard — it provides the best connection compression while remaining compatible with the vast majority of application patterns.""",
 """<strong class="text-white">SqlClient connection pooling</strong> is the standard pooler for SQL Server, built into the driver rather than deployed as a tier. The pool is keyed by the exact connection string: %s checks out a pooled connection, %s / %s returns it, and %s cleans session state between checkouts. %s and %s bound the pool per application process — and because pooling is per process, the database sees the sum across your whole app fleet, so size the ceiling against the fleet.""" % (code('Open()'), code('Close()'), code('Dispose'), code('sp_reset_connection'), code('Min Pool Size'), code('Max Pool Size'))),

# 6 pgbouncer.ini -> two connection strings
("""Configuring PgBouncer for a two-node setup (one primary, one replica) with read/write splitting typically means running two PgBouncer instances or configuring two separate database sections in %s, one pointing at the primary and one at the replica, and having the application or a higher-level proxy route to the appropriate PgBouncer endpoint.""" % code('pgbouncer.ini'),
 """Configuring read/write splitting with SqlClient typically means two connection strings in the application: one with %s pointing at the AG listener (writes and read-after-write), one with %s (reporting and analytics, routed to readable secondaries). The application or ORM picks the string per operation — no proxy tier required.""" % (code('ApplicationIntent=ReadWrite'), code('ApplicationIntent=ReadOnly'))),

# 8 idle-in-transaction
("""High numbers of idle-in-transaction connections in PostgreSQL are a common sign that the application is holding transactions open longer than necessary — perhaps because the connection pooler is not configured correctly or because the application code has slow processing between SQL statements within a transaction. These connections hold locks and prevent autovacuum from cleaning dead tuples. A well-tuned connection pool with reasonable idle-in-transaction timeouts prevents this from accumulating.""",
 """High numbers of sessions with open transactions and no active request are a common sign that the application is holding transactions open longer than necessary — perhaps slow processing between SQL statements within a transaction. These sessions hold locks and, under RCSI, block version-store cleanup. Find them by joining %s to %s for %s with no matching row in %s, and set command timeouts so leaked transactions can't accumulate silently.""" % (code('sys.dm_exec_sessions'), code('sys.dm_tran_session_transactions'), code('open_transaction_count > 0'), code('sys.dm_exec_requests'))),

# 15 mermaid handled via surgery in main() (see below)

# 17 PG config block para
("""For PostgreSQL, there is no single equivalent configuration block, but the same routing intent can be expressed through PgBouncer or pgPool-II configuration:""",
 """One operational gotcha: the routing list above is per-primary — repeat the PRIMARY_ROLE routing list on every replica that can become primary, or a failover will silently drop read-only routing until someone reconfigures it."""),

# 18 HAProxy/Patroni health check
("""For PostgreSQL with HAProxy, the health check is typically a TCP connect check combined with a custom HTTP check against Patroni's REST API. Patroni returns HTTP 200 for the primary and HTTP 503 for replicas (or a customizable response). HAProxy checks this endpoint every two seconds by default. The %s and %s parameters control how many consecutive successes are required to mark a backend healthy and how many consecutive failures are required to mark it down. A typical production configuration uses %s — two consecutive failures to take a node out of rotation, two consecutive successes to add it back. This prevents flapping from transient network hiccups.""" % (code('rise'), code('fall'), code('rise 2 fall 2')),
 """For the AG listener, health checking is built in: the listener only accepts connections on the primary, so a failed primary naturally stops receiving traffic. When a TCP load balancer sits in front of the listener, its health check is a lightweight T-SQL probe — %s, or %s when you need role awareness — every couple of seconds. Use rise/fall thresholds (two consecutive failures to take a node out of rotation, two successes to add it back) to prevent flapping from transient network hiccups.""" % (code('SELECT 1'), code('sys.fn_hadr_is_primary_replica(NULL)'))),

# 19 takeaway
("""PostgreSQL load balancing is assembled from composable tools: Patroni manages failover and primary election, HAProxy routes traffic based on health-check results, and PgBouncer pools connections at each node. SQL Server's Always On Availability Groups provide an integrated solution through the AG listener and native read-only routing, but they still benefit from external connection pooling at the application tier.""",
 """SQL Server load balancing is integrated: the AG listener routes by ApplicationIntent, readable secondaries absorb the read load, and SqlClient pooling at the application tier keeps connection counts sane. External TCP load balancers still have a role for cross-datacenter or non-SQL-aware routing — but they sit in front of the listener, not in place of it."""),
]

def main():
    text = open(PATH).read()
    # Replace PG tools section (h3 at 123 through the --- before the AG listener h3).
    idx_a = text.index('Tools for PostgreSQL Load Balancing: pgPool-II, HAProxy, and Patroni')
    start = text.rindex('<h3', 0, idx_a)
    idx_b = text.index('SQL Server Always On and the Availability Group Listener')
    end = text.rindex('<h3', 0, idx_b)
    text = text[:start] + TOOLS_SECTION + '\n\n' + text[end:]
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch23: section replaced + all {len(REPLACEMENTS)} replacements applied')

main()
