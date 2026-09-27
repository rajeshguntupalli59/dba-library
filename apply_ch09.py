#!/usr/bin/env python3
"""Apply ch09 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch09-access-control.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter walks through the complete access control model in PostgreSQL and SQL Server: how authentication and authorization work, how roles and privileges are structured, how to lock down a production environment, and how to audit who has access to what.""",
 """This chapter walks through the complete access control model in SQL Server: how authentication and authorization work, how roles and privileges are structured, how to lock down a production environment, and how to audit who has access to what."""),

# 2 auth paragraph
("""In PostgreSQL, authentication is controlled entirely outside of SQL, through the %s file (Host-Based Authentication). Each line in that file matches a combination of connection type, database name, username, client address, and authentication method. Common methods include %s, %s, %s, %s, and %s. The order of rules matters — PostgreSQL reads the file top to bottom and applies the first matching rule.""" % (code('pg_hba.conf'), code('md5'), code('scram-sha-256'), code('peer'), code('ldap'), code('cert')),
 """In SQL Server, authentication is controlled by the server's authentication mode — Windows Authentication mode or Mixed Mode — set at install and changeable under Server Properties → Security (restart required). Windows/AD logins delegate to the domain (Kerberos preferred; confirm with the auth_scheme column in %s), while SQL logins are managed inside the instance with password policy enforcement via %s and %s.""" % (code('sys.dm_exec_connections'), code('CHECK_POLICY'), code('CHECK_EXPIRATION'))),

# 3 authorization intro
("""This is where %s, %s, %s, roles, and schemas come into play — the entire subject of permissions management. Both systems separate authentication from authorization, but the design philosophy differs: PostgreSQL uses a unified role model that merges the concepts of users and groups, while SQL Server maintains a strict separation between logins (server-level) and users (database-level).""" % (code('GRANT'), code('REVOKE'), code('DENY')),
 """This is where %s, %s, %s, roles, and schemas come into play — the entire subject of permissions management. SQL Server separates authentication from authorization with a strict two-tier design: logins (server-level identities) are mapped to users (database-level identities), and permissions flow through role membership — which is where least privilege is actually implemented.""" % (code('GRANT'), code('REVOKE'), code('DENY'))),

# 4 dropping logins
("""Conversely, dropping a PostgreSQL role that still owns objects or has active dependencies will fail entirely until those dependencies are resolved.""",
 """Conversely, dropping a login while its database users still exist leaves orphaned users behind — always drop the database users first, then the login."""),

# 5 h3
("""The Role Model in PostgreSQL and the Login/User Model in SQL Server""",
 """The Login/User Model in SQL Server"""),

# 6 role concept intro
("""Both systems use the concept of a *role* as the primary unit of identity and permission, but the implementation differs enough to cause confusion when you work across both platforms.""",
 """SQL Server uses the role as the primary unit of permission — server roles at the instance level, database roles at the database level — with logins and users as the identity endpoints that get placed into those roles."""),

# 7 PG everything-is-role -> SQL Server separation
("""<strong class="text-white">PostgreSQL</strong> treats everything as a role. There is no separate object type for "user" versus "group." When you run %s, PostgreSQL internally runs %s — the %s attribute is what distinguishes an interactive user from a group role. Roles can be members of other roles, creating a hierarchy that allows permissions to be inherited.""" % (code('CREATE USER'), code('CREATE ROLE ... WITH LOGIN'), code('LOGIN')),
 """<strong class="text-white">SQL Server</strong> separates identity from permission deliberately. A <strong class="text-white">login</strong> proves who you are to the instance; a <strong class="text-white">user</strong> is that login's presence inside a database; <strong class="text-white">roles</strong> — server-level and database-level, fixed and user-defined — carry the permissions. You create the login, create the user mapped to it, and add the user to roles. Custom database roles with explicit grants are the right approach for anything beyond development — the fixed roles (%s, %s, %s) are convenient but coarse.""" % (code('db_datareader'), code('db_datawriter'), code('db_owner'))),

# 8 rolsuper -> sysadmin
("""In PostgreSQL, the %s, %s, %s, %s, and %s attributes on a role control powerful system-level capabilities. These should be treated like production keys — only granted to accounts that genuinely require them, and ideally to service accounts with no interactive login rather than to personal accounts. The superuser attribute in particular bypasses every permission check in the system, including row-level security.""" % (code('rolsuper'), code('rolcreaterole'), code('rolcreatedb'), code('rolreplication'), code('rolbypassrls')),
 """The fixed server roles control powerful instance-level capabilities — %s above all. Treat sysadmin membership like production keys: only for accounts that genuinely require it, ideally service accounts with no interactive use rather than personal accounts. Members of sysadmin bypass every permission check in the system, including RLS predicates and %s.""" % (code('sysadmin'), code('DENY'))),

