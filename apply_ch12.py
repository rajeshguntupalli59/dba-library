#!/usr/bin/env python3
"""Apply ch12 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch12-disaster-recovery.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

RECOVERY_MODELS_SECTION = """<p class="text-gray-300 leading-relaxed">#### Recovery Models: The Choice That Gates Everything</p>

<p class="text-gray-300 leading-relaxed">Before any restore sequence works, the database's recovery model must allow it. <strong class="text-white">SIMPLE</strong> truncates the log on checkpoint — no log backups, no point-in-time recovery; your RPO equals your last full or differential backup. <strong class="text-white">FULL</strong> keeps log records until a log backup truncates them — this is what makes point-in-time recovery possible, and it's the only honest choice for production data you can't afford to lose. <strong class="text-white">BULK_LOGGED</strong> is the middle ground: minimally logged bulk operations (%s, %s, index rebuilds) don't bloat the log, but you lose point-in-time recovery across the bulk window — you can only restore to the end of a log backup containing bulk-logged changes, not to a moment inside it.</p>

<p class="text-gray-300 leading-relaxed">The classic production mistake is a database in FULL recovery model with no log backup job — the log grows until the disk fills, and the application stops. Check %s for %s: a value of %s means exactly this. Conversely, a database accidentally left in SIMPLE after a migration silently discards your RPO. Audit recovery models as part of every deployment checklist and every restore validation.</p>

<p class="text-gray-300 leading-relaxed">Switching from SIMPLE to FULL doesn't retroactively create recoverability — you need a full backup after the switch to start the log chain. Until that base exists, log backup attempts will fail. This bites during incident response: someone switches to FULL, schedules log backups, and discovers at restore time that the chain was never valid.</p>
""" % (code('BULK INSERT'), code('SELECT INTO'), code('sys.databases'), code('log_reuse_wait_desc'), code('LOG_BACKUP'))

LOG_SHIPPING_SECTION = """<p class="text-gray-300 leading-relaxed">#### Log Shipping: The Simple DR Standby</p>

<p class="text-gray-300 leading-relaxed">Log shipping is SQL Server's simplest DR standby technology: a SQL Server Agent job takes transaction-log backups on the primary, copies them to the standby server, and another job restores them on a schedule — with %s (read-only between restores) or %s. There's no automatic failover; on disaster you manually bring the standby online with %s and redirect applications. RPO equals your shipping interval (typically 15 minutes); RTO is measured in minutes of manual work.</p>

<p class="text-gray-300 leading-relaxed">What log shipping buys you over "just backups" is automation and currency: the standby stays within one interval of the primary without anyone remembering to copy files. It needs no WSFC, works across domains, and runs on Standard Edition — which makes it the pragmatic DR choice for a cross-region standby where an AG's continuous transport isn't justified. Monitor it through the log shipping status tables (%s); an unmonitored shipper is just a backup job with extra steps.</p>

<p class="text-gray-300 leading-relaxed">The operational discipline that matters: test the manual failover. Log shipping failovers are rare enough that the runbook rots — server names change, copy-share permissions drift, the standby's SQL version falls behind. A quarterly rehearsal (bring the standby online on an isolated network, verify the data, throw it away) is what makes log shipping a DR strategy instead of a DR hope.</p>
""" % (code('STANDBY'), code('NORECOVERY'), code('RESTORE ... WITH RECOVERY'), code('msdb.dbo.log_shipping_monitor_primary/secondary'))

VERIFY_BLOCK = """<p class="text-gray-300 leading-relaxed"><strong class="text-white">SQL Server — verify after failover:</strong></p>

