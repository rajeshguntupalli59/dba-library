#!/usr/bin/env python3
"""Apply ch38 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch38-audits.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x):
    return '<code class="%s">%s</code>' % (C, x)

R = []

R.append((
    "This chapter covers how auditing works in both PostgreSQL and SQL Server,",
    "This chapter covers how auditing works in SQL Server,",
))

R.append((
    "PostgreSQL Audit Architecture",
    "Audit Granularity: What to Capture",
))

R.append((
    "PostgreSQL does not ship with a built-in, GUI-driven audit module, but it provides robust primitives from which a complete audit system can be built. The two main mechanisms are the built-in logging system and the " + code('pgaudit') + " extension.",
    "SQL Server Audit works at two levels: server audit specifications capture server-scoped events (logins, permission changes, server role membership), while database audit specifications capture database-scoped events (DDL, DML on selected objects, permission changes). The discipline is the same as anywhere: audit at the object level for compliance evidence, because session-level capture of everything produces enormous volumes of noise.",
))

R.append((
    "<strong class=\"text-white\">PostgreSQL's native logging</strong> is controlled through " + code('postgresql.conf') + " parameters.",
    "<strong class=\"text-white\">SQL Server's native error log</strong> records session lifecycle and startup events, but it is not an audit trail. Treat the error log as a complement to SQL Server Audit, not a substitute: login auditing (" + code('Failed logins only') + " at minimum) catches authentication probing, while the audit specifications capture the authorized-but-interesting actions.",
))

R.append((
    "<strong class=\"text-white\">pgaudit</strong> is the production-grade solution. It is an open-source extension maintained by the pgaudit project and supported on PostgreSQL versions back through 9.5. It hooks into the executor and produces clean, structured audit log records that are interleaved with the PostgreSQL log but clearly identifiable by their " + code('AUDIT:') + " prefix. pgaudit operates at two levels: <strong class=\"text-white\">session-level</strong> auditing, which applies to the entire connection, and <strong class=\"text-white\">object-level</strong> auditing, which applies to specific tables, views, or functions.",
    "<strong class=\"text-white\">SQL Server Audit</strong> is the production-grade solution. It hooks into the engine's eventing infrastructure and produces clean, structured audit records written to a file, the Windows Security log, the Application log, or Azure storage. It operates at two levels: <strong class=\"text-white\">server-level</strong> auditing, which applies to the whole instance, and <strong class=\"text-white\">database-level</strong> auditing, which applies to specific databases and objects.",
))

R.append((
    "<code># postgresql.conf\nshared_preload_libraries = 'pgaudit'\npgaudit.log = 'ddl, role, connection'\npgaudit.log_catalog = off\npgaudit.log_relation = on\npgaudit.log_parameter = on</code>",
    "<code>-- Production audit baseline: failed logins, DDL, permission changes\nCREATE SERVER AUDIT ProdAudit\nTO FILE (FILEPATH = N'C:\\Audit\\', MAXSIZE = 100 MB, MAX_ROLLOVER_FILES = 20)\nWITH (ON_FAILURE = FAIL_OPERATION);\n\nCREATE SERVER AUDIT SPECIFICATION ProdServerSpec\nFOR SERVER AUDIT ProdAudit\nADD (FAILED_LOGIN_GROUP),\nADD (SERVER_PERMISSION_CHANGE_GROUP);\n\nCREATE DATABASE AUDIT SPECIFICATION ProdDbSpec\nFOR SERVER AUDIT ProdAudit\nADD (SCHEMA_OBJECT_CHANGE_GROUP),\nADD (DATABASE_PERMISSION_CHANGE_GROUP)\nWITH (STATE = ON);\n\nALTER SERVER AUDIT ProdAudit WITH (STATE = ON);</code>",
))

R.append((
    "The " + code('pgaudit.log') + " parameter accepts a comma-separated list of statement classes:",
    "The audit action groups accept a fixed vocabulary of event classes — " + code('FAILED_LOGIN_GROUP') + ", " + code('SCHEMA_OBJECT_CHANGE_GROUP') + ", " + code('DATABASE_OBJECT_CHANGE_GROUP') + " — so be deliberate:",
))

R.append((
    "An audit trail is only useful if you can interrogate it. The mechanics of reading audit data differ significantly between the two platforms.",
    "An audit trail is only useful if you can interrogate it. The mechanics of reading audit data depend on the audit target you chose.",
))

R.append((
    "In PostgreSQL with pgaudit, audit records live in the PostgreSQL log files. On most Linux deployments using systemd, you can capture logs with " + code('journalctl') + ", or you can configure PostgreSQL to write to CSV format using " + code("log_destination = 'csvlog'") + " and " + code('logging_collector = on') + ". CSV logging makes the audit records machine-readable without a parsing script:",
    "With SQL Server Audit writing to files, audit records are queried with " + code('sys.fn_get_audit_file') + " — a table-valued function that reads the binary audit files as rows, so you can filter, aggregate, and join audit data with plain T-SQL (see the example below). File targets keep the audit trail machine-readable without a parsing script:",
))

R.append((
    "Many organizations ship PostgreSQL CSV logs to Elasticsearch or Splunk via Filebeat or Logstash. SQL Server shops frequently forward audit records to Azure Monitor or a centralized SQL table using scheduled jobs.",
    "Many organizations forward audit records to Azure Monitor, Elasticsearch, or Splunk, or load them into a centralized SQL table using scheduled jobs that call " + code('sys.fn_get_audit_file') + ".",
))

R.append((
    "In PostgreSQL, the performance cost of pgaudit is primarily I/O",
    "In SQL Server, the performance cost of auditing is primarily I/O",
))

R.append((
    "Another technique in PostgreSQL is using trigger-based auditing for high-value DML rather than relying on pgaudit's session-level write class.",
    "Another technique is using trigger-based auditing for high-value DML rather than relying on the audit's statement-level capture.",
))

R.append((
    "The " + code('SECURITY DEFINER') + " clause means the function executes with the permissions of its owner (typically a privileged DBA account), not the session user.",
    "Use " + code('EXECUTE AS OWNER') + " on the trigger so it executes with the permissions of its owner (typically a privileged DBA account), not the session user.",
))

R.append((
    "In PostgreSQL, protect audit integrity through several layers. First, ensure the PostgreSQL server process does not own the log directory with write-modify-delete access for any other OS user. Second, restrict who can reconfigure " + code('pgaudit') + " settings",
    "In SQL Server, protect audit integrity through several layers. First, write audit files to a directory where the SQL Server service account is the only writer. Second, restrict who can reconfigure the audit: " + code('ALTER ANY SERVER AUDIT') + " is a sysadmin-equivalent power, so managing sysadmin membership tightly is directly related to audit integrity. Third, restrict who can reconfigure audit settings",
))

R.append((
    "PostgreSQL auditing is built on `pgaudit` for structured session and object-level logging, optionally supplemented by trigger-based audit tables that capture old and new row values directly to a queryable schema.",
    "SQL Server auditing is built on SQL Server Audit for structured server- and database-level logging, optionally supplemented by trigger-based audit tables that capture old and new row values directly to a queryable schema.",
))

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(R):
        count = text.count(old)
        if count != 1:
            print('FAIL replacement %d: found %d occurrences' % (i, count))
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print('ch38: all %d replacements applied' % len(R))

main()
