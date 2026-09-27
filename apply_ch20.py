#!/usr/bin/env python3
"""Apply ch20 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch20-deployment.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""A brilliantly tuned PostgreSQL instance on undersized hardware, or a SQL Server deployment without proper high availability, will still fail the business.""",
 """A brilliantly tuned SQL Server instance on undersized hardware, or a deployment without proper high availability, will still fail the business."""),
("""This chapter walks through each model, explains how PostgreSQL and SQL Server behave within it, and helps you make informed decisions about where and how to deploy databases for production workloads.""",
 """This chapter walks through each model, explains how SQL Server behaves within it, and helps you make informed decisions about where and how to deploy databases for production workloads."""),

# 2 on-prem control
("""For both PostgreSQL and SQL Server, on-premises deployment gives you the highest degree of control.""",
 """For SQL Server, on-premises deployment gives you the highest degree of control."""),

# 3 PG sizing -> SQL Server sizing
("""When sizing on-premises hardware for PostgreSQL, memory is typically the most important resource. PostgreSQL relies heavily on shared buffers and OS page cache to keep hot data in memory. The general recommendation is to set %s to about 25%% of total RAM, and ensure total RAM is large enough to hold your working set plus the OS overhead. Storage matters enormously — local NVMe SSDs dramatically outperform SAN-attached spinning disks for OLTP workloads, while SAN or NAS may still be appropriate for large data warehouses where sequential scan performance is acceptable.""" % code('shared_buffers'),
 """When sizing on-premises hardware for SQL Server, memory is typically the most important resource: set %s to total RAM minus the OS reserve, and ensure total RAM is large enough to hold your working set plus that overhead. Storage matters enormously — local NVMe SSDs dramatically outperform SAN-attached spinning disks for OLTP workloads, while SAN may still suit large data warehouses where sequential throughput dominates.""" % code('max server memory')),

# 4 SQL Server sizing para
("""SQL Server on-premises has its own sizing considerations. Unlike PostgreSQL, which relies on the OS page cache as a second layer, SQL Server manages its own buffer pool directly and will aggressively claim available RAM up to the %s limit. Forgetting to set this limit is a classic mistake that starves the OS of memory on a shared machine.""" % code('max server memory'),
 """SQL Server manages its own buffer pool directly and will aggressively claim available RAM up to the %s limit. Forgetting to set this limit is a classic mistake that starves the OS of memory on a shared machine — set it on every instance, including dev.""" % code('max server memory')),

# 5 storage layout
("""One often-overlooked aspect of on-premises deployment is the storage layout. Both PostgreSQL and SQL Server benefit from separating data, transaction logs, and temporary workspace onto different physical devices. This isn't just about throughput — it's about I/O isolation. A long-running sort operation that hammers temporary storage shouldn't affect WAL write latency, which directly impacts transaction commit performance.""",
 """One often-overlooked aspect of on-premises deployment is the storage layout. SQL Server benefits from separating data, transaction log, and tempdb onto different physical devices. This isn't just about throughput — it's about I/O isolation. A long-running sort operation that hammers tempdb shouldn't affect transaction-log write latency, which directly impacts transaction commit performance."""),

# 6 WAL dir
("""For PostgreSQL, the WAL directory (%s) should reside on its own fast volume, especially on high-write workloads. For SQL Server, transaction log files (%s) should be on dedicated storage, and %s files should sit on the fastest available storage, ideally local SSDs even in a SAN environment, because %s contention is one of the most common SQL Server performance problems in production.""" % (code('pg_wal'), code('.ldf'), code('tempdb'), code('tempdb')),
 """Transaction log files (%s) should be on dedicated storage, and %s files should sit on the fastest available storage, ideally local SSDs even in a SAN environment, because %s contention is one of the most common SQL Server performance problems in production.""" % (code('.ldf'), code('tempdb'), code('tempdb'))),

# 7 ballooning
("""Memory ballooning and transparent page sharing are similar hazards. Hypervisors may reclaim memory from your database VM under pressure, forcing the database to evict buffer pool pages. For PostgreSQL this means more disk reads. For SQL Server this triggers a warning in the error log and degrades buffer pool hit ratios.""",
 """Memory ballooning and transparent page sharing are real hazards. Hypervisors may reclaim memory from your database VM under pressure, forcing buffer pool evictions — SQL Server logs a warning in the Error Log and buffer pool hit ratios degrade. Lock the VM's memory reservation so the hypervisor can't reclaim buffer pool pages under pressure."""),

