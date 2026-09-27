#!/usr/bin/env python3
"""Rewrite PostgreSQL-centric content in b5-ch02 to SQL Server focus."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch02-managed-vs-self-managed.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

reps = []

reps.append((
"""When you ran PostgreSQL on bare metal or VMware, your responsibility surface looked like this: hardware procurement, OS patching, filesystem layout, network configuration, PostgreSQL installation, parameter tuning, backup scheduling, replication setup, failover scripting, and monitoring.""",
"""When you ran SQL Server on bare metal or VMware, your responsibility surface looked like this: hardware procurement, OS patching, disk layout, network configuration, SQL Server installation, sp_configure tuning, backup scheduling, Always On setup, failover scripting, and monitoring."""
))

reps.append((
"""You cannot install extensions that are not on the approved list, you cannot modify <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code> directly, and you cannot change the PostgreSQL binary. What you can do is control almost everything above that layer: parameter groups, option groups, subnet groups, security groups, IAM authentication, automated backup retention up to 35 days, and Multi-AZ deployment.""",
"""You cannot install components that are not on the supported list — no SQL Server Agent, no SSIS, SSAS, or SSRS — you cannot add startup parameters or trace flags beyond the curated set AWS exposes, and you cannot change the SQL Server binaries. What you can do is control almost everything above that layer: parameter groups, option groups, subnet groups, security groups, IAM authentication, automated backup retention up to 35 days, and Multi-AZ deployment."""
))

reps.append((
"""It runs PostgreSQL, MySQL, or SQL Server on Compute Engine VMs that Google manages. You get database flags (the equivalent of postgresql.conf parameters), authorized networks, private IP configuration, and automated backups. Like RDS, the OS is not yours.""",
"""It runs SQL Server, MySQL, or PostgreSQL on Compute Engine VMs that Google manages. For SQL Server you get a small set of database flags (the equivalent of sp_configure parameters), authorized networks, private IP configuration, and automated backups. Like RDS, the OS is not yours."""
))

# Access boundary table
reps.append((
"""| Capability | Self-Managed PostgreSQL | AWS RDS PostgreSQL | Azure SQL | Cloud SQL PostgreSQL |""",
"""| Capability | Self-Managed SQL Server | RDS for SQL Server | Azure SQL | Cloud SQL for SQL Server |"""
))
reps.append((
"""| Modify <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_hba.conf</code> | Yes | No (use IAM/security groups) | N/A | No (use authorized networks) |""",
"""| Manage logins and authentication rules at OS level | Yes | No (use IAM/security groups) | N/A | No (use authorized networks) |"""
))
reps.append((
"""| Access WAL files directly | Yes | No (can stream via logical replication) | N/A | No |""",
"""| Access the transaction log directly | Yes | No | N/A | No |"""
))
reps.append((
"""| <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_basebackup</code> to external target | Yes | No (use native backup export to S3) |N/A | No (use export to GCS) |""",
"""| Native <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">BACKUP DATABASE</code> to external target | Yes | Yes (to S3 via the SQLSERVER_BACKUP_RESTORE option group) | N/A | Yes (to GCS) |"""
))
reps.append((
"""The <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">rds_superuser</code> point deserves emphasis. On RDS PostgreSQL, you receive a user with the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">rds_superuser</code> role. This gives you the ability to manage other users, replication slots, logical replication, and most administrative functions. But it does not give you <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_read_all_settings</code> on internal parameters, and it cannot create C-language extensions. If you have built any tooling that depends on superuser-level OS interaction — for example, a custom archiving script that writes directly to the filesystem — that tooling requires redesign.""",
"""The master-user privilege point deserves emphasis. On RDS for SQL Server, the master user you create at provisioning time is <strong class="text-white">not</strong> a full <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sysadmin</code>. It can manage logins, databases, and most administrative functions, but it cannot grant itself server-level permissions that AWS reserves, cannot install components outside the supported set, and cannot touch the OS. If you have built any tooling that depends on sysadmin-level OS interaction — for example, a maintenance script that shells out with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">xp_cmdshell</code> or writes directly to the filesystem — that tooling requires redesign."""
))

