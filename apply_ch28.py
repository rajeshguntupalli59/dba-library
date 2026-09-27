#!/usr/bin/env python3
"""Apply ch28 rewrites: delete/replace PG docker+K8s content with SQL Server. Fails loudly."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch28-containerization.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'
PRE = '<pre class="bg-gray-900 border border-gray-800 rounded-xl p-5 text-xs text-gray-300 overflow-x-auto my-5"><code>'

CONFIG_SPAN = (
P + "SQL Server reads its configuration from environment variables and " + code('mssql.conf') + " at startup. There are three approaches to customizing them in containers.</p>\n\n" +
P + "The first approach uses environment variables, which the container honors directly — no config file needed:</p>\n\n" +
PRE + "docker run -d \\\n  --name mssql-tuned \\\n  -e ACCEPT_EULA=Y \\\n  -e MSSQL_SA_PASSWORD='<redacted>' \\\n  -e MSSQL_PID=Developer \\\n  -e MSSQL_MEMORY_LIMIT_MB=2048 \\\n  -v mssqldata:/var/opt/mssql \\\n  mcr.microsoft.com/mssql/server:2022-latest</code></pre>\n\n" +
P + "The second mounts a custom " + code('mssql.conf') + " (normally at " + code('/var/opt/mssql/mssql.conf') + " inside the container):</p>\n\n" +
PRE + "docker run -d \\\n  --name mssql-custom \\\n  -v /etc/mssql/mssql.conf:/var/opt/mssql/mssql.conf \\\n  -v mssqldata:/var/opt/mssql \\\n  mcr.microsoft.com/mssql/server:2022-latest</code></pre>\n\n" +
P + "The third bakes configuration into a derived image:</p>\n\n" +
PRE + "FROM mcr.microsoft.com/mssql/server:2022-latest\nCOPY mssql.conf /var/opt/mssql/mssql.conf</code></pre>"
)

STS_YAML = (
"apiVersion: apps/v1\nkind: StatefulSet\nmetadata:\n  name: mssql\nspec:\n  serviceName: \"mssql\"\n  replicas: 1\n  selector:\n    matchLabels:\n      app: mssql\n  template:\n    metadata:\n      labels:\n        app: mssql\n    spec:\n      containers:\n        - name: mssql\n          image: mcr.microsoft.com/mssql/server:2022-latest\n          env:\n            - name: ACCEPT_EULA\n              value: \"Y\"\n            - name: MSSQL_PID\n              value: Developer\n            - name: MSSQL_SA_PASSWORD\n              valueFrom:\n                secretKeyRef:\n                  name: mssql-secret\n                  key: sapassword\n            - name: MSSQL_MEMORY_LIMIT_MB\n              value: \"6144\"\n          ports:\n            - containerPort: 1433\n          resources:\n            requests:\n              memory: \"4Gi\"\n              cpu: \"2\"\n            limits:\n              memory: \"8Gi\"\n              cpu: \"4\"\n          volumeMounts:\n            - name: sqldata\n              mountPath: /var/opt/mssql\n  volumeClaimTemplates:\n    - metadata:\n        name: sqldata\n      spec:\n        accessModes: [\"ReadWriteOnce\"]\n        storageClassName: \"fast-ssd\"\n        resources:\n          requests:\n            storage: 100Gi"
)

PROBES = (
"livenessProbe:\n  exec:\n    command:\n      - /bin/sh\n      - -c\n      - /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" -Q \"SELECT 1\" -b\n  initialDelaySeconds: 60\n  periodSeconds: 10\n  failureThreshold: 3\nreadinessProbe:\n  exec:\n    command:\n      - /bin/sh\n      - -c\n      - /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" -Q \"SELECT 1\" -b\n  initialDelaySeconds: 10\n  periodSeconds: 5"
)

BACKUP_BLOCK = (
"-- Full backup to Azure Blob Storage, run inside the container\nBACKUP DATABASE [appdb]\nTO URL = 'https://myaccount.blob.core.windows.net/backups/appdb_full.bak'\nWITH COMPRESSION, CHECKSUM;"
)

BACKUP_BASH = (
"# Or via docker exec with sqlcmd, writing to a mounted backup volume\ndocker exec -t mssql-prod /opt/mssql-tools/bin/sqlcmd \\\n  -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" \\\n  -Q \"BACKUP DATABASE [appdb] TO DISK = '/var/opt/mssql/backup/appdb_full.bak' WITH COMPRESSION, CHECKSUM\""
)

UPGRADE_BLOCK = (
"# Major-version upgrade: stop, pull the new image, start against the same volume\ndocker stop mssql-prod\ndocker pull mcr.microsoft.com/mssql/server:2025-latest\ndocker run -d \\\n  --name mssql-prod \\\n  -e ACCEPT_EULA=Y \\\n  -e MSSQL_SA_PASSWORD=\"$MSSQL_SA_PASSWORD\" \\\n  -v mssqldata:/var/opt/mssql \\\n  -p 1433:1433 \\\n  mcr.microsoft.com/mssql/server:2025-latest\n# The engine upgrades the system databases automatically on first boot"
)

BIND_MOUNT = (
"docker run -d \\\n  --name mssql-dev \\\n  -e ACCEPT_EULA=Y \\\n  -e MSSQL_SA_PASSWORD='<redacted>' \\\n  -v /data/mssql:/var/opt/mssql \\\n  mcr.microsoft.com/mssql/server:2022-latest"
)

REPLACEMENTS = [
# intro
("""Today, containerized PostgreSQL and SQL Server instances run in production at companies of every size,""",
 """Today, containerized SQL Server instances run in production at companies of every size,"""),
("""how to run PostgreSQL and SQL Server correctly in Docker and Kubernetes,""",
 """how to run SQL Server correctly in Docker and Kubernetes,"""),
# reproducible image
("""same PostgreSQL version, same shared libraries, same locale settings.""",
 """same SQL Server build and CU, same shared libraries, same locale settings."""),
# h3
("""Running PostgreSQL and SQL Server in Docker""",
 """Running SQL Server in Docker"""),
# official image para
("""The official PostgreSQL image is maintained by the Docker community and available on Docker Hub as %s. Microsoft maintains the SQL Server image under %s. Both follow the same basic pattern: pull an image, provide environment variables for initialization, mount a volume for data persistence.""" % (code('postgres'), code('mcr.microsoft.com/mssql/server')),
 """Microsoft maintains the SQL Server image under %s. The basic pattern is: pull an image, provide environment variables for initialization (notably %s and %s), mount a volume for data persistence.""" % (code('mcr.microsoft.com/mssql/server'), code('ACCEPT_EULA'), code('MSSQL_SA_PASSWORD'))),
# volumes para
("""When you declare %s, Docker creates a volume at a path like %s on the host and mounts it into the container.""" % (code('pgdata:/var/lib/postgresql/data'), code('/var/lib/docker/volumes/pgdata/_data')),
 """When you declare %s, Docker creates a volume at a path like %s on the host and mounts it into the container.""" % (code('mssqldata:/var/opt/mssql'), code('/var/lib/docker/volumes/mssqldata/_data'))),
# RWO para
("""Two PostgreSQL instances writing to the same data directory simultaneously is not high availability — it is corruption.""",
 """Two SQL Server instances writing to the same data directory simultaneously is not high availability — it is corruption."""),
# durability
("""One configuration detail that catches teams off guard: PostgreSQL's %s and %s settings. When running inside a container, the database is relying on the storage driver and volume backend to honor %s calls faithfully. Most production storage backends do. Some cloud-managed NFS implementations have quirks. Always verify that your storage backend flushes durably on %s before disabling it for performance reasons — the result of getting that wrong is a data directory that looks intact but has corrupted pages after an unexpected shutdown.""" % (code('data_checksums'), code('fsync'), code('fsync'), code('fsync')),
 """One configuration detail that catches teams off guard: durability. SQL Server opens data files with unbuffered I/O and depends on the storage stack honoring flush (write-through / FUA) faithfully. Most production storage backends do. Some cloud-managed NFS implementations have quirks. Verify durable flush before chasing performance — the result of getting that wrong is a data directory that looks intact but has torn pages after an unexpected shutdown. Run %s after any storage-level incident; it is non-negotiable.""" % code('DBCC CHECKDB')),