# 8 managed PG
("""Amazon RDS for PostgreSQL and Azure Database for PostgreSQL are not vanilla PostgreSQL — they're PostgreSQL running inside a managed abstraction. You cannot access the underlying OS. You cannot modify %s directly. You cannot use %s with local filesystem paths. You cannot install arbitrary extensions. The managed environment constrains what you can do, and understanding those constraints before committing to a managed service is essential.""" % (code('pg_hba.conf'), code('COPY')),
 """Managed SQL Server offerings — Amazon RDS for SQL Server, Azure SQL Database, SQL Server on Azure VMs — run inside a managed abstraction. You cannot access the underlying OS. You cannot use %s with local filesystem paths on Azure SQL Database. You cannot install arbitrary components. The managed environment constrains what you can do, and understanding those constraints before committing to a managed service is essential.""" % code('BULK INSERT')),

# 9 instance sizing
("""Performance in managed services is tied to the instance class or service tier you select. RDS PostgreSQL and RDS SQL Server are sized by instance type (db.t3.medium, db.r6g.4xlarge, etc.), and storage IOPS are either included or purchasable separately depending on the storage type. Azure SQL Database uses DTUs or vCores, with corresponding IOPS limits tied to the tier.""",
 """Performance in managed services is tied to the instance class or service tier you select. RDS for SQL Server is sized by instance type (db.t3.medium, db.r6g.4xlarge, etc.), with storage IOPS included or purchasable separately depending on the storage type. Azure SQL Database uses DTUs or vCores, with corresponding IOPS limits tied to the tier."""),

# 10 Aurora -> Hyperscale
("""Aurora PostgreSQL and Aurora SQL Server (via RDS compatibility) deserve mention as hybrid managed offerings. Aurora disaggregates storage from compute, using a distributed storage engine with six-way replication across availability zones. This fundamentally changes the HA model — a primary failure results in near-instantaneous failover because the new primary immediately attaches to the same shared storage volume. For PostgreSQL workloads that need strong availability SLAs without managing replication manually, Aurora PostgreSQL is a compelling option. The tradeoff is that Aurora's storage engine, while PostgreSQL-compatible, has its own performance characteristics and some behavioral differences from community PostgreSQL.""",
 """Azure SQL Database's <strong class="text-white">Hyperscale</strong> tier deserves mention as a disaggregated-storage offering: compute and storage scale independently, with page servers replicating data across availability zones. This changes the HA model — a primary failure results in fast failover because the new primary attaches to the same shared storage. For workloads that need strong availability SLAs without managing AGs manually, Hyperscale (or Azure SQL Managed Instance for near-on-premises parity) is compelling. The tradeoff is the managed abstraction: some on-premises features and knobs aren't available, and performance characteristics differ from a tuned bare-metal instance."""),

# 11 h3 containers
("""Containerized Deployments: PostgreSQL and SQL Server in Docker and Kubernetes""",
 """Containerized Deployments: SQL Server in Docker and Kubernetes"""),

# 12 containers intro
("""Running databases in containers is no longer experimental — it's a production deployment pattern, particularly for PostgreSQL. Containers provide environment consistency, fast startup, easy version upgrades, and alignment with modern application deployment tooling.""",
 """Running databases in containers is no longer experimental — it's a production deployment pattern. Containers provide environment consistency, fast startup, easy version upgrades, and alignment with modern application deployment tooling."""),

# 13 PG containers -> SQL Server containers
("""PostgreSQL in containers is straightforward because it's a single-process server that reads its data directory from a configurable path. The official %s Docker image is well-maintained, environment variables configure initialization, and the data directory maps cleanly to a persistent volume. For development, local testing, and CI/CD pipeline databases, containerized PostgreSQL is excellent. For production, the question is whether Kubernetes storage performance matches what you need.""" % code('postgres'),
 """SQL Server in containers is well-trodden ground: Microsoft maintains official Linux-based images, environment variables (%s, %s, %s) configure initialization, and the data directory maps cleanly to a persistent volume. For development, local testing, and CI/CD pipeline databases, containerized SQL Server is excellent. For production, the question is whether Kubernetes storage performance matches what you need.""" % (code('ACCEPT_EULA'), code('MSSQL_SA_PASSWORD'), code('MSSQL_PID'))),

# 14 container ops
("""SQL Server has supported Docker containers since SQL Server 2017, and Microsoft maintains official Linux-based container images for SQL Server. Running SQL Server in a container is operationally similar to PostgreSQL — mount a persistent volume to the data directory, configure via environment variables or startup scripts, and manage the lifecycle through container orchestration. SQL Server containers on Kubernetes are used in production, particularly in development/test environments and for SQL Server instances that need fast provisioning and deprovisioning.""",
 """Running SQL Server in a container is operationally straightforward — mount a persistent volume to the data directory, configure via environment variables or startup scripts, and manage the lifecycle through container orchestration. SQL Server containers on Kubernetes run in production, particularly in development/test environments and for instances that need fast provisioning and deprovisioning."""),

