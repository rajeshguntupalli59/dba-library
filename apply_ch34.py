#!/usr/bin/env python3
"""Apply ch34 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch34-compliance.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
("""PostgreSQL does not have a built-in comprehensive audit facility comparable to SQL Server's native options, but the %s extension fills that gap cleanly. %s integrates with PostgreSQL's standard logging infrastructure and allows you to log session-level activity (everything a session does) or object-level activity (specific operations on specific objects). For compliance purposes, object-level auditing is usually what you want, because session logging tends to produce enormous volumes of noise.""" % (code('pgaudit'), code('pgaudit')),
 """SQL Server Audit is the native, comprehensive audit facility: server audits, server audit specifications, and database audit specifications capture logins, permission changes, and DDL/DML at whatever granularity compliance requires. For compliance purposes, object-level auditing is usually what you want, because session-level logging tends to produce enormous volumes of noise."""),

("Beyond extension-based or native auditing, both databases support trigger-based audit tables",
 "Beyond native auditing, SQL Server supports trigger-based audit tables"),
("""Using autonomous transactions (available in PostgreSQL through %s to a separate connection, or through a foreign data wrapper) can address the rollback problem at the cost of additional complexity.""" % code('dblink'),
 """The robust answer is SQL Server Audit's file target, which is written outside the transaction and cannot be rolled back with it."""),

("""PostgreSQL's permission model is built around roles. Roles can be users (they can log in) or groups (they cannot log in directly but can be granted to other roles). This makes it straightforward to build a layered permission model where you define roles by job function and assign those roles to users.""",
 """SQL Server's permission model is built around server roles, database roles, and securables. Logins authenticate at the server level, users map them into databases, and roles collect permissions by job function. This makes it straightforward to build a layered permission model where you define roles by job function and assign those roles to users."""),

("""Both PostgreSQL and SQL Server support transparent data encryption (TDE) at the storage level. SQL Server's TDE is a native enterprise feature available in Standard and Enterprise editions. PostgreSQL does not have built-in TDE, but file system-level encryption (like Linux's LUKS or dm-crypt) achieves the same protection for the data files. Some PostgreSQL distributions, including EDB's Advanced Server and certain cloud offerings, do provide TDE at the cluster level.""",
 """SQL Server supports transparent data encryption (TDE) at the storage level natively, in Standard and Enterprise editions as well as Azure SQL Database. TDE encrypts data and log files with a database encryption key protected by a certificate in master — backups are encrypted too, which closes the backup-file exposure that auditors always ask about."""),

("""In PostgreSQL, the %s extension provides encryption and decryption functions. In SQL Server, Always Encrypted shifts encryption key management to the client application so that even the DBA cannot read plaintext values.""" % code('pgcrypto'),
 """In SQL Server, Always Encrypted shifts encryption key management to the client application so that even the DBA cannot read plaintext values. For in-database column encryption without application changes, cell-level encryption with %s and symmetric keys protects specific values from users who can read the table.""" % code('ENCRYPTBYKEY')),

("""PostgreSQL does not have a built-in equivalent to DDM, but masking can be implemented through views that apply masking logic based on the current user or a session-level setting. The %s (PostgreSQL Anonymizer) extension provides a more complete masking framework with declarative masking rules similar to DDM.""" % code('anon'),
 """Dynamic Data Masking (DDM) is built into SQL Server: define masking functions on columns (default, email, random, custom string) and unprivileged users see masked values while privileged users see the real data. No application changes are needed — masking happens at query time based on the UNMASK permission."""),

("""In PostgreSQL, declarative partitioning by date makes retention management cleaner: a partition covering a specific month or year can be dropped with a single %s command on the partition, which is far faster and less disruptive than a %s statement against millions of rows.""" % (code('DROP TABLE'), code('DELETE')),
 """In SQL Server, partitioning by date with a sliding window makes retention management cleaner: a partition covering a specific month or year can be removed with %s or switched out and dropped, which is far faster and less disruptive than a %s statement against millions of rows.""" % (code('TRUNCATE TABLE ... WITH (PARTITIONS (...))'), code('DELETE'))),

("<strong class=\"text-white\">PostgreSQL (Flyway migration tracking table):</strong>",
 "<strong class=\"text-white\">Flyway migration tracking table (SQL Server):</strong>"),

