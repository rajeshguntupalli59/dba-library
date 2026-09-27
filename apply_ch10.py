#!/usr/bin/env python3
"""Apply ch10 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch10-backup.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter covers how PostgreSQL and SQL Server approach backup and recovery, the practical mechanics of each method, how to choose the right strategy for your environment, and what production DBAs learn the hard way about backup systems that look fine until the moment they need to work.""",
 """This chapter covers how SQL Server approaches backup and recovery, the practical mechanics of each method, how to choose the right strategy for your environment, and what production DBAs learn the hard way about backup systems that look fine until the moment they need to work."""),

# 2 backup types intro
("""Both PostgreSQL and SQL Server support multiple backup types that differ in what they capture and how long they take to restore. Each type makes a different trade-off between backup time, storage consumption, and restore complexity.""",
 """SQL Server supports multiple backup types that differ in what they capture and how long they take to restore. Each type makes a different trade-off between backup time, storage consumption, and restore complexity."""),

# 3 differential
("""PostgreSQL does not have a native differential backup concept at the SQL level, but tools like %s implement both differential and incremental backup semantics at the file level through file-level comparisons and delta copies.""" % code('pgBackRest'),
 """SQL Server implements differential backups natively: %s captures all extents changed since the last full backup, tracked by the differential bitmap. Differentials are the middle ground — faster than a full backup, simpler to restore than a long log chain — and they're what makes weekly-full/daily-differential/hourly-log the most common production rhythm.""" % code('BACKUP DATABASE ... WITH DIFFERENTIAL')),

# 4 pg_dump/pg_basebackup guidance
("""PostgreSQL's built-in backup utility %s always produces logical backups equivalent to a full backup. File-level base backups are taken using %s, which is the foundation of physical backup strategies:""" % (code('pg_dump'), code('pg_basebackup')),
 """For small databases, migrations, and selective object restores, BACPAC exports (schema plus data, portable to Azure) and %s serve the logical-backup role. For production databases beyond a few gigabytes, native %s — full plus differential plus log — is the standard approach:""" % (code('bcp'), code('BACKUP DATABASE'))),

# 5 logical backups
("""<strong class="text-white">Logical backups</strong> export the data as SQL statements or structured data formats. In PostgreSQL, %s and %s produce logical backups. In SQL Server, logical backups are sometimes produced through BACPAC exports for Azure migration or through BCP utilities for bulk data.""" % (code('pg_dump'), code('pg_dumpall')),
 """<strong class="text-white">Logical backups</strong> export the data as SQL statements or structured data formats. In SQL Server, logical backups are produced through BACPAC exports for Azure migration or through BCP utilities for bulk data movement."""),

# 6 physical backups
("""<strong class="text-white">Physical backups</strong> copy the actual data files at the storage level. In PostgreSQL, this means copying the data directory files along with the Write-Ahead Log (WAL) segments required to make that copy consistent. In SQL Server, %s always produces a physical backup — it reads data pages directly and writes them to the backup file. Physical backups are faster to create and restore for large databases, but they are less flexible. A physical backup from PostgreSQL 15 cannot be directly restored into PostgreSQL 14. A physical backup taken on Windows cannot be simply moved to Linux.""" % code('BACKUP DATABASE'),
 """<strong class="text-white">Physical backups</strong> copy the actual data files at the storage level. In SQL Server, %s always produces a physical backup — it reads data pages directly and writes them to the backup file. Physical backups are faster to create and restore for large databases, but they are less flexible: a backup from a newer SQL Server version cannot be restored to an older one (there is no downward compatibility), so version upgrades need a tested restore path, not just a backup file.""" % code('BACKUP DATABASE')),

# 7 pg_dump guidance
("""For PostgreSQL, %s remains the right choice for small databases, migrations, schema transfers, and selective table restores. For production databases beyond a few gigabytes, physical backup with %s or %s is the standard approach.""" % (code('pg_dump'), code('pg_basebackup'), code('pgBackRest')),
 """BACPAC and %s remain the right choice for small databases, migrations, schema transfers, and selective table restores. For production databases beyond a few gigabytes, native full plus differential plus log backup is the standard approach.""" % code('bcp')),

# 8 WAL -> transaction log
("""In PostgreSQL, the equivalent mechanism is <strong class="text-white">Write-Ahead Logging (WAL)</strong>. PostgreSQL always writes changes to WAL before applying them to data files. For point-in-time recovery (PITR), you archive WAL segments as they are completed and pair them with a base backup. When restoring, you restore the base backup and then replay WAL segments up to your target recovery point.""",
 """In SQL Server, the equivalent mechanism is the <strong class="text-white">transaction log</strong>. SQL Server always writes changes to the log before applying them to data files (write-ahead logging). For point-in-time recovery, you take log backups capturing the log records since the last log backup, paired with a full (and optionally differential) base. When restoring, you restore the full, then differentials, then replay log backups in sequence up to your target recovery point with %s.""" % code('STOPAT')),

# 9 WAL archiving config -> log backup config
("""WAL archiving is configured in %s:""" % code('postgresql.conf'),
 """Log backups require the %s recovery model — in %s, log backups are impossible and point-in-time recovery doesn't exist. The standard setup:""" % (code('FULL'), code('SIMPLE'))),