# 9 sysadmin paragraph PG reference
("""In SQL Server, the equivalent of a PostgreSQL superuser is membership in the %s server role. Members of %s can do anything to the instance.""" % (code('sysadmin'), code('sysadmin')),
 """Membership in the %s server role grants complete control over the instance. Members of %s can do anything — there is no permission check they don't pass.""" % (code('sysadmin'), code('sysadmin'))),

# 10 guest user PG reference
("""One SQL Server behavior that surprises many DBAs coming from PostgreSQL is the <strong class="text-white">guest user</strong>.""",
 """One SQL Server behavior that surprises many DBAs is the <strong class="text-white">guest user</strong>."""),

# 11 privilege levels
("""In PostgreSQL, the privilege system operates at several levels: database, schema, table, column, sequence, function, and more. The two commands you use most are %s and %s. PostgreSQL also has a concept of <strong class="text-white">default privileges</strong>, which allows you to define what permissions should automatically be applied to new objects created in the future — this is something many DBAs overlook and then wonder why a new table isn't accessible.""" % (code('GRANT'), code('REVOKE')),
 """In SQL Server, the privilege system operates at several levels: server, database, schema, table, column, and more. The three commands you use most are %s, %s, and %s. Permissions can be granted at the schema level — %s — which automatically covers future tables created in that schema. Schema-level grants are the cleanest way to handle a growing schema without per-table grant maintenance.""" % (code('GRANT'), code('REVOKE'), code('DENY'), code('GRANT SELECT ON SCHEMA::sales TO reporting_team'))),

# 12 DENY
("""One of the sharpest differences between the two systems here is SQL Server's %s command. In SQL Server, %s explicitly prohibits an action and takes precedence over any %s — even grants inherited through role membership.""" % (code('DENY'), code('DENY'), code('GRANT')),
 """One of the sharpest tools in SQL Server's model is the %s command. %s explicitly prohibits an action and takes precedence over any %s — even grants inherited through role membership.""" % (code('DENY'), code('DENY'), code('GRANT'))),
("""In PostgreSQL, there is no equivalent %s. The model is purely additive: permissions accumulate through direct grants and role memberships, and if you want to restrict access you revoke grants rather than denying them.""" % code('DENY'),
 """Use %s sparingly — because it overrides grants even through role inheritance, it makes effective-permission auditing harder to reason about. Prefer designing roles so that %s is rarely needed.""" % (code('DENY'), code('DENY'))),

# 13 multi-tenant
("""This difference has a practical consequence. In a PostgreSQL multi-tenant application where different users need access to different row subsets of the same table, row-level security (covered in the next section) is usually the right tool. In SQL Server, you might use %s at the table level and then %s through carefully scoped views or procedures to achieve granular control.""" % (code('DENY'), code('GRANT')),
 """This has a practical consequence. In a multi-tenant application where different users need access to different row subsets of the same table, row-level security (covered in the next section) is usually the right tool. You might also use %s at the table level and then %s through carefully scoped views or procedures to achieve granular control.""" % (code('DENY'), code('GRANT'))),

# 14 public schema PG -> SQL Server
("""In PostgreSQL, the %s schema deserves special attention. By default, all users have the %s and %s privileges on the %s schema, and all users have %s privilege on all databases. If you create a table in %s, every authenticated user can see it unless you explicitly lock it down. For PostgreSQL 14 and earlier, this means that at database setup time you should immediately run:""" % (code('public'), code('USAGE'), code('CREATE'), code('public'), code('CONNECT'), code('public')),
 """In SQL Server, the %s role and the %s user deserve special attention. Every database has an implicit guest account — if it's enabled, any authenticated login without an explicit user mapping can connect through it. And the public role holds default grants that are broader than most organizations realize. At database setup time, audit both:""" % (code('public'), code('guest'))),

# 15 PG15 paragraph -> drop, replaced with SQL Server note
("""PostgreSQL 15 changed this behavior — %s on the %s schema is no longer granted to %s by default — but if you're running an older version or inheriting a cluster, always verify these settings.""" % (code('CREATE'), code('public'), code('PUBLIC')),
 """Verify these settings on every inherited database, not just new builds — defaults drift, and the databases you didn't set up are the ones most likely to carry surprises."""),

