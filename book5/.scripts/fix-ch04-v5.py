#!/usr/bin/env python3
"""Rewrite final PostgreSQL remnants in b5-ch04 (v5)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch04-cloud-dba-role.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

# 1. Clean up leftover empty parameter block + autovacuum_analyze block
reps.append((
"  parameter {" + NL +
'    # (removed PostgreSQL autovacuum tuning — not applicable to Aurora MySQL)' + NL +
"  }" + NL + NL +
"  parameter {" + NL +
'    name         = "autovacuum_analyze_scale_factor"' + NL +
'    value        = "0.005"' + NL +
'    apply_method = "immediate"' + NL +
"  }" + NL,
""
))

# 2. Architecture ownership paragraph
reps.append((
"An on-premises DBA might optimize a single PostgreSQL cluster indefinitely. A cloud DBA is frequently asked whether data should live in RDS, Aurora, DynamoDB, Redshift, or S3-plus-Athena,",
"An on-premises DBA might optimize a single SQL Server cluster indefinitely. A cloud DBA is frequently asked whether data should live in RDS for SQL Server, Aurora, DynamoDB, Redshift, or S3-plus-Athena,"
))

# 3. EXPLAIN code block -> SQL Server only
reps.append((
"<code>-- PostgreSQL: execution plan analysis works identically on RDS and self-managed" + NL +
"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)" + NL +
"SELECT" + NL +
"    o.order_id," + NL +
"    o.created_at," + NL +
"    c.email," + NL +
"    SUM(oi.quantity * oi.unit_price) AS order_total" + NL +
"FROM orders o" + NL +
"JOIN customers c ON o.customer_id = c.customer_id" + NL +
"JOIN order_items oi ON o.order_id = oi.order_id" + NL +
"WHERE o.created_at &gt;= NOW() - INTERVAL '30 days'" + NL +
"  AND o.status = 'completed'" + NL +
"GROUP BY o.order_id, o.created_at, c.email" + NL +
"ORDER BY o.created_at DESC;" + NL + NL +
"-- SQL Server: same analysis approach on Azure SQL" + NL +
"SET STATISTICS IO, TIME ON;",
"<code>-- SQL Server: plan and IO analysis works identically on RDS, Azure SQL, and self-managed" + NL +
"SET STATISTICS IO, TIME ON;"
))

# 4. Schema design paragraph
reps.append((
"A poorly designed schema that causes table bloat through inefficient updates will bloat just as effectively on Aurora as on a bare-metal PostgreSQL server.",
"A poorly designed schema that causes page splits through inefficient clustered index choices will fragment just as effectively on RDS as on a bare-metal SQL Server."
))

# 5. Delete the entire PostgreSQL lock-contention query body (header through its ORDER BY),
#    leaving the SQL Server blocking-chain query that follows it.
import re
pg_lock_body = re.compile(
    r"<code>-- PostgreSQL: identify lock contention \(works on RDS, Aurora, Cloud SQL identically\)\n"
    r".*?ORDER BY blocked_duration DESC;\n\n",
    re.S
)
m = pg_lock_body.search(t)
if not m:
    print("FAILED: PG lock query body pattern not found")
    sys.exit(1)
t = (t[:m.start()] + "<code>-- SQL Server: identify blocking chains (works on RDS, Azure SQL, self-managed identically)\n" + t[m.end():])

# 6. Takeaway
reps.append((
"Authentication and authorization move from engine-native mechanisms (`pg_hba.conf`, SQL Server logins) to cloud IAM layers (AWS IAM database authentication, Azure Entra ID contained users)",
"Authentication and authorization move from engine-native mechanisms (SQL Server logins, Windows authentication) to cloud IAM layers (AWS IAM database authentication, Azure Entra ID contained users)"
))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

# 7. Remove the entire PG lock-contention query body (pg_catalog.pg_locks ... through the closing of the PG query),
#    i.e. delete from the line after the (now SQL Server) header comment up to just before the SQL Server SELECT.
#    Inspect the exact span first.
if failed:
    print("FAILED REPLACEMENTS:")
    for n, s in failed:
        print("  count=" + str(n) + ": " + s)
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch04 v5 OK:", len(reps), "replacements applied")