# configmaps
("""ConfigMaps hold non-sensitive configuration like %s.""" % code('postgresql.conf'),
 """ConfigMaps hold non-sensitive configuration like %s.""" % code('mssql.conf')),
# memory limits
("""Memory limits require special attention. When you set """ + code('--memory=8g') + """ on a Docker container or a """ + code('resources.limits.memory') + """ in a Kubernetes pod spec, the container's memory is capped at that value. PostgreSQL's """ + code('shared_buffers') + """ should typically be set to 25% of the memory limit, not 25% of the host's total RAM. If you let PostgreSQL inherit defaults from a host with 256 GB of RAM while your container is limited to 8 GB, the configuration won't match reality, and you will encounter OOM kills. The same logic applies to SQL Server's """ + code('max server memory') + """ setting \u2014 it must be configured to stay within the container's memory limit.""",
 """Memory limits require special attention. When you set %s on a Docker container or a %s in a Kubernetes pod spec, the container's memory is capped at that value. SQL Server's %s must stay within that limit — use the %s environment variable to cap the engine directly. If you let SQL Server size itself for a 256 GB host while the container is limited to 8 GB, the configuration won't match reality and you will meet the OOM killer.""" % (code('--memory=8g'), code('resources.limits.memory'), code('max server memory'), code('MSSQL_MEMORY_LIMIT_MB'))),