# Parameter tuning section
reps.append((
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">Parameter Tuning: From postgresql.conf to Parameter Groups</h3>

<p class="text-gray-300 leading-relaxed">On a self-managed PostgreSQL instance, tuning <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">work_mem</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">shared_buffers</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">checkpoint_completion_target</code>, and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">effective_cache_size</code> means editing a file and reloading or restarting. In RDS, that workflow translates to parameter groups.</p>""",
"""<h3 class="text-lg font-semibold text-white mt-8 mb-3">Parameter Tuning: From sp_configure to Parameter Groups</h3>

<p class="text-gray-300 leading-relaxed">On a self-managed SQL Server instance, tuning <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max server memory (MB)</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">cost threshold for parallelism</code>, <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">max degree of parallelism</code>, and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">fill factor (%)</code> means running <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> and possibly restarting. In RDS, that workflow translates to parameter groups.</p>"""
))

reps.append((
"""# Create a custom RDS parameter group for PostgreSQL 15
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-pg15-custom \\
  --db-parameter-group-family postgres15 \\
  --description "Production PostgreSQL 15 parameter group" \\
  --region us-east-1

# Modify key parameters
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-pg15-custom \\
  --parameters \\
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \\
    "ParameterName=checkpoint_completion_target,ParameterValue=0.9,ApplyMethod=immediate" \\
    "ParameterName=max_connections,ParameterValue=500,ApplyMethod=pending-reboot" \\
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \\
  --region us-east-1

# Apply the parameter group to an existing instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-pg-primary \\
  --db-parameter-group-name prod-pg15-custom \\
  --apply-immediately \\
  --region us-east-1</code></pre>""",
"""# Create a custom RDS parameter group for SQL Server 2022 (Standard Edition)
aws rds create-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-custom \\
  --db-parameter-group-family sqlserver-se-16.0 \\
  --description "Production SQL Server 2022 parameter group" \\
  --region us-east-1

# Modify key parameters (the sp_configure equivalents)
aws rds modify-db-parameter-group \\
  --db-parameter-group-name prod-sql2022-custom \\
  --parameters \\
    "ParameterName=max server memory (MB),ParameterValue={DBInstanceClassMemory/1048576}*3/4,ApplyMethod=pending-reboot" \\
    "ParameterName=cost threshold for parallelism,ParameterValue=50,ApplyMethod=immediate" \\
    "ParameterName=max degree of parallelism,ParameterValue=8,ApplyMethod=immediate" \\
    "ParameterName=fill factor (%),ParameterValue=90,ApplyMethod=pending-reboot" \\
    "ParameterName=optimize for ad hoc workloads,ParameterValue=1,ApplyMethod=immediate" \\
  --region us-east-1

# Apply the parameter group to an existing instance
aws rds modify-db-instance \\
  --db-instance-identifier prod-sql-primary \\
  --db-parameter-group-name prod-sql2022-custom \\
  --apply-immediately \\
  --region us-east-1</code></pre>"""
))

reps.append((
"""On Google Cloud SQL, the equivalent concept is <strong class="text-white">database flags</strong>. The syntax and application mechanism differ, but the intent is the same. Note that Cloud SQL does not support all PostgreSQL parameters — some low-level settings are fixed by Google.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Set database flags on a Cloud SQL PostgreSQL instance
gcloud sql instances patch prod-pg-instance \\
  --database-flags \\
    max_connections=500,\\
    work_mem=65536,\\
    checkpoint_completion_target=0.9,\\
    log_min_duration_statement=1000 \\
  --project my-gcp-project

# Verify current flags
gcloud sql instances describe prod-pg-instance \\
  --project my-gcp-project \\
  --format="json(settings.databaseFlags)"</code></pre>""",
"""On Google Cloud SQL for SQL Server, the equivalent concept is <strong class="text-white">database flags</strong>. The syntax and application mechanism differ, but the intent is the same. Note that Cloud SQL for SQL Server exposes only a small flag surface — most instance tuning still happens with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sp_configure</code> inside the instance.</p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code># Set database flags on a Cloud SQL for SQL Server instance
gcloud sql instances patch prod-sql-instance \\
  --database-flags \\
    max degree of parallelism=4 \\
  --project my-gcp-project

# Verify current flags
gcloud sql instances describe prod-sql-instance \\
  --project my-gcp-project \\
  --format="json(settings.databaseFlags)"</code></pre>"""
))

