#!/usr/bin/env python3
"""Rewrite ch05 sections 5.1-5.2 (part A)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch05-architecture-patterns.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

reps.append((
"or PostgreSQL streaming replication with Patroni. You managed VIPs, fencing, and split-brain scenarios yourself.",
"or SQL Server transactional replication with a distributor. You managed VIPs, fencing, and split-brain scenarios yourself."
))
reps.append((
"<strong class=\"text-white\">Cloud SQL</strong> (GCP) uses regional instances with a standby in a second zone within the same region. Failover is automatic and typically completes in 60–120 seconds — meaningfully slower than Aurora or Azure Business Critical. AlloyDB for PostgreSQL, Google's premium offering, uses a Paxos-based distributed storage layer similar to Aurora, with failover under 60 seconds and readable replicas that share the underlying storage.",
"<strong class=\"text-white\">Cloud SQL</strong> (GCP) uses regional instances with a standby in a second zone within the same region. Failover is automatic and typically completes in 60–120 seconds — meaningfully slower than Aurora or Azure Business Critical. For SQL Server workloads on GCP, Cloud SQL for SQL Server is the managed option; AlloyDB is PostgreSQL-only with no SQL Server equivalent, so SQL Server architectures on GCP pair Cloud SQL for SQL Server with Compute Engine self-managed instances when custom HA is required."
))
# Multi-AZ CLI -> RDS for SQL Server
reps.append((
"# Create a Multi-AZ RDS PostgreSQL instance" + NL +
"aws rds create-db-instance " + BS + NL +
"  --db-instance-identifier prod-postgres-primary " + BS + NL +
"  --db-instance-class db.r6g.4xlarge " + BS + NL +
"  --engine postgres " + BS + NL +
"  --engine-version 15.4 " + BS + NL,
"# Create a Multi-AZ RDS for SQL Server instance" + NL +
"aws rds create-db-instance " + BS + NL +
"  --db-instance-identifier prod-sql-primary " + BS + NL +
"  --db-instance-class db.r6i.4xlarge " + BS + NL +
"  --engine sqlserver-se " + BS + NL +
"  --engine-version 16.00 " + BS + NL
))
reps.append((
"aws rds describe-db-instances " + BS + NL +
"  --db-instance-identifier prod-postgres-primary " + BS,
"aws rds describe-db-instances " + BS + NL +
"  --db-instance-identifier prod-sql-primary " + BS
))
# Aurora TF -> Aurora MySQL
reps.append((
"# Aurora PostgreSQL cluster with Multi-AZ writer and readers" + NL +
'resource "aws_rds_cluster" "prod_aurora" {' + NL +
'  cluster_identifier     = "prod-aurora-postgres"' + NL +
'  engine                 = "aurora-postgresql"' + NL +
'  engine_version         = "15.4"',
"# Aurora MySQL cluster with Multi-AZ writer and readers" + NL +
'resource "aws_rds_cluster" "prod_aurora" {' + NL +
'  cluster_identifier     = "prod-aurora-mysql"' + NL +
'  engine                 = "aurora-mysql"' + NL +
'  engine_version         = "8.0.mysql_aurora.3.08.0"'
))
reps.append((
'enabled_cloudwatch_logs_exports = ["postgresql"]',
'enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]'
))
# What You Can't Control paragraph
reps.append((
"On a self-managed PostgreSQL cluster, you control the exact failover timing: <code " + CODE + ">synchronous_commit</code>, <code " + CODE + ">synchronous_standby_names</code>, and the Patroni TTL settings. In RDS Multi-AZ, you don't choose the replication protocol — it's block-level synchronous replication of EBS volumes managed by AWS. You can't query the replication lag on the standby because it isn't a readable PostgreSQL replica; it's a shadow volume.",
"On a self-managed SQL Server cluster, you control the exact failover timing: availability group synchronous-commit mode, <code " + CODE + ">REQUIRED_SYNCHRONIZED_SECONDARIES_TO_COMMIT</code>, and WSFC quorum votes. In RDS Multi-AZ for SQL Server, you don't choose the replication protocol — AWS manages the mirroring/AG layer underneath. You can't query replication lag on the standby because it isn't a readable SQL Server replica; it's a shadow volume."
))
reps.append((
"Always configure your JDBC, psycopg2, or .NET connection strings to use the RDS DNS endpoint",
"Always configure your JDBC, pyodbc, or .NET SqlClient connection strings to use the RDS DNS endpoint"
))
# 5.2 mental model
reps.append((
"configuring streaming replication, managing replication slots, and worrying about <code " + CODE + ">max_replication_slots</code> and <code " + CODE + ">max_wal_senders</code>.",
"configuring Always On availability groups, managing cluster quorum, and worrying about WSFC votes and listener DNS records."
))
reps.append((
"<strong class=\"text-white\">RDS Read Replicas</strong> are asynchronous replicas using native PostgreSQL streaming replication or SQL Server log shipping. They're readable, each with their own endpoint, and can be promoted to standalone instances. You can have up to five read replicas per RDS instance. Replication lag is the same concern you had on-premises: under normal conditions you'll see sub-second lag, but long-running transactions on the primary that generate heavy WAL, or large bulk operations, can push lag to minutes.",
"<strong class=\"text-white\">RDS Read Replicas</strong> are asynchronous replicas using SQL Server log shipping. They're readable, each with their own endpoint, and can be promoted to standalone instances. You can have up to five read replicas per RDS instance. Replication lag is the same concern you had on-premises: under normal conditions you'll see sub-second lag, but long-running transactions on the primary that generate heavy transaction log volume, or large bulk operations, can push lag to minutes."
))
reps.append((
"a reader instance doesn't need to ship or apply WAL — it reads the same storage pages the writer uses",
"a reader instance doesn't need to ship or apply redo logs — it reads the same storage pages the writer uses"
))
reps.append((
"This is a genuinely different operational experience from PostgreSQL streaming replication, and it means Aurora replicas are appropriate for latency-sensitive reporting workloads that RDS read replicas are not.",
"This is a genuinely different operational experience from SQL Server log shipping, and it means Aurora replicas are appropriate for latency-sensitive reporting workloads that RDS read replicas are not."
))
# RDS Proxy
reps.append((
"One on-premises pattern that doesn't translate cleanly to RDS is PgBouncer or pgpool-II sitting in front of your replica pool. RDS Proxy is the managed alternative. It maintains a connection pool to your RDS or Aurora instances and exposes a single endpoint to applications. When you have Lambda functions or containerized microservices opening thousands of short-lived connections — a workload that would exhaust <code " + CODE + ">max_connections</code> on PostgreSQL — RDS Proxy pins connections to backend instances and handles multiplexing.",
"One on-premises pattern that doesn't translate cleanly to RDS is a standalone connection pooler sitting in front of your replica pool. RDS Proxy is the managed alternative. It maintains a connection pool to your RDS or Aurora instances and exposes a single endpoint to applications. When you have Lambda functions or containerized microservices opening thousands of short-lived connections — a workload that would exhaust worker threads and connection capacity on SQL Server — RDS Proxy pins connections to backend instances and handles multiplexing."
))
reps.append((
"  --engine-family POSTGRESQL " + BS,
"  --engine-family SQLSERVER " + BS
))
reps.append((
"  --db-cluster-identifiers prod-aurora-postgres",
"  --db-cluster-identifiers prod-aurora-mysql"
))
reps.append((
"RDS Proxy has a real limitation that catches DBAs by surprise: it doesn't support all PostgreSQL client features. <code " + CODE + ">COPY</code> commands, <code " + CODE + ">LISTEN/NOTIFY</code>, <code " + CODE + ">pg_terminate_backend()</code>, and <code " + CODE + ">SET LOCAL</code> within certain transaction modes behave unexpectedly through the proxy. If your application relies on advisory locks or NOTIFY-based event queuing, test against the proxy endpoint explicitly before deploying to production.",
"RDS Proxy has real limitations that catch DBAs by surprise: certain session-state changes force connection pinning (the proxy holds a dedicated backend connection for the client), which reduces the multiplexing benefit. Session-level <code " + CODE + ">SET</code> options, temporary tables, and application locks via <code " + CODE + ">sp_getapplock</code> can all trigger pinning or behave unexpectedly through the proxy. If your application relies on temporary tables or session state, test against the proxy endpoint explicitly before deploying to production."
))
reps.append((
"which use the native PostgreSQL replication stream and typically show 2–10 seconds of lag depending on bandwidth.",
"which use native log shipping and typically show 2–10 seconds of lag depending on bandwidth."
))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

if failed:
    print("FAILED:")
    for n, s in failed:
        print("  count=" + str(n) + ": " + s)
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch05-A OK:", len(reps), "replacements")