("""Your database server configuration — %s, SQL Server's sp_configure settings, TLS certificate configurations, authentication method settings in %s — should be version-controlled and reviewed periodically. A change to %s that adds an unauthenticated connection method, or a SQL Server configuration change that enables xp_cmdshell, is exactly the kind of drift that auditors look for and that can go unnoticed in an environment with poor change control.""" % (code('postgresql.conf'), code('pg_hba.conf'), code('pg_hba.conf')),
 """Your database server configuration — SQL Server's sp_configure settings, TLS certificate configurations, login and authentication settings — should be version-controlled and reviewed periodically. A SQL Server configuration change that enables xp_cmdshell or weakens login auditing is exactly the kind of drift that auditors look for and that can go unnoticed in an environment with poor change control."""),

("the CIS Benchmark hardening scripts for PostgreSQL and SQL Server provide codified security baselines",
 "the CIS Benchmark hardening scripts for SQL Server provide codified security baselines"),

("<strong class=\"text-white\">PostgreSQL — checking key configuration values against a security baseline:</strong>",
 "<strong class=\"text-white\">SQL Server — checking key configuration values against a security baseline:</strong>"),

("""<code>-- Query current configuration to compare against documented baseline
SELECT
    name,
    setting,
    unit,
    context,
    short_desc
FROM pg_settings
WHERE name IN (
    'ssl',
    'ssl_min_protocol_version',
    'password_encryption',
    'log_connections',
    'log_disconnections',
    'log_duration',
    'log_statement',
    'shared_preload_libraries',
    'pgaudit.log',
    'row_security'
)
ORDER BY name;</code>""",
 """<code>-- Query current configuration to compare against documented baseline
SELECT name,
       value_in_use,
       is_advanced
FROM sys.configurations
WHERE name IN (
    'xp_cmdshell',
    'Ole Automation Procedures',
    'clr enabled',
    'cross db ownership chaining',
    'remote access',
    'Database Mail XPs',
    'backup compression default'
)
ORDER BY name;</code>"""),

("""For PostgreSQL environments, DDL auditing through %s captures schema object changes when configured at the session or object level with %s included in the %s parameter:""" % (code('pgaudit'), code('DDL'), code('pgaudit.log')),
 """For DDL auditing, a database audit specification with %s captures every schema change with who and when:""" % code('SCHEMA_OBJECT_CHANGE_GROUP')),

("PostgreSQL has native row-level security with a clean policy syntax. SQL Server provides a similar feature also called Row-Level Security, implemented through inline table-valued functions used as security predicates.",
 "SQL Server provides Row-Level Security, implemented through inline table-valued functions used as security predicates bound to tables by a security policy."),

("PostgreSQL RLS handles this through WITH CHECK clauses on policies when you want write restrictions in addition to read filtering.",
 "For write restrictions in addition to read filtering, add a block predicate to the same security policy."),

("Many organizations now run PostgreSQL and SQL Server in cloud-managed environments — Amazon RDS, Amazon Aurora, Google Cloud SQL, Azure Database for PostgreSQL, Azure SQL Database, and similar services.",
 "Many organizations now run SQL Server in cloud-managed environments — Amazon RDS for SQL Server, Google Cloud SQL for SQL Server, Azure SQL Database, and Azure SQL Managed Instance."),

("""Amazon RDS for PostgreSQL supports %s through parameter groups. Aurora PostgreSQL similarly supports %s and can stream audit logs to CloudWatch. Azure Database for PostgreSQL supports server logs and Azure Monitor integration. For SQL Server, Azure SQL Database has its own built-in auditing feature that writes to Azure Blob Storage or Azure Log Analytics, and this is generally preferable to the file-based SQL Server Audit approach in on-premises environments.""" % (code('pgaudit'), code('pgaudit')),
 """For SQL Server, Azure SQL Database has its own built-in auditing feature that writes to Azure Blob Storage or Azure Log Analytics, and this is generally preferable to the file-based SQL Server Audit approach in on-premises environments. RDS for SQL Server can publish audit and error logs to CloudWatch Logs for the same centralized-analysis pattern."""),

("Auditing should be implemented through purpose-built tools (`pgaudit` in PostgreSQL, SQL Server Audit in SQL Server) rather than relying solely on trigger-based approaches,",
 "Auditing should be implemented through purpose-built tools (SQL Server Audit) rather than relying solely on trigger-based approaches,"),

("column-level encryption (pgcrypto, Always Encrypted) protects values from privileged database users,",
 "column-level encryption (cell-level encryption, Always Encrypted) protects values from privileged database users,"),
("data masking (Dynamic Data Masking in SQL Server, view-based masking or the `anon` extension in PostgreSQL) limits what authorized users see during normal operations.",
 "data masking (Dynamic Data Masking) limits what authorized users see during normal operations."),
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
    print(f'ch34: all {len(REPLACEMENTS)} replacements applied')

main()