# HA section
reps.append((
"""In a self-managed PostgreSQL environment, high availability required you to configure streaming replication, set <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">primary_conninfo</code>, manage <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">recovery.conf</code> (or <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">standby.signal</code> in PostgreSQL 12+), build a failover mechanism with Patroni, Repmgr, or a custom script, and test it regularly. That is a significant operational surface.""",
"""In a self-managed SQL Server environment, high availability required you to build a Windows Server Failover Cluster, configure Always On availability groups, set up the availability group listener, write the failover detection and alerting, and test it regularly. That is a significant operational surface."""
))
reps.append((
"""RDS Multi-AZ reduces that surface dramatically. When you enable Multi-AZ on an RDS PostgreSQL instance, AWS provisions a synchronous standby in a different Availability Zone, manages the replication, monitors the primary, and executes automatic failover — typically completing within 60 to 120 seconds for standard RDS.""",
"""RDS Multi-AZ reduces that surface dramatically. When you enable Multi-AZ on an RDS for SQL Server instance, AWS provisions a synchronous standby in a different Availability Zone using SQL Server's own high-availability technology under the hood, manages the replication, monitors the primary, and executes automatic failover — typically completing within 60 to 120 seconds for standard RDS."""
))

# Python failover example -> pyodbc
reps.append((
"""# Python example: RDS-aware connection handling with retry logic
# This pattern is necessary because RDS/Aurora failover breaks existing connections

import boto3
import psycopg2
import time
import logging
from psycopg2 import OperationalError

logger = logging.getLogger(__name__)

def get_rds_connection(host, port, dbname, user, password,
                        max_retries=5, retry_delay=2):
    \"\"\"
    Establish a connection to RDS with retry logic suitable for
    Multi-AZ failover scenarios. On failover, DNS propagation
    may take 5-30 seconds; this loop handles the gap.
    \"\"\"
    attempt = 0
    last_error = None

    while attempt &lt; max_retries:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password,
                connect_timeout=5,
                # options=-c statement_timeout=30000 for 30s query timeout
                options="-c statement_timeout=30000"
            )
            conn.set_session(autocommit=False)
            logger.info(f"Connected to RDS at {host} on attempt {attempt + 1}")
            return conn

        except OperationalError as e:
            last_error = e
            attempt += 1
            logger.warning(
                f"RDS connection attempt {attempt} failed: {e}. "
                f"Retrying in {retry_delay}s..."
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # exponential backoff, cap at 30s

    raise RuntimeError(
        f"Could not connect to RDS after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


def execute_with_reconnect(host, port, dbname, user, password, query, params=None):
    \"\"\"
    Execute a query and handle connection failures that can occur
    mid-session during failover events.
    \"\"\"
    conn = get_rds_connection(host, port, dbname, user, password)
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.fetchall() if cur.description else None
    except OperationalError as e:
        logger.error(f"Query failed, connection likely lost during failover: {e}")
        conn.close()
        # Re-raise so the caller can decide whether to retry at the business logic level
        raise
    finally:
        if not conn.closed:
            conn.close()</code></pre>""",
"""# Python example: RDS-aware connection handling with retry logic
# This pattern is necessary because RDS/Aurora failover breaks existing connections

import pyodbc
import time
import logging

logger = logging.getLogger(__name__)

CONN_TEMPLATE = (
    "DRIVER={{ODBC Driver 18 for SQL Server}};"
    "SERVER={host},{port};DATABASE={dbname};"
    "UID={user};PWD={password};"
    "Encrypt=yes;TrustServerCertificate=no;"
    "Connect Timeout=5;"
)

def get_rds_connection(host, port, dbname, user, password,
                        max_retries=5, retry_delay=2):
    \"\"\"
    Establish a connection to RDS with retry logic suitable for
    Multi-AZ failover scenarios. On failover, DNS propagation
    may take 5-30 seconds; this loop handles the gap.
    \"\"\"
    attempt = 0
    last_error = None

    while attempt &lt; max_retries:
        try:
            conn = pyodbc.connect(
                CONN_TEMPLATE.format(host=host, port=port, dbname=dbname,
                                     user=user, password=password),
                autocommit=False,
            )
            logger.info(f"Connected to RDS at {host} on attempt {attempt + 1}")
            return conn

        except pyodbc.Error as e:
            last_error = e
            attempt += 1
            logger.warning(
                f"RDS connection attempt {attempt} failed: {e}. "
                f"Retrying in {retry_delay}s..."
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)  # exponential backoff, cap at 30s

    raise RuntimeError(
        f"Could not connect to RDS after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


def execute_with_reconnect(host, port, dbname, user, password, query, params=None):
    \"\"\"
    Execute a query and handle connection failures that can occur
    mid-session during failover events.
    \"\"\"
    conn = get_rds_connection(host, port, dbname, user, password)
    try:
        cur = conn.cursor()
        cur.execute(query, params or [])
        rows = cur.fetchall() if cur.description else None
        conn.commit()
        cur.close()
        return rows
    except pyodbc.Error as e:
        logger.error(f"Query failed, connection likely lost during failover: {e}")
        conn.close()
        # Re-raise so the caller can decide whether to retry at the business logic level
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass</code></pre>"""
))