# 16 RLS header paragraph
("""<strong class="text-white">PostgreSQL Row-Level Security</strong> is implemented through policies. You enable RLS on a table and then define one or more policies that determine which rows are visible or modifiable for a given role. The policies are applied transparently — the application doesn't need to add any WHERE clause; the database enforces the filter automatically.""",
 """<strong class="text-white">Row-Level Security</strong> is implemented through security policies. You create an inline table-valued predicate function and bind it to the table with %s; the engine then applies the filter transparently — the application doesn't need to add any WHERE clause, and the user can't remove the filter.""" % code('CREATE SECURITY POLICY')),

# 17 USING/WITH CHECK -> filter/block predicates
("""A subtlety worth knowing: %s controls which rows are visible for reads (SELECT) and which rows can be modified (the WHERE condition in UPDATE/DELETE). %s controls which rows can be inserted or updated *into* — it validates the row after the change, not before. If you create an RLS policy without a %s clause on an UPDATE or INSERT policy, PostgreSQL defaults to using the %s expression for that check too. Most production policies should define both.""" % (code('USING'), code('WITH CHECK'), code('WITH CHECK'), code('USING')),
 """A subtlety worth knowing: the filter predicate controls which rows are visible for reads and which rows can be modified. <strong class="text-white">Block predicates</strong> validate writes — without them, a user could insert rows they'd never be able to read back, or update rows out of their own visibility. Most production policies should define both filter and block predicates."""),

# 18 pgaudit -> SQL Server Audit
("""PostgreSQL provides <strong class="text-white">pgaudit</strong>, an extension that integrates with the standard logging infrastructure to produce structured audit logs at the session level or object level. At the object level, you define which operations on which objects should be logged. pgaudit outputs through the normal PostgreSQL log facility, so your existing log shipping and SIEM integration infrastructure applies.""",
 """SQL Server Audit integrates with the instance to produce structured audit logs at the server and database level. At the database level, a database audit specification defines which operations on which objects get logged. Audit output goes to files, the Security log, or the Application log — so your existing log shipping and SIEM integration infrastructure applies."""),

# 19 system views PG tail
(""" In PostgreSQL, %s, %s, and the %s, %s, and %s functions let you test permissions from within the session, which is far faster than hunting through catalog joins.""" % (code('pg_roles'), code('pg_auth_members'), code('has_table_privilege()'), code('has_schema_privilege()'), code('has_column_privilege()')),
 """ %s lets you test effective permissions from within the session, which is far faster than hunting through catalog joins.""" % code('fn_my_permissions')),

# 20 two scenarios -> orphaned users only
("""Two production scenarios that illustrate why this matters: First, a %s on %s in PostgreSQL affects every table that existed at the time of the grant, but not tables created afterward — unless %s was also set. This means that as the schema grows, the reporting user silently loses access to new tables without anyone noticing, or (in the worse scenario) someone sets %s too broadly and new tables grant access to roles that shouldn't have it. Second, in SQL Server, when a database is restored from a backup to a different server, the SIDs of SQL logins may not match the SIDs of users inside the database.""" % (code('GRANT'), code('ALL TABLES IN SCHEMA'), code('ALTER DEFAULT PRIVILEGES'), code('ALTER DEFAULT PRIVILEGES')),
 """One production scenario that illustrates why this matters: when a database is restored from a backup to a different server, the SIDs of SQL logins may not match the SIDs of users inside the database."""),

# 21 SECURITY DEFINER -> EXECUTE AS
("""PostgreSQL's %s functions deserve attention here. When a function is defined with %s, it executes with the privileges of the function's owner, not the calling user. This is the PostgreSQL equivalent of ownership chaining and %s combined. It allows non-privileged users to perform controlled operations on objects they otherwise cannot access. The risk is that a %s function that takes unsanitized user input and builds dynamic SQL is a privilege escalation vector. Any function using this attribute should be written with the same care as security-critical code: input validation, parameterized queries, and a clear understanding of what the owner's privileges allow.""" % (code('SECURITY DEFINER'), code('SECURITY DEFINER'), code('EXECUTE AS'), code('SECURITY DEFINER')),
 """Stored procedures defined %s deserve attention here. Such a procedure executes with the privileges of the specified principal — typically the schema owner — not the calling user. Combined with ownership chaining (same-owner procedure and tables need no explicit table grants), this is the controlled way to let non-privileged users perform specific operations on objects they otherwise cannot access. The risk is real: a procedure that takes unsanitized input and builds dynamic SQL is a privilege escalation vector. Any procedure using %s should be written with the same care as security-critical code: input validation, parameterized queries via %s, and a clear understanding of what the owner's privileges allow.""" % (code('WITH EXECUTE AS OWNER'), code('EXECUTE AS'), code('sp_executesql'))),

