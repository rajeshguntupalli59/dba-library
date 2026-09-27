#!/usr/bin/env python3
"""Rewrite ch05 sections 5.6-5.10 + takeaways (part C)."""
import sys, re

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch05-architecture-patterns.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

# 5.6 serverless
reps.append((
"Serverless databases — Aurora Serverless v2, Azure SQL Serverless, Neon, AlloyDB Omni — solve a specific problem:",
"Serverless databases — Aurora Serverless v2, Azure SQL Serverless — solve a specific problem:"
))
reps.append((
'  cluster_identifier  = "staging-aurora-serverless"' + NL +
'  engine              = "aurora-postgresql"' + NL +
'  engine_version      = "15.4"',
'  cluster_identifier  = "staging-aurora-serverless"' + NL +
'  engine              = "aurora-mysql"' + NL +
'  engine_version      = "8.0.mysql_aurora.3.08.0"'
))
# (autoscaling resource-id handled as a global rename below)

# 5.7 DR table
reps.append((
"<strong class=\"text-white\">AWS cross-region strategy options (RDS PostgreSQL):</strong>",
"<strong class=\"text-white\">AWS cross-region strategy options (RDS for SQL Server):</strong>"
))

# 5.8 observability
reps.append((
"On premises you assembled your own monitoring stack — Prometheus + Grafana + postgres_exporter, or Zabbix, or a commercial monitoring product.",
"On premises you assembled your own monitoring stack — Prometheus + Grafana with a SQL Server exporter, or Zabbix, or a commercial monitoring product."
))
reps.append((
"it samples <code " + CODE + ">pg_stat_activity</code>, wait events, and top SQL every second and presents a visual breakdown",
"it samples active sessions, wait events, and top SQL every second and presents a visual breakdown"
))
reps.append((
"    DBInstanceIdentifier='prod-postgres-primary'",
"    DBInstanceIdentifier='prod-sql-primary'"
))
reps.append((
"gcloud sql instances patch prod-cloudsql-pg " + BS,
"gcloud sql instances patch prod-cloudsql-sqlserver " + BS
))
# Log export -> SQL Server
reps.append((
"# AWS: Export RDS PostgreSQL logs to CloudWatch Logs" + NL +
"aws rds modify-db-instance " + BS + NL +
"  --db-instance-identifier prod-postgres-primary " + BS + NL +
"""  --cloudwatch-logs-export-configuration '{"EnableLogTypes":["postgresql","upgrade"]}' """ + BS,
"# AWS: Export RDS SQL Server logs to CloudWatch Logs" + NL +
"aws rds modify-db-instance " + BS + NL +
"  --db-instance-identifier prod-sql-primary " + BS + NL +
"""  --cloudwatch-logs-export-configuration '{"EnableLogTypes":["error","agent"]}' """ + BS
))
reps.append((
"  --log-group-name /aws/rds/instance/prod-postgres-primary/postgresql " + BS,
"  --log-group-name /aws/rds/instance/prod-sql-primary/error " + BS
))
reps.append((
"  --alarm-name prod-postgres-slow-queries " + BS,
"  --alarm-name prod-sql-slow-queries " + BS
))
reps.append((
'# First, ensure log_min_duration_statement is set to 1000 (via database flags as shown earlier)',
'# First, ensure Query Insights is enabled on the instance (as shown earlier)'
))
reps.append((
'    resource.labels.database_id="my-project:prod-cloudsql-pg"',
'    resource.labels.database_id="my-project:prod-cloudsql-sqlserver"'
))
reps.append((
'  --description="Count of Cloud SQL queries exceeding log_min_duration_statement" ' + BS,
'  --description="Count of slow Cloud SQL queries captured by Query Insights" ' + BS
))

# 5.9 cost
reps.append((
"1. Instance class (db.r6g.4xlarge Multi-AZ ≈ 2x single-AZ hourly rate)",
"1. Instance class (db.r6i.4xlarge Multi-AZ ≈ 2x single-AZ hourly rate)"
))
reps.append((
"if average DBLoad is consistently below 2 on a db.r6g.4xlarge (which has 16 vCPUs), a db.r6g.2xlarge may be appropriate.",
"if average DBLoad is consistently below 2 on a db.r6i.4xlarge (which has 16 vCPUs), a db.r6i.2xlarge may be appropriate."
))
reps.append((
"estimate_rightsizing_opportunity('prod-postgres-primary')",
"estimate_rightsizing_opportunity('prod-sql-primary')"
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

# global rename: autoscaling resource-id (2 occurrences)
t = t.replace(
    "  --resource-id cluster:prod-aurora-postgres " + BS,
    "  --resource-id cluster:prod-aurora-mysql " + BS
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch05-C OK:", len(reps), "replacements")