reps.append((
"""For multi-region automatic failover in Google Cloud, the answer is <strong class="text-white">AlloyDB</strong> or <strong class="text-white">Cloud Spanner</strong>, not Cloud SQL.""",
"""For multi-region automatic failover of a SQL Server workload in Google Cloud, Cloud SQL for SQL Server is not the answer — you architect it with cross-region read replicas and manual promotion, or choose a platform whose SQL Server offering has it built in."""
))

# Backup section
reps.append((
"""On a self-managed PostgreSQL instance, your backup strategy involved <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_basebackup</code> for full backups, WAL archiving to a shared storage target, and periodic validation through <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_restore</code> test runs. You controlled the retention schedule, the storage location, and the restore procedure.""",
"""On a self-managed SQL Server instance, your backup strategy involved <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">BACKUP DATABASE</code> for full backups, transaction log backups to a network target, and periodic validation through <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">RESTORE VERIFYONLY</code> and full test restores. You controlled the retention schedule, the storage location, and the restore procedure."""
))
reps.append((
"""or you use the restored instance to extract specific data with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_dump</code> and load it into the production instance.""",
"""or you use the restored instance to extract specific data with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">bcp</code> or an SSMS export and load it into the production instance."""
))
reps.append((
"""aws rds restore-db-instance-to-point-in-time \\
  --source-db-instance-identifier prod-pg-primary \\
  --target-db-instance-identifier prod-pg-pitr-restore-20240115 \\
  --restore-time 2024-01-15T14:30:00Z \\
  --db-instance-class db.r6g.2xlarge \\
  --db-subnet-group-name prod-subnet-group \\
  --vpc-security-group-ids sg-0abc123def456789 \\
  --no-publicly-accessible \\
  --region us-east-1

# Monitor the restore status
aws rds describe-db-instances \\
  --db-instance-identifier prod-pg-pitr-restore-20240115 \\""",
"""aws rds restore-db-instance-to-point-in-time \\
  --source-db-instance-identifier prod-sql-primary \\
  --target-db-instance-identifier prod-sql-pitr-restore-20240115 \\
  --restore-time 2024-01-15T14:30:00Z \\
  --db-instance-class db.r6i.2xlarge \\
  --db-subnet-group-name prod-subnet-group \\
  --vpc-security-group-ids sg-0abc123def456789 \\
  --no-publicly-accessible \\
  --region us-east-1

# Monitor the restore status
aws rds describe-db-instances \\
  --db-instance-identifier prod-sql-pitr-restore-20240115 \\"""
))