<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>-- Confirm the new primary is writable and replicas are healthy
SELECT DATABASEPROPERTYEX('OrdersDB', 'Updateability');  -- should return READ_WRITE
SELECT replica_server_name, role_desc, synchronization_state_desc
FROM sys.dm_hadr_availability_replica_states;</code></pre>
"""

REPLACEMENTS = [
# 1 intro
("""Both PostgreSQL and SQL Server have mature, battle-tested tools for this work, and understanding both systems side by side gives you the mental model to design and defend recovery strategies across any environment.""",
 """SQL Server has mature, battle-tested tools for this work, and this chapter gives you the mental model to design and defend recovery strategies in any SQL Server environment."""),

# 2 backup tools
("""In PostgreSQL, %s is the primary logical backup tool, while %s is the physical backup tool. In SQL Server, native backups (%s) are physical, and %s, SSIS, or %s exports are logical equivalents.""" % (code('pg_dump'), code('pg_basebackup'), code('BACKUP DATABASE'), code('bcp'), code('BACPAC')),
 """In SQL Server, native backups (%s) are physical, and %s, SSIS, or %s exports are the logical equivalents for migrations and selective object recovery.""" % (code('BACKUP DATABASE'), code('bcp'), code('BACPAC'))),

# 3 differential/incremental
("""<strong class="text-white">Differential backups</strong> (SQL Server) capture all changes since the last full backup. They grow over time and are faster to restore than a long chain of incremental backups. <strong class="text-white">Incremental backups</strong> (PostgreSQL WAL-based, using tools like pgBackRest or Barman) capture only changes since the last incremental or full backup, minimizing storage but requiring the full chain during restore.""",
 """<strong class="text-white">Differential backups</strong> capture all changes since the last full backup, tracked by the differential bitmap. They grow over time and are faster to restore than a long chain of log backups. <strong class="text-white">Log backups</strong> capture only changes since the last log backup, minimizing backup size and RPO but requiring the full chain during restore — which is why the most common production rhythm is weekly full, daily differential, frequent log."""),

# 4 PITR mechanism
("""By continuously capturing transaction logs (PostgreSQL: WAL segments; SQL Server: transaction log backups), you can restore a database to any specific moment between backup events.""",
 """By continuously capturing transaction log backups, you can restore a database to any specific moment between backup events."""),

# 27 pgBackRest verify -> VERIFYONLY + test restores
("""For PostgreSQL, pgBackRest has a built-in verification command (%s) that checks backup integrity, confirms WAL segments are in place, and validates that a restore chain is complete. If you use pg_basebackup directly without a tool like pgBackRest or Barman, you need to periodically test restores manually.""" % code('pgbackrest verify'),
 """%s validates that a backup file is readable and its header is intact — but it does not validate the data inside. True verification means test restores: restore the backup to an isolated instance and run %s. Automate this on a schedule; an untested backup is a hope, not a recovery strategy.""" % (code('RESTORE VERIFYONLY'), code('DBCC CHECKDB'))),

# 28 amcheck -> CHECKDB
("""PostgreSQL does not have a built-in equivalent to %s for running storage-level checks while online. The closest approach combines %s (which reads every page and will fail on corruption) with %s extension for index validation.""" % (code('DBCC CHECKDB'), code('pg_dump'), code('amcheck')),
 """%s is SQL Server's storage-level integrity check — run it on a schedule in production and always after a restore. For very large databases, %s catches hardware-level corruption cheaply between full checks.""" % (code('DBCC CHECKDB'), code('PHYSICAL_ONLY'))),

# 30 runbook
("""the actual %s or %s invocation, with the real file paths and server names for that environment, is.""" % (code('RESTORE DATABASE'), code('pg_basebackup')),
 """the actual %s invocation, with the real file paths and server names for that environment, is.""" % code('RESTORE DATABASE')),

# 31 takeaway backups
("""**Physical and logical backups solve different problems and most production environments need both.** Physical backups (`pg_basebackup`, SQL Server native `BACKUP DATABASE`) are fast and support point-in-time recovery; logical backups (`pg_dump`, BACPAC) are portable and support selective, table-level restores.""",
 """**Physical and logical backups solve different problems and most production environments need both.** Physical backups (SQL Server native `BACKUP DATABASE`) are fast and support point-in-time recovery; logical backups (BACPAC, `bcp`) are portable and support selective, table-level restores."""),

# 32 takeaway PITR
("""**Point-in-time recovery is the mechanism behind "restore to right before the mistake happened."** PostgreSQL achieves it through WAL replay to a target time or LSN; SQL Server achieves it through a full/differential restore followed by ordered log restores with `STOPAT` — and in SQL Server, a tail-log backup taken before the restore sequence begins can reduce data loss to zero even in an unplanned incident.""",
 """**Point-in-time recovery is the mechanism behind "restore to right before the mistake happened."** SQL Server achieves it through a full/differential restore followed by ordered log restores with `STOPAT` — and a tail-log backup taken before the restore sequence begins can reduce data loss to zero even in an unplanned incident."""),
]

def main():
    lines = open(PATH).read().split('\n')
    # 1. Replace PG PITR section (lines 146-168, 1-indexed) with recovery-models section.
    assert '#### PostgreSQL PITR' in lines[145], lines[145][:80]
    assert '#### SQL Server PITR' in lines[169], lines[169][:80]
    lines = lines[:145] + [RECOVERY_MODELS_SECTION] + lines[169:]
    # 2. Replace PG streaming replication section with log shipping section.
    idx_pg = next(i for i, l in enumerate(lines) if '#### PostgreSQL Streaming Replication' in l)
    idx_ag = next(i for i, l in enumerate(lines) if '#### SQL Server Always On Availability Groups' in l)
    assert idx_ag > idx_pg
    lines = lines[:idx_pg] + [LOG_SHIPPING_SECTION] + lines[idx_ag:]
    # 3. Replace PG promote header + 2 code blocks with SQL Server verification block.
    text = '\n'.join(lines)
    pg_header = '<strong class="text-white">PostgreSQL — promote a standby:</strong>'
    sql_header = '<strong class="text-white">SQL Server — manual failover of an AG:</strong>'
    i1 = text.find(pg_header)
    i2 = text.find(sql_header)
    assert i1 != -1 and i2 != -1 and i2 > i1
    # find start of the <p> containing pg_header
    pstart = text.rfind('<p class="text-gray-300 leading-relaxed">', 0, i1)
    text = text[:pstart] + VERIFY_BLOCK + '\n' + text[i2 - len('<p class="text-gray-300 leading-relaxed">'):]
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch12: 3 sections replaced + all {len(REPLACEMENTS)} replacements applied')

main()
