#!/usr/bin/env python3
"""Apply ch26 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch26-event-driven.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)
P = '<p class="text-gray-300 leading-relaxed">'

BRIDGE_A = (P + "SQL Server's native answer is Change Data Capture, covered next — the log-reading approach with the capture and cleanup jobs as its operational surface, and no slot management on your side.</p>")
BRIDGE_B = (P + "For lightweight database-native messaging in SQL Server, the answer is Service Broker — persistent queues with transactional enqueue/dequeue and poison-message handling, covered next.</p>")

REPLACEMENTS = [
# 1 intro
("""This chapter is about how databases fit into that world — how PostgreSQL and SQL Server can both participate in event-driven architectures, either as producers that emit events when data changes or as consumers that process event streams.""",
 """This chapter is about how databases fit into that world — how SQL Server can participate in event-driven architectures, either as a producer that emits events when data changes or as a consumer that processes event streams."""),

# 2 mechanisms
("""Let's walk through how it works structurally, and then we'll look at the native mechanisms both PostgreSQL and SQL Server provide that build on or replace it.""",
 """Let's walk through how it works structurally, and then we'll look at the native mechanisms SQL Server provides that build on or replace it."""),

# 3 CDC both
("""Both PostgreSQL and SQL Server implement CDC by reading the transaction log rather than polling tables. The log is the most faithful record of what changed and when, and it imposes almost no overhead on the primary write path.""",
 """SQL Server implements CDC by reading the transaction log rather than polling tables. The log is the most faithful record of what changed and when, and it imposes almost no overhead on the primary write path."""),

# section title
("""Using LISTEN/NOTIFY and Service Broker for Lightweight Messaging""",
 """Using Service Broker for Lightweight Messaging"""),

# 212 LISTEN/NOTIFY reference
("""Unlike %s/%s, messages survive server restarts and are not dropped if there's no active receiver.""" % (code('LISTEN'), code('NOTIFY')),
 """Messages survive server restarts and are not dropped if there is no active receiver."""),

# 10 idempotency
("""using upsert semantics (%s in PostgreSQL, %s in SQL Server) so re-processing a create event doesn't fail""" % (code('INSERT ... ON CONFLICT DO UPDATE'), code('MERGE')),
 """using upsert semantics (%s) so re-processing a create event doesn't fail""" % code('MERGE')),

# 11 outbox relay locking
("""The outbox relay should also use %s in PostgreSQL or %s in SQL Server to allow multiple relay instances to run concurrently without contending for the same rows.""" % (code('SELECT ... FOR UPDATE SKIP LOCKED'), code('WITH (UPDLOCK, READPAST)')),
 """The outbox relay should also use %s to allow multiple relay instances to run concurrently without contending for the same rows.""" % code('WITH (UPDLOCK, READPAST)')),

# 12 slot lag visibility
("""In PostgreSQL, replication slot lag is visible in%s, as shown earlier. Outbox backlog is trivially queryable:""" % code('pg_replication_slots'),
 """In SQL Server, CDC capture latency is visible in the capture job's history and %s. Outbox backlog is trivially queryable:""" % code('cdc.lsn_time_mapping')),

# 13 JSONB
("""PostgreSQL's JSONB flexibility can hide schema drift in local queries, but it doesn't protect downstream consumers from receiving a field they didn't expect to be absent or renamed.""",
 """SQL Server's JSON flexibility can hide schema drift in local queries, but it doesn't protect downstream consumers from receiving a field they didn't expect to be absent or renamed."""),

# 14 event store
("""PostgreSQL is a reasonable event store for low-to-moderate volume event-sourced systems.""",
 """SQL Server is a reasonable event store for low-to-moderate volume event-sourced systems."""),
("""but the operational simplicity of staying in PostgreSQL has real value.""",
 """but the operational simplicity of staying in SQL Server has real value."""),

# 15 load events code
("""-- PostgreSQL: load all events for an aggregate in order
SELECT
    sequence_number,
    event_type,
    payload,
    occurred_at
FROM domain_events
WHERE aggregate_id = $1
ORDER BY sequence_number ASC;""",
 """-- T-SQL: load all events for an aggregate in order
SELECT
    sequence_number,
    event_type,
    payload,
    occurred_at
FROM domain_events
WHERE aggregate_id = @aggregate_id
ORDER BY sequence_number ASC;"""),

# 16 snapshot code
("""-- PostgreSQL: snapshot table for event-sourced aggregates
CREATE TABLE aggregate_snapshots (
    aggregate_id    UUID        NOT NULL,
    aggregate_type  TEXT        NOT NULL,
    sequence_number BIGINT      NOT NULL,
    state           JSONB       NOT NULL,
    taken_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_snapshots PRIMARY KEY (aggregate_id, sequence_number)
);""",
 """-- T-SQL: snapshot table for event-sourced aggregates
CREATE TABLE aggregate_snapshots (
    aggregate_id    UNIQUEIDENTIFIER NOT NULL,
    aggregate_type  NVARCHAR(128)    NOT NULL,
    sequence_number BIGINT           NOT NULL,
    state           NVARCHAR(MAX)    NOT NULL,   -- JSON document
    taken_at        DATETIME2        NOT NULL DEFAULT SYSUTCDATETIME(),

    CONSTRAINT pk_snapshots PRIMARY KEY (aggregate_id, sequence_number)
);"""),
("""    FROM aggregate_snapshots
    WHERE aggregate_id = $1
    ORDER BY sequence_number DESC
    LIMIT 1
)""",
 """    FROM aggregate_snapshots
    WHERE aggregate_id = @aggregate_id
    ORDER BY sequence_number DESC
    OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY
)"""),
("""WHERE e.aggregate_id = $1
  AND e.sequence_number &gt; COALESCE(s.sequence_number, 0)""",
 """WHERE e.aggregate_id = @aggregate_id
  AND e.sequence_number &gt; COALESCE(s.sequence_number, 0)"""),
]

def main():
    lines = open(PATH).read().split('\n')
    # Surgery A: PG logical-decoding subsection -> bridge (0-based 140..148).
    assert 'PostgreSQL Logical Replication and Logical Decoding' in lines[140], lines[140][:80]
    assert 'SQL Server Change Data Capture' in lines[149], lines[149][:80]
    lines[140:149] = [BRIDGE_A, '']
    # Surgery B: PG LISTEN/NOTIFY subsection -> bridge. Re-locate after edit.
    text = '\n'.join(lines)
    i = text.index('PostgreSQL LISTEN/NOTIFY')
    start = text.rindex('<p', 0, i)
    j = text.index('SQL Server Service Broker')
    end = text.rindex('<p', 0, j)
    text = text[:start] + BRIDGE_B + '\n\n' + text[end:]
    for n, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {n}: found {count} occurrences')
            print('OLD SNIPPET:', old[:150])
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch26: 2 surgeries + all {len(REPLACEMENTS)} replacements applied')

main()
