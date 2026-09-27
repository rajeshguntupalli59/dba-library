#!/usr/bin/env python3
"""Rewrite ch06 sections 6.3-6.4 (part B)."""
import sys

PATH = "/home/hatch/workspace/dba-library/book5/b5-ch06-rds-deep-dive.html"

with open(PATH, encoding="utf-8") as f:
    t = f.read()

NL = "\n"
BS = "\\"
CODE = 'class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs"'
reps = []

# 6.3
reps.append((
"For most PostgreSQL and MySQL workloads, gp3 with provisioned IOPS is sufficient and cheaper.",
"For most SQL Server and MySQL workloads, gp3 with provisioned IOPS is sufficient and cheaper."
))
reps.append((
"Configure a new PostgreSQL instance with gp3 and autoscaling via Terraform:",
"Configure a new SQL Server instance with gp3 and autoscaling via Terraform:"
))
reps.append((
"# terraform/rds_instance.tf" + NL + "# Production PostgreSQL RDS with gp3 storage and appropriate settings",
"# terraform/rds_instance.tf" + NL + "# Production SQL Server RDS with gp3 storage and appropriate settings"
))
reps.append((
'resource "aws_db_instance" "prod_postgres" {' + NL +
'  identifier        = "prod-postgres-primary"' + NL +
'  engine            = "postgres"' + NL +
'  engine_version    = "16.3"' + NL +
'  instance_class    = "db.r7g.4xlarge"',
'resource "aws_db_instance" "prod_sql" {' + NL +
'  identifier        = "prod-sql-primary"' + NL +
'  engine            = "sqlserver-se"' + NL +
'  engine_version    = "16.00"' + NL +
'  instance_class    = "db.r7i.4xlarge"'
))
reps.append((
"  vpc_security_group_ids = [aws_security_group.rds_postgres.id]",
"  vpc_security_group_ids = [aws_security_group.rds_sqlserver.id]"
))
reps.append((
"  parameter_group_name = aws_db_parameter_group.postgres16_prod.name",
"  parameter_group_name = aws_db_parameter_group.sqlserver2022_prod.name"
))
PG_TF_PARAMS = (
'resource "aws_db_parameter_group" "postgres16_prod" {' + NL +
'  name   = "postgres16-prod"' + NL +
'  family = "postgres16"' + NL + NL +
'  parameter {' + NL +
'    name  = "shared_buffers"' + NL +
'    value = "{DBInstanceClassMemory/4}"   # 25% of instance memory' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "effective_cache_size"' + NL +
'    value = "{DBInstanceClassMemory*3/4}"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "max_connections"' + NL +
'    value = "500"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "log_min_duration_statement"' + NL +
'    value = "1000"  # Log queries over 1 second' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "log_checkpoints"' + NL +
'    value = "1"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "log_lock_waits"' + NL +
'    value = "1"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "track_io_timing"' + NL +
'    value = "1"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "pg_stat_statements.track"' + NL +
'    value = "all"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "rds.log_retention_period"' + NL +
'    value = "10080"   # 7 days in minutes' + NL +
'  }' + NL +
'}'
)
SQL_TF_PARAMS = (
'resource "aws_db_parameter_group" "sqlserver2022_prod" {' + NL +
'  name   = "sqlserver2022-prod"' + NL +
'  family = "sqlserver-se-16.0"' + NL + NL +
'  parameter {' + NL +
'    name  = "max server memory (MB)"' + NL +
'    value = "{DBInstanceClassMemory/1048576}*3/4"   # ~75% of instance memory' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "max degree of parallelism"' + NL +
'    value = "8"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "cost threshold for parallelism"' + NL +
'    value = "50"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "fill factor (%)"' + NL +
'    value = "90"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "optimize for ad hoc workloads"' + NL +
'    value = "1"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "backup compression default"' + NL +
'    value = "1"' + NL +
'  }' + NL + NL +
'  parameter {' + NL +
'    name  = "blocked process threshold (s)"' + NL +
'    value = "30"   # capture blocking chains in the error log' + NL +
'  }' + NL +
'}'
)
reps.append((PG_TF_PARAMS, SQL_TF_PARAMS))
t = t.replace(
    "Name=DBInstanceIdentifier,Value=prod-postgres-primary",
    "Name=DBInstanceIdentifier,Value=prod-sql-primary"
)
reps.append((
"At that point, you cannot write data including WAL.",
"At that point, you cannot write data including transaction log records."
))

