#!/usr/bin/env python3
"""Apply ch15 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch15-automation.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

AGENT_SUBSECTION = """<p class="text-gray-300 leading-relaxed"><strong class="text-white">SQL Server Agent: The Built-in Scheduler</strong></p>

<p class="text-gray-300 leading-relaxed">SQL Server Agent is the built-in job scheduling framework — jobs, steps, schedules, alerts, and operators, all stored in msdb and manageable from SSMS or T-SQL. A job is a sequence of steps (T-SQL, PowerShell, SSIS, CmdExec); each step runs as a proxy account or the Agent service account, with success/failure flow control between steps. Schedules are first-class objects you attach to jobs, and alerts can fire jobs in response to errors, performance conditions, or WMI events.</p>

<p class="text-gray-300 leading-relaxed">Three Agent disciplines separate reliable shops from the rest. First, <strong class="text-white">job ownership</strong>: jobs owned by a personal login break when that login is disabled or leaves — own every production job with a dedicated service account. Second, <strong class="text-white">failure notification</strong>: a job that fails silently is worse than no job; configure operators, alert on every failure, and monitor %s for jobs that haven't run when they should have. Third, <strong class="text-white">idempotency</strong>: maintenance jobs must be safe to re-run. The adaptive pattern in the example below — only rebuilding what's actually fragmented — is idempotent by construction, while fixed-scope scripts are not.</p>
""" % code('msdb.dbo.sysjobhistory')

REPLACEMENTS = [
# 1 intro
("""Both PostgreSQL and SQL Server offer native scheduling and scripting capabilities, and this chapter walks through both ecosystems in depth, from writing your first scheduled job to building fully automated operational pipelines that require minimal human intervention.""",
 """SQL Server offers native scheduling through SQL Server Agent plus PowerShell and dbatools scripting, and this chapter walks through that ecosystem in depth, from writing your first scheduled job to building fully automated operational pipelines that require minimal human intervention."""),

# 2 VACUUM anecdote
("""A VACUUM that should have happened at 2 AM did not happen because the DBA was on vacation and no one else knew about the script sitting in a home directory.""",
 """An index rebuild that should have happened at 2 AM did not happen because the DBA was on vacation and no one else knew about the script sitting in a home directory."""),

# 3 ecosystem paragraph
("""Both PostgreSQL and SQL Server have matured significantly in this area. PostgreSQL relies on cron-based scheduling at the OS level, the %s extension for database-native scheduling, and scripting in Bash or Python. SQL Server has SQL Server Agent, which provides a full job scheduling framework inside the engine. Each approach has trade-offs, and experienced DBAs often combine native tools with external orchestration depending on the scale of the environment.""" % code('pg_cron'),
 """SQL Server's automation stack centers on SQL Server Agent — a full job scheduling framework inside the engine — plus PowerShell and the dbatools module for scripting, with external orchestration (Azure DevOps, Jenkins, Kubernetes CronJobs) layered on for deployment pipelines. Experienced DBAs combine Agent jobs for database-local maintenance with external orchestration for cross-system workflows."""),

# 8 OS cron pattern
("""For PostgreSQL environments using OS cron, the pattern is typically a shell script that calls %s. The script can include logic to decide what maintenance to run based on bloat queries, making it equally adaptive.""" % code('psql'),
 """For environments where Agent isn't available — or for cross-instance orchestration — the pattern is a PowerShell/dbatools script run from Task Scheduler or a pipeline: it can query fragmentation and job health across dozens of instances and invoke maintenance remotely, making it equally adaptive at fleet scale."""),

# 9 REINDEX/pg_cron subtlety
("""One subtlety to keep in mind: in PostgreSQL, %s cannot run inside a transaction block, which means it cannot simply be wrapped in %s's default execution model the same way an ordinary statement can. %s is a separate extension with its own release history independent of the PostgreSQL server version, and its handling of commands that cannot run inside a transaction block has evolved over its releases — check the %s changelog for the version you have installed rather than assuming behavior based on your PostgreSQL server version.""" % (code('REINDEX CONCURRENTLY'), code('pg_cron'), code('pg_cron'), code('pg_cron')),
 """One subtlety to keep in mind: %s index rebuilds require Enterprise edition, so a maintenance job that assumes %s will fail on Standard — parameterize the edition check (%s) and degrade gracefully to offline rebuilds inside the window. Similarly, always test maintenance procedures as the Agent service account, not as sysadmin in SSMS: permission and context differences between your session and the job's runtime are the classic "works for me" failure.""" % (code('ONLINE'), code('ONLINE = ON'), code("SERVERPROPERTY('EngineEdition')"))),

