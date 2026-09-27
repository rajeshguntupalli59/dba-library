#!/usr/bin/env python3
"""Rewrite ch05 section 5.10 as SQL Server feature constraints (part D)."""
import sys, re

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch05-architecture-patterns.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'

START = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">5.10 Extension and Feature Constraints by Cloud Provider</h3>'
END = '<p class="text-gray-300 leading-relaxed">---</p>' + NL + NL + '<h3 class="text-lg font-semibold text-white mt-8 mb-3">Key Takeaways</h3>'

si = t.find(START)
ei = t.find(END)
if si == -1 or ei == -1 or ei <= si:
    print("markers not found", si, ei)
    sys.exit(1)

new_section = '''<h3 class="text-lg font-semibold text-white mt-8 mb-3">5.10 Feature and Component Constraints by Cloud Provider</h3>

<p class="text-gray-300 leading-relaxed">#### Not All SQL Server Is the Same SQL Server</p>

<p class="text-gray-300 leading-relaxed">A common misconception when migrating from self-managed SQL Server is that every component that ships in the box — Agent, SSIS, SSAS, SSRS, CLR, replication — will work on RDS, Cloud SQL, or Azure SQL. The managed service controls which components are available, and the list differs meaningfully across providers. This affects job scheduling, ETL architecture, and monitoring design.</p>

<p class="text-gray-300 leading-relaxed"><strong class="text-white">RDS for SQL Server</strong> has the most visible constraint list because it runs the full SQL Server engine on EC2 under the hood but walls off the surrounding components. SQL Server Agent is <strong class="text-white">not available</strong> — scheduled jobs must move to Lambda/EventBridge, Systems Manager, or an external scheduler that connects over TDS. SSIS, SSAS, and SSRS are unavailable. <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">xp_cmdshell</code> is disabled. CLR is restricted to the approved assembly set. Linked servers are supported to a limited set of providers. The master user is not <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sysadmin</code>, so server-level operations like adding trace flags or configuring the dedicated admin connection are unavailable.</p>

<p class="text-gray-300 leading-relaxed"><strong class="text-white">Cloud SQL for SQL Server</strong> has a similar profile with GCP-specific edges. SQL Server Agent is not available — scheduled work moves to Cloud Scheduler calling Cloud Run or Cloud Functions. The database flag list is intentionally narrow, so engine tuning that you would do with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> on premises often has no direct equivalent; the tuning surface shifts to database-scoped configuration, indexing, and Query Store–driven query design. Cross-database queries within the same instance work, but anything resembling linked-server federation to external sources is constrained.</p>

<p class="text-gray-300 leading-relaxed"><strong class="text-white">Azure SQL Database</strong> (PaaS) differs the most from the box product. SQL Server Agent does not exist — job scheduling moves to Elastic Jobs, which run T-SQL across databases and servers from a dedicated job database, or to Azure Automation and Logic Apps. CLR is restricted to <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">SAFE</code> assemblies only. R and Python external scripts (<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_execute_external_script</code>) are available in SQL Server on Azure VMs but not in Azure SQL Database PaaS; for ML workloads in Azure SQL, you use Azure ML integration or call REST endpoints from T-SQL instead. Full-text search, In-Memory OLTP, and columnstore indexes are fully available. Change Data Capture and Change Tracking are available and are the preferred CDC mechanisms in PaaS.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Audit SQL Server feature usage before a cloud migration
-- Run on the source instance to inventory components with no managed equivalent

-- 1. SQL Server Agent jobs (no Agent on RDS for SQL Server / Cloud SQL)
SELECT name AS job_name, enabled
FROM msdb.dbo.sysjobs
ORDER BY name;

-- 2. CLR assemblies (restricted to SAFE on Azure SQL, approved set on RDS)
SELECT name, permission_set_desc
FROM sys.assemblies
WHERE is_user_defined = 1;

-- 3. Linked servers (limited provider support in managed services)
SELECT name, provider, data_source
FROM sys.servers
WHERE is_linked = 1;

-- 4. External scripts / ML Services usage
SELECT OBJECT_SCHEMA_NAME(object_id) AS schema_name,
       OBJECT_NAME(object_id) AS object_name
FROM sys.sql_modules
WHERE definition LIKE '%sp_execute_external_script%';</code></pre>

<p class="text-gray-300 leading-relaxed">Run this inventory early in any migration assessment. Every Agent job needs a new home (Elastic Jobs, Lambda, Cloud Scheduler), every CLR assembly needs a permission review, and every SSIS package needs a re-platforming decision — Azure Data Factory, AWS Glue, or a self-managed SSIS runtime on EC2/GCE. Discovering these dependencies during cutover weekend is how migrations fail.</p>

'''

t = t[:si] + new_section + t[ei:]

# takeaway: rewrite the extension takeaway + streaming replication takeaway
old_tk = "An extension-dependent architecture built on self-managed PostgreSQL may not port directly to any managed service. Audit your `pg_extension` list early in a cloud migration, check availability against the target provider's current documentation, and design mitigation patterns — application-layer alternatives, Cloud Scheduler–based replacements for `pg_cron`, or a provider switch — before the migration cutover."
new_tk = "A component-dependent architecture built on self-managed SQL Server may not port directly to any managed service. Audit your Agent jobs, CLR assemblies, linked servers, and SSIS packages early in a cloud migration, check availability against the target provider's current documentation, and design mitigation patterns — Elastic Jobs or Lambda-based replacements for Agent, Azure Data Factory or Glue for SSIS — before the migration cutover."
if t.count(old_tk) != 1:
    print("takeaway not found")
    sys.exit(1)
t = t.replace(old_tk, new_tk)

old_rep = "RDS and Cloud SQL read replicas use asynchronous streaming replication and can show meaningful lag under write pressure."
new_rep = "RDS and Cloud SQL read replicas use asynchronous log shipping and can show meaningful lag under write pressure."
if t.count(old_rep) != 1:
    print("replica takeaway not found")
    sys.exit(1)
t = t.replace(old_rep, new_rep)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch05-D OK: section 5.10 rewritten + 2 takeaways fixed")