# 15 operators
("""Kubernetes operators for databases add a higher-level abstraction over raw container deployment. The Crunchy Data PGO (PostgreSQL Operator) and Zalando's postgres-operator for PostgreSQL, and the SQL Server Operator for Kubernetes (from Microsoft), all provide CRD-based (Custom Resource Definition) declarations for PostgreSQL and SQL Server clusters. You define the desired state — primary + replicas, backup schedules, resource limits, connection pooling — and the operator reconciles the running environment to match that state. This brings the Kubernetes model of declarative infrastructure to database management.""",
 """Kubernetes operators for databases add a higher-level abstraction over raw container deployment. Operators such as DH2i's DxOperator provide CRD-based (Custom Resource Definition) declarations for SQL Server clusters with Availability Group semantics. You define the desired state — primary + replicas, backup schedules, resource limits — and the operator reconciles the running environment to match that state. This brings the Kubernetes model of declarative infrastructure to database management."""),

# 16 OOM
("""Setting CPU and memory limits on a database container seems like good Kubernetes hygiene, but if the memory limit is too low, PostgreSQL's shared buffers plus per-connection work_mem allocations can push the container over its limit, triggering an OOM kill. PostgreSQL doesn't handle OOM kills gracefully — the instance disappears and must restart, replaying WAL from the last checkpoint. Set memory requests and limits with the full knowledge of how PostgreSQL allocates memory, and consider setting a memory limit somewhat higher than the expected working set to provide headroom.""",
 """Setting CPU and memory limits on a database container seems like good Kubernetes hygiene, but if the memory limit is too low, the buffer pool plus per-query memory grants can push the container over its limit, triggering an OOM kill. SQL Server doesn't handle OOM kills gracefully — the instance disappears and must restart, replaying the transaction log from the last checkpoint. Set memory requests and limits with full knowledge of %s plus grant headroom, and keep the limit somewhat above the expected working set.""" % code('max server memory')),

# 17 hybrid PG -> hybrid AG
("""The fundamental challenge in hybrid architectures is data movement and consistency. If your primary PostgreSQL cluster runs on-premises and your disaster recovery replica runs on AWS RDS, you need logical replication between them, because physical replication (streaming replication) doesn't work across different storage architectures. Logical replication in PostgreSQL replicates data at the row level, crossing version and environment boundaries, but it has limitations — DDL changes are not replicated, sequences don't replicate their current values, and large object operations don't replicate. These gaps require operational procedures to compensate.""",
 """The fundamental challenge in hybrid architectures is data movement and consistency. If your primary SQL Server cluster runs on-premises and your disaster recovery replica runs in Azure, Availability Groups — including distributed AGs — span the boundary cleanly, and log shipping crosses environment boundaries well too. The gaps are operational rather than semantic: latency, bandwidth, and the fact that failover across a WAN needs careful quorum design so a network partition doesn't take down both sides."""),

# 18 replication latency
("""Network latency between on-premises and cloud is the most persistent challenge in hybrid deployments. WAL shipping and logical replication both tolerate latency better than synchronous streaming replication, but any replication-based architecture needs reliable, low-jitter connectivity between environments.""",
 """Network latency between on-premises and cloud is the most persistent challenge in hybrid deployments. Log shipping and asynchronous AG replicas tolerate latency better than synchronous commit, but any replication-based architecture needs reliable, low-jitter connectivity between environments."""),

# 19 99.99
("""If your application requires 99.99% uptime (about 52 minutes of downtime per year), you need an architecture with automatic failover, whether that's on-premises PostgreSQL streaming replication with a tool like Patroni managing failover, SQL Server Always On Availability Groups, Aurora PostgreSQL, or Azure SQL Database's built-in HA.""",
 """If your application requires 99.99% uptime (about 52 minutes of downtime per year), you need an architecture with automatic failover — on-premises Always On Availability Groups with automatic failover, or Azure SQL Database's built-in HA. A standalone instance with manual failover procedures cannot reliably hit 99.99% without extraordinarily disciplined operations."""),

# 20 team capability
("""A small engineering team that has been running VMware for years with a well-documented runbook for PostgreSQL virtual machines will operate that environment more reliably than a Kubernetes-based deployment they're learning as they go.""",
 """A small engineering team that has been running VMware for years with a well-documented runbook for SQL Server virtual machines will operate that environment more reliably than a Kubernetes-based deployment they're learning as they go."""),

# 21 takeaway hybrid
("""consistent governance across environments, and a clearunderstanding of replication mechanisms — logical replication for PostgreSQL and Availability Groups or log shipping for SQL Server — because data movement""",
 """consistent governance across environments, and a clear understanding of replication mechanisms — Availability Groups or log shipping — because data movement"""),
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
    print(f'ch20: all {len(REPLACEMENTS)} replacements applied')

main()
