#!/usr/bin/env python3
"""Apply ch18 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch18-logging.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
PRE = '<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>'
H3 = '<h3 class="text-lg font-semibold text-white mt-8 mb-3">%s</h3>'

LOGGING_SECTION = H3 % "Configuring SQL Server Logging: Error Log and Extended Events" + "\n\n" + \
P + "The <strong class=\"text-white\">SQL Server Error Log</strong> is the operational journal of the instance: startup and shutdown, backup and restore completions, DBCC results, login failures, corruption alerts, AG role changes. Read it with " + code('sp_readerrorlog') + " (or SSMS → Management → SQL Server Logs), and cycle it weekly with " + code('sp_cycle_errorlog') + " via an Agent job — SQL Server keeps only a fixed number of archives, and an unrotated log becomes an unsearchable multi-gigabyte file.</p>\n\n" + \
P + "What the Error Log won't do is tell you about slow queries — that responsibility falls to <strong class=\"text-white\">Extended Events</strong> and Query Store. Extended Events (XEvents) is the lightweight, high-performance tracing framework that replaced Profiler and server-side Trace. You define a session with events, attach actions and predicates, point it at a target, and start it. A canonical slow-query session captures batches over a duration threshold to an event file — near-zero overhead for everything faster, because the predicate filters before the target writes:</p>\n\n" + \
PRE + """CREATE EVENT SESSION SlowQueries ON SERVER
ADD EVENT sqlserver.sql_batch_completed(
    ACTION(sqlserver.sql_text, sqlserver.client_app_name, sqlserver.username)
    WHERE duration > 1000000)  -- microseconds: 1 second
ADD TARGET package0.event_file(
    SET filename = N'C:\\XEvents\\SlowQueries.xel');
ALTER EVENT SESSION SlowQueries ON SERVER STATE = START;</code></pre>\n\n""" + \
P + "Query the file with " + code('sys.fn_xe_file_target_read_file') + ", or watch live with SSMS's XEvent Profiler for ad-hoc diagnosis. Two rules that prevent self-inflicted wounds: never run Profiler or server-side Trace on production — the overhead can cripple a busy system — and always put a predicate on high-frequency events. An unfiltered " + code('sql_batch_completed') + " session on an OLTP system will write gigabytes per hour.</p>"

AUDIT_PRACTICE = P + "<strong class=\"text-white\">SQL Server Audit in Practice</strong></p>\n\n" + \
P + "The three-layer model (Server Audit → Server/Database Audit Specification) is only half the story; the operational half is what happens around it. First, choose the failure mode deliberately: " + code('ON_FAILURE = CONTINUE') + " lets the server run unaudited when the audit target is unavailable, while " + code('SHUTDOWN') + " stops the instance instead. For compliance-bound systems, SHUTDOWN is the honest choice; for everything else, CONTINUE plus alerting on audit failures. Second, auditors will ask for 'every SELECT against customer_payments in March' — the answer is a query against the audit files with " + code('sys.fn_get_audit_file') + ", not a grep:</p>\n\n" + \
PRE + """-- Who touched the payments table last Tuesday
SELECT event_time, server_principal_name, statement
FROM sys.fn_get_audit_file('D:\\Audit\\ComplianceAudit*.sqlaudit', NULL, NULL)
WHERE object_name = 'customer_payments'
  AND event_time >= '2026-09-22' AND event_time < '2026-09-23';</code></pre>\n\n""" + \
P + "Third, be surgical with database audit specifications. Auditing every SELECT on every table of a busy OLTP database costs measurable throughput and generates unmanageable volume. Audit the sensitive objects, the privileged actions (DDL, role changes), and the logins that matter — and document why each specification exists, because the next auditor will ask. Finally, put audit files on a dedicated volume with a retention job that archives and purges: SQL Server never deletes audit files on its own.</p>"

LOGIN_DEEPENING = P + "<strong class=\"text-white\">Login Auditing Beyond the Audit Spec</strong></p>\n\n" + \
P + "The cheapest login auditing needs no Audit object at all: the server's login-auditing level (SSMS → Server Properties → Security) controls what lands in the Error Log — failed logins only (the production default, and usually the right one), successful logins, or both. Failed logins in the Error Log are your brute-force and misconfigured-application signal; alert on their rate, not just their presence. Successful-login logging at the server level is voluminous — prefer the targeted " + code('SUCCESSFUL_LOGIN_GROUP') + " in a Server Audit Specification (above) when compliance requires it.</p>\n\n" + \
P + "Privilege escalation deserves its own attention, because it is the audit event auditors actually ask about: who became sysadmin, and when. " + code('SERVER_ROLE_MEMBER_CHANGE_GROUP') + " and " + code('DATABASE_ROLE_MEMBER_CHANGE_GROUP') + " (in the specification above) capture exactly that. Pair the audit with an alert — a job that scans the audit file for role-membership changes and pages — because an audit record nobody reads is just disk usage.</p>"

REPLACEMENTS = [
# intro
("""This chapter covers how PostgreSQL and SQL Server each approach logging and auditing, from the raw mechanics of writing log entries to building robust audit trails that satisfy regulatory requirements.""",
 """This chapter covers how SQL Server approaches logging and auditing, from the raw mechanics of the Error Log and Extended Events to building robust audit trails that satisfy regulatory requirements."""),
("""By the end, you will know how to configure both systems to capture exactly what you need, interpret what you find, and avoid the common pitfalls that leave DBAs without the evidence they need when it matters most.""",
 """By the end, you will know how to configure SQL Server to capture exactly what you need, interpret what you find, and avoid the common pitfalls that leave DBAs without the evidence they need when it matters most."""),

# layers
("""Both PostgreSQL and SQL Server generate logs at multiple layers.""",
 """SQL Server generates logs at multiple layers."""),
("""There is the transaction log (WAL in PostgreSQL, the LDF file in SQL Server), which is a durability mechanism and not a readable audit trail.""",
 """There is the transaction log (the LDF file), which is a durability mechanism and not a readable audit trail."""),

# error log framing
("""SQL Server's equivalent of PostgreSQL's operational log is the <strong class="text-white">SQL Server Error Log</strong>. It is written to a flat text file by default and captures server startup events, backup completions, login failures, database corruption alerts, and various informational messages. Unlike PostgreSQL's configurable log verbosity, the Error Log is less flexible — you cannot easily tell it to log slow queries there. That responsibility falls to other mechanisms.""",
 """The <strong class="text-white">SQL Server Error Log</strong> is written to a flat text file by default and captures server startup events, backup completions, login failures, database corruption alerts, and various informational messages. It is not very flexible — you cannot tell it to log slow queries. That responsibility falls to Extended Events and Query Store, covered in the previous section."""),