# 11 archive_command -> log chain
("""The %s is the shell command PostgreSQL executes to copy each completed WAL segment to your archive location. It must return exit code 0 only on success; a failed archive command will stall WAL recycling and eventually halt the database if %s fills up. This is why monitoring the archive success rate is non-negotiable.""" % (code('archive_command'), code('max_wal_size')),
 """A failed log backup breaks the log chain: every subsequent log backup is useless for a continuous recovery sequence until a new full or differential base is taken. This is why monitoring log backup success — and the %s column in %s — is non-negotiable. If the log can't be truncated because backups are failing, the log file grows until the disk fills, and then everything stops.""" % (code('log_reuse_wait_desc'), code('sys.databases'))),

# 12 recovery_target_time -> STOPAT/marked transactions
("""For point-in-time recovery in PostgreSQL, the %s parameter in %s (PostgreSQL 11 and earlier) or %s (PostgreSQL 12+) tells the recovery process where to stop replaying WAL. You can also target a specific transaction ID with %s, or a named restore point created with %s.""" % (code('recovery_target_time'), code('recovery.conf'), code('postgresql.conf'), code('recovery_target_xid'), code('pg_create_restore_point()')),
 """For point-in-time recovery, the %s clause on %s tells the recovery process where to stop replaying the log. You can also stop at a marked transaction — %s — which creates a named recovery point in the log, ideal for stopping just before a known-bad deployment.""" % (code('STOPAT'), code('RESTORE LOG'), code('BEGIN TRANSACTION ... WITH MARK'))),

# 13 compression
("""Backup compression deserves deliberate attention. SQL Server's %s option typically reduces backup size by 60–70%% for typical OLTP data, with modest CPU overhead that is usually well worth the storage and I/O savings. PostgreSQL's %s supports gzip and lz4 compression. %s supports zstd, which achieves better compression ratios than gzip at faster speeds and is the recommended choice for modern PostgreSQL backup infrastructure.""" % (code('WITH COMPRESSION'), code('pg_basebackup'), code('pgBackRest')),
 """Backup compression deserves deliberate attention. SQL Server's %s option typically reduces backup size by 60–70%% for typical OLTP data, with modest CPU overhead that is usually well worth the storage and I/O savings. Enable it by default at the server level (%s) — there is rarely a reason not to.""" % (code('WITH COMPRESSION'), code("sp_configure 'backup compression default', 1"))),

# 14 amcheck -> CHECKDB
("""The %s extension in PostgreSQL verifies B-tree index structural integrity. Running it after a restore confirms that the backup did not contain silently corrupted index pages. For heap data, %s checks and %s can surface corruption that would otherwise remain hidden.""" % (code('amcheck'), code('pg_catalog'), code('VACUUM VERBOSE')),
 """%s verifies database structural integrity — run it regularly in production and always after a restore to confirm the backup didn't contain silently corrupted pages. For very large databases where a full %s is too heavy for the maintenance window, %s catches most hardware-level corruption cheaply; just don't let it become a permanent substitute.""" % (code('DBCC CHECKDB'), code('DBCC CHECKDB'), code('PHYSICAL_ONLY'))),

# 15 partial restores
(""" In PostgreSQL, %s allows restoring individual tables from a directory-format dump, which can recover an accidentally dropped table without restoring the entire database.""" % code('pg_restore'),
 """ For an accidentally dropped table, the standard SQL Server recovery pattern is restoring to a second instance — or a point-in-time copy — and copying the table across, which avoids taking the production database offline for a full restore."""),

# 16 takeaway logical/physical
("""**Logical and physical backups serve different purposes.** Physical backups (`pg_basebackup`, SQL Server `BACKUP DATABASE`) are fast and suitable for disaster recovery at scale. Logical backups (`pg_dump`, selective exports) are portable and suitable for migrations, schema transfers, and partial object recovery. Production environments should use both.""",
 """**Logical and physical backups serve different purposes.** Physical backups (SQL Server `BACKUP DATABASE`) are fast and suitable for disaster recovery at scale. Logical backups (BACPAC, `bcp` selective exports) are portable and suitable for migrations, schema transfers, and partial object recovery. Production environments should use both."""),

# 17 takeaway log management
("""**Transaction log management is what enables point-in-time recovery.** In SQL Server, the `FULL` recovery model with regular log backups is required. In PostgreSQL, WAL archiving must be configured, monitored, and verified. Without functioning log backups, your recovery capability is limited to your last full or differential backup.""",
 """**Transaction log management is what enables point-in-time recovery.** In SQL Server, the `FULL` recovery model with regular log backups is required — and a broken log chain means your recovery capability silently degrades to your last full or differential backup. Monitor backup success, not just backup existence."""),
]

CODE_OLD = """wal_level = replica
archive_mode = on
archive_command = 'cp %p /mnt/wal_archive/%f'
restore_command = 'cp /mnt/wal_archive/%f %p'"""
CODE_NEW = """-- Full recovery model is required for log backups
ALTER DATABASE OrdersDB SET RECOVERY FULL;
-- Log backup every 15 minutes (SQL Server Agent job)
BACKUP LOG OrdersDB
  TO DISK = 'D:\\Backups\\OrdersDB_log.trn' WITH COMPRESSION;
-- Point-in-time restore to just before the accident
RESTORE LOG OrdersDB FROM DISK = 'D:\\Backups\\OrdersDB_log.trn'
  WITH STOPAT = '2026-09-26T14:32:00', RECOVERY;"""

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    if text.count(CODE_OLD) != 1:
        print('FAIL code block: found %d occurrences' % text.count(CODE_OLD))
        sys.exit(1)
    text = text.replace(CODE_OLD, CODE_NEW, 1)
    open(PATH, 'w').write(text)
    print(f'ch10: all {len(REPLACEMENTS)} prose + 1 code-block replacements applied')

main()