# 6.4
reps.append((
"6.4 Parameter Groups: The Replacement for postgresql.conf",
"6.4 Parameter Groups: The Replacement for sp_configure"
))
reps.append((
"A parameter group has a family (e.g., <code " + CODE + ">postgres16</code>, <code " + CODE + ">mysql8.0</code>, <code " + CODE + ">sqlserver-se-15.0</code>)",
"A parameter group has a family (e.g., <code " + CODE + ">sqlserver-se-16.0</code>, <code " + CODE + ">mysql8.0</code>, <code " + CODE + ">postgres16</code>)"
))
reps.append((
"AWS ships a <code " + CODE + ">default.postgres16</code> parameter group",
"AWS ships a <code " + CODE + ">default.sqlserver-se-16.0</code> parameter group"
))
reps.append((
"Examples: `shared_buffers`, `max_connections`, `wal_level`.",
"Examples: `max server memory (MB)`, `max degree of parallelism`, `fill factor (%)`."
))
reps.append((
"Examples: `log_min_duration_statement`, `effective_cache_size`, `work_mem`.",
"Examples: `cost threshold for parallelism`, `optimize for ad hoc workloads`, `backup compression default`."
))
reps.append((
"Common PostgreSQL parameter customizations for RDS:",
"Common SQL Server parameter customizations for RDS:"
))
PG_PG_CLI = (
"# Create a custom parameter group and configure key parameters" + NL + NL +
"aws rds create-db-parameter-group " + BS + NL +
"  --db-parameter-group-name postgres16-prod " + BS + NL +
"  --db-parameter-group-family postgres16 " + BS + NL +
'  --description "Production PostgreSQL 16 parameters" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Apply multiple parameters in one call" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name postgres16-prod " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=log_checkpoints,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=log_lock_waits,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=track_io_timing,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=work_mem,ParameterValue=16384,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=maintenance_work_mem,ParameterValue=262144,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=checkpoint_completion_target,ParameterValue=0.9,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=random_page_cost,ParameterValue=1.1,ApplyMethod=immediate" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Static parameters require pending reboot — apply these separately" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name postgres16-prod " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=max_connections,ParameterValue=500,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=wal_level,ParameterValue=logical,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=max_replication_slots,ParameterValue=10,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=max_wal_senders,ParameterValue=10,ApplyMethod=pending-reboot" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Apply the parameter group to the instance (takes effect after maintenance window" + NL +
"# unless you use --apply-immediately, which causes a brief interruption)" + NL +
"aws rds modify-db-instance " + BS + NL +
"  --db-instance-identifier prod-postgres-primary " + BS + NL +
"  --db-parameter-group-name postgres16-prod " + BS + NL +
"  --region us-east-1"
)
SQL_PG_CLI = (
"# Create a custom parameter group and configure key parameters" + NL + NL +
"aws rds create-db-parameter-group " + BS + NL +
"  --db-parameter-group-name sqlserver2022-prod " + BS + NL +
"  --db-parameter-group-family sqlserver-se-16.0 " + BS + NL +
'  --description "Production SQL Server 2022 parameters" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Apply multiple parameters in one call" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name sqlserver2022-prod " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=cost threshold for parallelism,ParameterValue=50,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=max degree of parallelism,ParameterValue=8,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=optimize for ad hoc workloads,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=backup compression default,ParameterValue=1,ApplyMethod=immediate" ' + BS + NL +
'    "ParameterName=blocked process threshold (s),ParameterValue=30,ApplyMethod=immediate" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Static parameters require pending reboot — apply these separately" + NL +
"aws rds modify-db-parameter-group " + BS + NL +
"  --db-parameter-group-name sqlserver2022-prod " + BS + NL +
"  --parameters " + BS + NL +
'    "ParameterName=max server memory (MB),ParameterValue={DBInstanceClassMemory/1048576}*3/4,ApplyMethod=pending-reboot" ' + BS + NL +
'    "ParameterName=fill factor (%),ParameterValue=90,ApplyMethod=pending-reboot" ' + BS + NL +
"  --region us-east-1" + NL + NL +
"# Apply the parameter group to the instance (takes effect after maintenance window" + NL +
"# unless you use --apply-immediately, which causes a brief interruption)" + NL +
"aws rds modify-db-instance " + BS + NL +
"  --db-instance-identifier prod-sql-primary " + BS + NL +
"  --db-parameter-group-name sqlserver2022-prod " + BS + NL +
"  --region us-east-1"
)
reps.append((PG_PG_CLI, SQL_PG_CLI))
reps.append((
"aws rds describe-db-instances " + BS + NL + "  --db-instance-identifier prod-postgres-primary " + BS + NL + "  --query 'DBInstances[0].DBParameterGroups'",
"aws rds describe-db-instances " + BS + NL + "  --db-instance-identifier prod-sql-primary " + BS + NL + "  --query 'DBInstances[0].DBParameterGroups'"
))
PG_VERIFY_Q = (
"<code>-- PostgreSQL: Check current effective values of key parameters" + NL +
"SELECT name, setting, unit, context, source" + NL +
"FROM pg_settings" + NL +
"WHERE name IN (" + NL +
"    'shared_buffers'," + NL +
"    'work_mem'," + NL +
"    'maintenance_work_mem'," + NL +
"    'max_connections'," + NL +
"    'effective_cache_size'," + NL +
"    'checkpoint_completion_target'," + NL +
"    'random_page_cost'," + NL +
"    'wal_level'," + NL +
"    'track_io_timing'," + NL +
"    'log_min_duration_statement'" + NL +
")" + NL +
"ORDER BY name;" + NL + NL +
"-- Check which parameters are still using default values vs. customized" + NL +
"SELECT name, setting, boot_val, reset_val, source" + NL +
"FROM pg_settings" + NL +
"WHERE source != 'default'" + NL +
"  AND source != 'override'" + NL +
"ORDER BY name;</code>"
)
SQL_VERIFY_Q = (
"<code>-- SQL Server: Check current effective values of key parameters" + NL +
"SELECT name, value, value_in_use, description, is_dynamic" + NL +
"FROM sys.configurations" + NL +
"WHERE name IN (" + NL +
"    'max server memory (MB)'," + NL +
"    'max degree of parallelism'," + NL +
"    'cost threshold for parallelism'," + NL +
"    'fill factor (%)'," + NL +
"    'optimize for ad hoc workloads'," + NL +
"    'backup compression default'," + NL +
"    'blocked process threshold (s)'," + NL +
"    'remote query timeout (s)'" + NL +
")" + NL +
"ORDER BY name;</code>"
)
reps.append((
"You can also verify parameter values from inside PostgreSQL after applying:",
"You can also verify parameter values from inside SQL Server after applying:"
))
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
print("ch06-B OK:", len(reps), "replacements")