# 10 health checks
("""A health check script typically checks a set of known indicators: connection pool saturation, replication lag, long-running queries, lock waits, tablespace usage, and autovacuum activity.""",
 """A health check script typically checks a set of known indicators: connection pool saturation, AG replication lag, long-running queries, lock waits, filegroup usage, and Agent job health."""),

# 11 online schema changes
("""For PostgreSQL, online schema changes require additional care. Adding a column with a default in PostgreSQL versions before 11 locked the table for the entire duration of the rewrite. Since PostgreSQL 11, adding a column with a non-volatile default is instant because the default is stored in metadata rather than written to every row. For index creation, %s should be the default in production because it builds the index without holding a lock that blocks writes.""" % code('CREATE INDEX CONCURRENTLY'),
 """For SQL Server, online schema changes center on %s index operations (Enterprise edition) and resumable builds for large tables — %s lets a multi-hour build pause and resume across maintenance windows instead of starting over. For table restructures, the expand-contract pattern (add the new structure, dual-write, backfill, switch reads, drop the old) keeps deployments online without exotic tooling.""" % (code('ONLINE'), code('WITH (ONLINE = ON, RESUMABLE = ON)'))),

# 12 runbook stats
("""refreshing statistics on tables that the autovacuum daemon has not analyzed recently.""",
 """refreshing statistics on tables that auto-update has not kept current."""),

# 13 K8s pg_cron
("""For PostgreSQL environments running on Kubernetes, the %s approach can be supplemented or replaced by Kubernetes CronJobs that run database maintenance scripts in containers. This gives you the full Kubernetes operational model — resource limits, restart policies, pod logs, events — applied to database maintenance. The trade-off is that the maintenance jobs are now external to the database process, which means they count toward the connection limit and must handle the case where the database is temporarily unavailable.""" % code('pg_cron'),
 """For SQL Server environments running on Kubernetes or inside CI/CD pipelines, Agent jobs can be supplemented by Kubernetes CronJobs or pipeline-scheduled containers running dbatools scripts. This gives you the full platform operational model — resource limits, restart policies, pod logs — applied to database maintenance. The trade-off is that external jobs consume connections and must handle the database being temporarily unavailable during failovers."""),

# 14 takeaway scheduling
("""PostgreSQL automation relies on a combination of OS-level cron, the `pg_cron` extension for database-native scheduling, and external scripting in Bash or Python; SQL Server provides SQL Server Agent as a built-in, feature-complete job scheduling framework.""",
 """SQL Server automation centers on SQL Server Agent as the built-in job scheduling framework, with PowerShell and dbatools for scripting and external orchestration for deployment pipelines — and every production job needs an owner that isn't a person, failure alerting, and idempotent logic."""),

# 15 takeaway adaptive
("""Adaptive maintenance — where scripts query current state (fragmentation percentages, bloat ratios, vacuum statistics) and perform only the work that is actually needed — is significantly more efficient than fixed-scope maintenance that runs unconditionally.""",
 """Adaptive maintenance — where scripts query current state (fragmentation percentages, statistics age, job history) and perform only the work that is actually needed — is significantly more efficient than fixed-scope maintenance that runs unconditionally."""),
]

def main():
    lines = open(PATH).read().split('\n')
    # Replace PG pg_cron subsection: header para + 3 paragraphs, keeping the SQL Server pre block.
    idx_head = next(i for i, l in enumerate(lines) if 'PostgreSQL: pg_cron and OS-Level Cron' in l)
    idx_pre = next(i for i, l in enumerate(lines) if l.startswith('<pre class=') and i > idx_head)
    lines = lines[:idx_head] + [AGENT_SUBSECTION] + lines[idx_pre:]
    text = '\n'.join(lines)
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch15: subsection replaced + all {len(REPLACEMENTS)} replacements applied')

main()