# 22 cross-database PG part
("""<strong class="text-white">Cross-database access</strong> is another edge worth understanding. In PostgreSQL, a connection is tied to a single database — there is no built-in cross-database query mechanism without extensions like %s or %s. This is actually a security asset: compromising access to one database does not inherently expose another. In SQL Server, linked servers and three-part names (%s) allow cross-database queries, which creates cross-database permission dependencies that need to be tracked.""" % (code('dblink'), code('postgres_fdw'), code('OtherDB.dbo.tablename')),
 """<strong class="text-white">Cross-database access</strong> is another edge worth understanding. In SQL Server, linked servers and three-part names (%s) allow cross-database queries, which creates cross-database permission dependencies that need to be tracked.""" % code('OtherDB.dbo.tablename')),

# 23 takeaway DENY
("""**PostgreSQL's permission model is purely additive; SQL Server's is not.** PostgreSQL has no DENY — permissions accumulate through grants and role memberships, so restricting access means revoking a grant. SQL Server's DENY overrides grants even through role inheritance, which enables fine-grained restriction but adds a second mechanism a DBA must account for when reasoning about a principal's effective permissions.""",
 """**SQL Server's permission model is not purely additive.** DENY overrides grants even through role inheritance, which enables fine-grained restriction but adds a second mechanism a DBA must account for when reasoning about a principal's effective permissions — use it sparingly and document every one."""),

# 24 takeaway RLS
("""**Row-level and column-level security enforce access at a finer grain than table permissions can.** PostgreSQL's RLS policies and SQL Server's security policies (built on inline table-valued functions) both filter rows transparently at the engine level, but neither protects against a superuser or `sysadmin`-level connection — those bypass the policy entirely, which is a strong argument against using highly-privileged accounts for routine application access.""",
 """**Row-level and column-level security enforce access at a finer grain than table permissions can.** SQL Server's security policies (built on inline table-valued functions) filter rows transparently at the engine level, but they don't protect against a `sysadmin`-level connection — those bypass the policy entirely, which is a strong argument against using highly-privileged accounts for routine application access."""),

# 25 takeaway audit
("""**Static permission snapshots are not enough; you need both audit logging and periodic review.** `pgaudit` in PostgreSQL and native SQL Server Audit provide event-level trails of who did what, while a recurring diff of the current permission state against a prior snapshot catches drift — orphaned grants, stale role memberships, and privileges nobody remembers approving — before it becomes a compliance or security incident.""",
 """**Static permission snapshots are not enough; you need both audit logging and periodic review.** Native SQL Server Audit provides event-level trails of who did what, while a recurring diff of the current permission state against a prior snapshot catches drift — orphaned grants, stale role memberships, and privileges nobody remembers approving — before it becomes a compliance or security incident."""),

# 26 takeaway ownership
("""**Ownership, impersonation, and cross-database trust settings can override the permission model you think is in effect.** Ownership chaining and `EXECUTE AS` in SQL Server, `SECURITY DEFINER` functions in PostgreSQL, and the `TRUSTWORTHY` database property all create paths where effective privilege differs from what a straightforward `GRANT`/`REVOKE` audit would show — knowing where to look for them is part of managing access control seriously.""",
 """**Ownership, impersonation, and cross-database trust settings can override the permission model you think is in effect.** Ownership chaining, `EXECUTE AS`, and the `TRUSTWORTHY` database property all create paths where effective privilege differs from what a straightforward `GRANT`/`REVOKE` audit would show — knowing where to look for them is part of managing access control seriously."""),
]

# Code-block replacement: PG REVOKE public-schema SQL -> SQL Server lockdown SQL
CODE_OLD = """-- Revoke public schema defaults (run as superuser at cluster setup time)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE mydb FROM PUBLIC;"""
CODE_NEW = """-- Lock down defaults (run in each user database)
REVOKE CONNECT FROM guest;
-- Audit what the public role can actually do:
SELECT p.permission_name, p.state_desc, o.name AS object_name
FROM sys.database_permissions AS p
LEFT JOIN sys.objects AS o ON p.major_id = o.object_id
WHERE p.grantee_principal_id = DATABASE_PRINCIPAL_ID('public');"""

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
    print(f'ch09: all {len(REPLACEMENTS)} prose + 1 code-block replacements applied')

main()