# statefulset pod name
("""When a pod named %s restarts, Kubernetes ensures it gets the same PVC it had before.""" % code('postgres-0'),
 """When a pod named %s restarts, Kubernetes ensures it gets the same PVC it had before.""" % code('mssql-0')),
# figure caption
("""*Figure: A PostgreSQL StatefulSet on Kubernetes — each pod keeps a stable identity and its own dedicated PersistentVolumeClaim across restarts and rescheduling.*""",
 """*Figure: A SQL Server StatefulSet on Kubernetes — the pod keeps a stable identity and its own dedicated PersistentVolumeClaim across restarts and rescheduling.*"""),
# minimal statefulset
("""A minimal StatefulSet for PostgreSQL:""",
 """A minimal StatefulSet for SQL Server:"""),
# liveness recovery
("""PostgreSQL running crash recovery after an unexpected shutdown may take minutes to complete before accepting connections.""",
 """SQL Server running database recovery (redo/undo) after an unexpected shutdown may take minutes to complete before accepting connections."""),
# operators
("""Operators extend Kubernetes with database-specific intelligence. The CloudNativePG operator for PostgreSQL and the SQL Server Operator for Kubernetes from Microsoft both automate tasks that would otherwise require manual intervention: failover, replica provisioning, backup scheduling, configuration updates. Operators encode operational runbooks as code, which is exactly what large-scale database management needs.""",
 """Operators extend Kubernetes with database-specific intelligence, encoding operational runbooks as code. For SQL Server the operator ecosystem is thin — most production teams run StatefulSets directly, handle failover with availability groups outside Kubernetes (or accept a single instance with fast rescheduling), and automate backups and configuration with CronJobs and mounted %s files.""" % code('mssql.conf')),
# backups para
("""For PostgreSQL, %s and %s run inside the container via %s or Kubernetes %s. Alternatively, a sidecar container — a second container in the same pod sharing the same volume mount — can run backup tools continuously without interfering with the primary container.""" % (code('pg_dump'), code('pg_basebackup'), code('docker exec'), code('exec')),
 """For SQL Server, %s runs inside the container via %s or %s, writing to Azure Blob Storage or a mounted backup volume. A sidecar container — a second container in the same pod sharing the same volume mount — can run backup tooling continuously without interfering with the primary container.""" % (code('BACKUP DATABASE ... TO URL'), code('docker exec'), code('kubectl exec'))),
# pg_upgrade para
("""<strong class="text-white">Major version upgrades</strong> of containerized databases are operationally cleaner than bare-metal upgrades in one important way: you can run the old and new versions side by side with separate containers, migrate data between them, and cut over with minimal downtime. For PostgreSQL major upgrades (e.g., 15 to 16), %s is still the right tool, but running it in a container requires mounting both the old and new data directories:""" % code('pg_upgrade'),
 """<strong class="text-white">Major version upgrades</strong> of containerized SQL Server are operationally cleaner than bare-metal upgrades in one important way: you stop the old container, pull the new image, and start it against the same data volume — the engine upgrades the system databases automatically on first boot. For large fleets, run old and new side by side, replicate or restore across, and cut over:"""),
# --link para
("""The %s flag runs %s in link mode, which rewrites the data in place rather than copying it — dramatically faster for large databases.""" % (code('--link'), code('pg_upgrade')),
 """Because the upgrade happens on first boot against the existing data files, keep a tested backup from before the switch — a failed automatic upgrade you cannot roll back is worse than a slow planned one."""),