# Terraform section
reps.append((
"""# Terraform configuration for a production-grade RDS PostgreSQL instance
# This encodes the decisions that matter most at provisioning time.""",
"""# Terraform configuration for a production-grade RDS for SQL Server instance
# This encodes the decisions that matter most at provisioning time."""
))
reps.append((
"""  description             = "RDS encryption key for production PostgreSQL\"""",
"""  description             = "RDS encryption key for production SQL Server\""""
))
reps.append((
"""# Custom parameter group for PostgreSQL 15
resource "aws_db_parameter_group" "pg15_prod" {
  name   = "prod-pg15-custom"
  family = "postgres15"
  description = "Production PostgreSQL 15 parameters"

  parameter {
    name         = "work_mem"
    value        = "65536"
    apply_method = "immediate"
  }

  parameter {
    name         = "checkpoint_completion_target"
    value        = "0.9"
    apply_method = "immediate"
  }

  parameter {
    name         = "log_min_duration_statement"
    value        = "1000"
    apply_method = "immediate"
  }

  parameter {
    name         = "log_connections"
    value        = "1"
    apply_method = "immediate"
  }

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements,auto_explain"
    apply_method = "pending-reboot"
  }
}""",
"""# Custom parameter group for SQL Server 2022 (Standard Edition)
resource "aws_db_parameter_group" "sql2022_prod" {
  name   = "prod-sql2022-custom"
  family = "sqlserver-se-16.0"
  description = "Production SQL Server 2022 parameters"

  parameter {
    name         = "max server memory (MB)"
    value        = "{DBInstanceClassMemory/1048576}*3/4"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "cost threshold for parallelism"
    value        = "50"
    apply_method = "immediate"
  }

  parameter {
    name         = "max degree of parallelism"
    value        = "8"
    apply_method = "immediate"
  }

  parameter {
    name         = "fill factor (%)"
    value        = "90"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "optimize for ad hoc workloads"
    value        = "1"
    apply_method = "immediate"
  }
}"""
))
reps.append((
"""# Production RDS PostgreSQL instance
resource "aws_db_instance" "prod_pg" {
  identifier        = "prod-pg-primary"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r6g.2xlarge"  # 8 vCPU, 64 GB RAM""",
"""# Production RDS for SQL Server instance
resource "aws_db_instance" "prod_sql" {
  identifier        = "prod-sql-primary"
  engine            = "sqlserver-se"
  engine_version    = "16.00"
  instance_class    = "db.r6i.2xlarge"  # 8 vCPU, 64 GB RAM"""
))
reps.append((
"""  # Parameter group
  parameter_group_name = aws_db_parameter_group.pg15_prod.name""",
"""  # Parameter group
  parameter_group_name = aws_db_parameter_group.sql2022_prod.name"""
))
reps.append((
"""  final_snapshot_identifier = "prod-pg-primary-final-snapshot"

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade"
  ]""",
"""  final_snapshot_identifier = "prod-sql-primary-final-snapshot"

  enabled_cloudwatch_logs_exports = [
    "error",
    "agent"
  ]"""
))

# Key takeaways
reps.append((
"""The `rds_superuser`, `cloudsqlsuperuser`, and Azure SQL `db_owner` roles are not equivalent to OS-level superuser access.""",
"""The RDS master user, `cloudsqlsuperuser`, and Azure SQL `db_owner` roles are not equivalent to full sysadmin or OS-level access."""
))

failed = []
for old, new in reps:
    n = t.count(old)
    if n == 1:
        t = t.replace(old, new)
    else:
        failed.append((n, old[:90]))

if failed:
    print("FAILED REPLACEMENTS:")
    for n, s in failed:
        print(f"  count={n}: {s}")
    sys.exit(1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(t)
print("ch02 OK:", len(reps), "replacements applied")