# h3 audit
("""Building Audit Trails: pgAudit and SQL Server Audit""",
 """Building Audit Trails with SQL Server Audit"""),

# maintenance
("""Logging infrastructure that is not maintained eventually becomes a liability. Logs that fill up disk cause PostgreSQL to crash or SQL Server to stop auditing (depending on your %s setting).""" % code('ON_FAILURE'),
 """Logging infrastructure that is not maintained eventually becomes a liability. Logs that fill up disk cause SQL Server to stop auditing — or stop the instance entirely — depending on your %s setting (%s vs %s).""" % (code('ON_FAILURE'), code('CONTINUE'), code('SHUTDOWN'))),

# rotation
("""<strong class="text-white">Rotation and retention</strong> policies should be written down and automated. For PostgreSQL, %s and %s handle file rotation. Deletion of old log files needs an external process — a cron job or a log management tool. A common pattern is retaining 90 days of operational logs locally and shipping to cold storage (S3, Azure Blob) for long-term compliance retention.""" % (code('log_rotation_age'), code('log_rotation_size')),
 """<strong class="text-white">Rotation and retention</strong> policies should be written down and automated. For the Error Log, %s on a weekly Agent schedule keeps the archives searchable (SQL Server retains only a fixed number). Audit files and XEvent targets need their own retention job — SQL Server never deletes them automatically. A common pattern is retaining 90 days of operational logs locally and shipping to cold storage (Azure Blob, S3) for long-term compliance retention.""" % code('sp_cycle_errorlog')),

# performance
("""For PostgreSQL, %s has essentially no overhead when queries complete faster than the threshold, because the decision is made post-execution. Logging itself is asynchronous through the logging collector process. The real performance risk is %s or very aggressive pgAudit settings on a write-heavy OLTP system — benchmark before enabling in production.""" % (code('log_min_duration_statement'), code("log_statement = 'all'")),
 """An Extended Events session with a duration predicate has essentially no overhead for queries faster than the threshold, because the predicate filters before the target writes. The real performance risk is capturing every statement — an unfiltered XEvent session or a broad Audit specification on a write-heavy OLTP system — benchmark before enabling in production, and prefer targeted predicates over catch-all capture."""),

# takeaway
("""**PostgreSQL's logging is highly configurable through `postgresql.conf`.** `log_min_duration_statement`, `log_connections`, `log_lock_waits`, and `log_statement = 'ddl'` form a solid production baseline. The `pgaudit` extension adds structured, compliance-grade audit output when statement-level logging is insufficient.""",
 """**Operational logging centers on the Error Log, Extended Events, and Query Store.** Cycle the Error Log on a schedule, trace with predicate-filtered XEvent sessions (never Profiler on production), and let Query Store keep the slow-query history. SQL Server Audit adds structured, compliance-grade audit output — with a deliberate `ON_FAILURE` mode and a retention job, because neither is optional."""),
]

def main():
    lines = open(PATH).read().split('\n')
    # 1. Replace PG logging section (lines 61-93, 1-based) with SQL Server section.
    h3_pg = next(i for i, l in enumerate(lines) if 'Configuring the PostgreSQL Logging System' in l)
    h3_next = next(i for i, l in enumerate(lines) if 'Configuring SQL Server Logging and the Error Log' in l)
    lines = lines[:h3_pg] + [LOGGING_SECTION, ''] + lines[h3_next:]
    # 2. Replace pgAudit subsection (header para through para before 'SQL Server: SQL Server Audit').
    text = '\n'.join(lines)
    idx_a = text.index('<strong class="text-white">PostgreSQL: pgAudit</strong>')
    idx_b = text.index('<strong class="text-white">SQL Server: SQL Server Audit</strong>')
    start = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_a)
    end = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_b)
    text = text[:start] + AUDIT_PRACTICE + '\n\n' + text[end:]
    # 3. Replace PG Login Auditing subsection (header para through content before 'SQL Server Login Auditing').
    idx_c = text.index('<strong class="text-white">PostgreSQL Login Auditing</strong>')
    idx_d = text.index('<strong class="text-white">SQL Server Login Auditing</strong>')
    start2 = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_c)
    end2 = text.rindex('<p class="text-gray-300 leading-relaxed">', 0, idx_d)
    text = text[:start2] + LOGIN_DEEPENING + '\n\n' + text[end2:]
    # 4. Prose replacements.
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch18: sections replaced + all {len(REPLACEMENTS)} replacements applied')

main()