# observability
("""Prometheus with the %s sidecar collects database metrics and exposes them for scraping. Grafana dashboards built on top of those metrics give you the same visibility you'd have on bare metal. For SQL Server, the %s serves the same function.""" % (code('postgres_exporter'), code('mssql_exporter')),
 """Prometheus with the %s (or sql_exporter) sidecar collects database metrics and exposes them for scraping. Grafana dashboards built on top of those metrics give you the same visibility you'd have on bare metal.""" % code('mssql_exporter')),
# logging
("""For PostgreSQL, setting %s and %s directs logs to stdout, where Docker or Kubernetes picks them up. From there, a log aggregator like Fluentd, Loki, or CloudWatch Logs collects and indexes them. For SQL Server, the error log writes to %s by default — a volume-backed path that persists across container restarts.""" % (code("log_destination = 'stderr'"), code('logging_collector = off'), code('/var/opt/mssql/log/errorlog')),
 """SQL Server's error log writes to %s by default — a volume-backed path that persists across container restarts. Tail it through your container log driver or ship it with Fluentd, Loki, or CloudWatch Logs like any other container log stream.""" % code('/var/opt/mssql/log/errorlog')),
# takeaway memory
("""(`shared_buffers`, `work_mem`, `max server memory`)""",
 """(`max server memory` / `MSSQL_MEMORY_LIMIT_MB`)"""),
]

def del_pre(anchor):
    """Return (start, end) spanning the <pre> block containing anchor."""
    i = text.index(anchor)
    s = text.rindex('<pre', 0, i)
    e = text.index('</code></pre>', i) + len('</code></pre>')
    return s, e

def main():
    global text
    text = open(PATH).read()
    # Surgery 1: delete PG docker-run block.
    i = text.index('A minimal PostgreSQL container:')
    s = text.rindex('<p', 0, i)
    e = text.index('</code></pre>', i) + len('</code></pre>')
    text = text[:s] + text[e:]
    # Surgery 2: delete PG compose block.
    s, e = del_pre('# docker-compose.yml for PostgreSQL')
    text = text[:s] + text[e:]
    # Surgery 3: PG bind-mount block -> SQL Server bind mount.
    s, e = del_pre('-v /data/postgres:/var/lib/postgresql/data')
    text = text[:s] + PRE + BIND_MOUNT + '</code></pre>' + text[e:]
    # Surgery 4: PG config span -> SQL Server config span.
    i = text.index('There are three approaches to customizing them in containers.')
    s = text.rindex('<p', 0, i)
    j = text.index('COPY pg_hba.conf /etc/postgresql/pg_hba.conf')
    e = text.index('</code></pre>', j) + len('</code></pre>')
    text = text[:s] + CONFIG_SPAN + text[e:]
    # Surgery 5: StatefulSet YAML -> SQL Server.
    s, e = del_pre('kind: StatefulSet')
    text = text[:s] + PRE + STS_YAML + '</code></pre>' + text[e:]
    # Surgery 6: pg_isready probes -> sqlcmd probes.
    s, e = del_pre('pg_isready')
    text = text[:s] + PRE + PROBES + '</code></pre>' + text[e:]
    # Surgery 7: pg_dump block -> BACKUP block.
    s, e = del_pre('pg_dump from inside a running container')
    text = text[:s] + PRE + BACKUP_BLOCK + '</code></pre>\n\n' + PRE + BACKUP_BASH + '</code></pre>' + text[e:]
    # Surgery 8: pg_upgrade block -> image upgrade block.
    s, e = del_pre('tianon/postgres-upgrade')
    text = text[:s] + PRE + UPGRADE_BLOCK + '</code></pre>' + text[e:]
    # Surgery 9: mermaid diagram -> SQL Server StatefulSet.
    mi = text.index('graph TD')
    mj = text.index('</pre></div>', mi)
    new_diagram = ('graph TD\\n'
        '    SS["StatefulSet: mssql"]\\n'
        '    SS --> Pod0["Pod mssql-0"]\\n'
        '    Pod0 --> PVC0[("PVC: sqldata-mssql-0")]\\n'
        '    Headless["Headless Service"] --> Pod0')
    text = text[:mi] + new_diagram + text[mj:]
    for n, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {n}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch28: 9 surgeries + all {len(REPLACEMENTS)} replacements applied')

main()
