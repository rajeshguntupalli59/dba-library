#!/usr/bin/env python3
"""Apply ch08 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch08-security.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
# 1 intro
("""This chapter walks through the foundational security model of both PostgreSQL and SQL Server — from authentication and authorization through privilege management, row-level security, auditing, and encryption at rest and in transit.""",
 """This chapter walks through the foundational security model of SQL Server — from authentication and authorization through privilege management, row-level security, auditing, and encryption at rest and in transit."""),

# 2 auth intro
("""Authentication answers a single question: are you who you claim to be? Both PostgreSQL and SQL Server have layered authentication systems, but they approach that question differently.""",
 """Authentication answers a single question: are you who you claim to be? SQL Server answers it with two authentication modes and a layered login system — and misconfiguring that layer is one of the most common findings in security audits."""),

# 3 pg_hba -> auth modes
("""PostgreSQL's authentication is controlled by a file called %s — Host-Based Authentication configuration. This file is read top-to-bottom, and the first rule that matches a connection request is applied. Each line specifies a connection type (local socket, host, hostssl, hostnossl), a database, a user, an address range, and an authentication method. If you've ever been confused about why a password you're certain is correct keeps getting rejected, the answer is almost always in %s.""" % (code('pg_hba.conf'), code('pg_hba.conf')),
 """SQL Server's authentication is controlled by the server's authentication mode: Windows Authentication mode (only Windows/AD identities) or Mixed Mode (Windows plus SQL Server logins). It's set at install time and changeable under Server Properties → Security in SSMS, requiring a restart. The mode is the first thing to check when a login fails that "should" work — a SQL login cannot authenticate at all against a Windows-only instance, and the error log won't always make that obvious."""),

# 4 auth methods -> login types
("""The authentication methods available in PostgreSQL include %s (no password required — frightening in production), %s and %s (password-based), %s (matches OS username to database username for local connections), %s, %s, %s, and %s (SSL client certificate). In modern PostgreSQL deployments, %s is preferred over %s because MD5 is cryptographically broken and transmits a hash that can be replayed. You should audit your %s for any remaining %s entries and update them.""" % (code('trust'), code('md5'), code('scram-sha-256'), code('peer'), code('ldap'), code('gss'), code('radius'), code('cert'), code('scram-sha-256'), code('md5'), code('pg_hba.conf'), code('md5')),
 """For SQL logins, enforce password policy with %s and %s so domain complexity and expiry rules apply to database passwords too. Prefer Windows/AD authentication wherever possible — it delegates credential management to the domain, supports Kerberos (verify with the auth_scheme column in %s), removes passwords from connection strings, and makes deprovisioning a matter of disabling one AD account instead of hunting logins across instances.""" % (code('CHECK_POLICY=ON'), code('CHECK_EXPIRATION=ON'), code('sys.dm_exec_connections'))),

# 5 sa/postgres
("""A common production mistake in both systems is leaving the highest-privileged accounts reachable from the network. In PostgreSQL, the %s superuser should either have its %s entry restricted to %s connections only or be protected by certificate authentication. In SQL Server, the %s login should be disabled outright in most production environments — AD service accounts and application logins should carry only the privileges they need.""" % (code('postgres'), code('pg_hba.conf'), code('local'), code('sa')),
 """A common production mistake is leaving the highest-privileged accounts reachable from the network. The %s login should be disabled outright in most production environments — and renamed as well, so attackers can't target a known account name. AD service accounts and application logins should carry only the privileges they need. If %s must exist for break-glass, give it a long random password stored in a vault, and alert on any use of it.""" % (code('sa'), code('sa'))),

# 6 auth method visibility
("""Note that PostgreSQL does not expose the authentication method used by an individual connection through a system view — %s shows what the rules *would* allow, but confirming which method a specific session actually used requires enabling %s and checking the server log.""" % (code('pg_hba_file_rules'), code('log_connections')),
 """SQL Server exposes login metadata through %s and %s — you can audit which logins exist, which are disabled, whether password policy is enforced, and when passwords were last changed. %s shows the auth scheme (NTLM, Kerberos, or SQL) per live session, which is how you confirm Kerberos is actually being used rather than assumed.""" % (code('sys.server_principals'), code('sys.sql_logins'), code('sys.dm_exec_connections'))),

# 7 trust trap -> weak login trap
("""One trap worth calling out explicitly: in PostgreSQL, setting %s to %s for a local socket connection might seem harmless because you assume only OS processes can reach the socket. But if your application runs on the same server as the database and an attacker achieves code execution on that host, %s means they walk straight in. The principle is defense in depth — even local connections should require authentication in sensitive environments.""" % (code('auth_method'), code('trust'), code('trust')),
 """One trap worth calling out explicitly: SQL logins created with %s and a weak password, or applications connecting as %s "temporarily" and never being fixed. Another is the service account running as a domain admin because the installer needed it once. The principle is defense in depth — every layer (network, login, database, object) should independently require proof, because attackers only need one layer to fail.""" % (code('CHECK_POLICY=OFF'), code('sa'))),

# 8 authorization intro
("""Once a connection is authenticated, the database needs to know what that identity is allowed to do. Both PostgreSQL and SQL Server use a role-based model, but the terminology and mechanics differ enough to cause genuine confusion if you're switching between the two.""",
 """Once a connection is authenticated, the database needs to know what that identity is allowed to do. SQL Server uses a two-tier role-based model — server-level logins and roles, database-level users and roles — and the mechanics repay precise understanding, because this is where least privilege is actually implemented."""),

# 9 PG roles -> SQL Server principals
("""In PostgreSQL, everything is a role. There is no separate concept of a "user" versus a "group" — a role can log in (making it effectively a user), own objects, hold other roles as members, and carry attributes like %s, %s, %s, and %s. When you run %s, PostgreSQL simply creates a role with %s attribute enabled. When you run %s, it creates a role with %s. The inheritance model means that when role A is granted to role B, B automatically inherits A's privileges — unless the role is created with %s, which forces B to explicitly %s before exercising those privileges.""" % (code('SUPERUSER'), code('CREATEDB'), code('CREATEROLE'), code('REPLICATION'), code('CREATE USER'), code('LOGIN'), code('CREATE GROUP'), code('NOLOGIN'), code('NOINHERIT'), code('SET ROLE A')),
 """In SQL Server, the hierarchy is: <strong class="text-white">login</strong> (the server-level identity, Windows or SQL) → <strong class="text-white">user</strong> (the database-level identity mapped to a login) → <strong class="text-white">role membership</strong> (fixed server roles like %s, fixed database roles like %s, and user-defined database roles you create). Permissions are granted to roles, and roles are granted to users — never grant permissions directly to individual users if you want access changes to stay auditable and reversible. Contained databases collapse the two tiers: the user authenticates directly at the database level with no server login, which simplifies Availability Group failovers and migrations because there's no SID to orphan.""" % (code('sysadmin'), code('db_owner'))),

# 10 two-step + orphaned users
("""The practical implication is that SQL Server requires two steps to give someone database access: create the login, then create the user in the target database and map it to that login. PostgreSQL has one step — create the role with appropriate attributes and grant it permissions.""",
 """The practical implication is that SQL Server requires two steps to give someone database access: create the login, then create the user in the target database and map it to that login. The classic failure is the <strong class="text-white">orphaned user</strong> — a database user whose login no longer exists (different SID) after a restore or migration. %s repairs the mapping, and auditing for orphaned users should be part of every restore validation.""" % code('ALTER USER ... WITH LOGIN')),

# 11 privilege visibility
("""In PostgreSQL, privilege visibility comes from the system catalog and information schema. In SQL Server, the %s and %s views are your tools.""" % (code('sys.database_permissions'), code('fn_my_permissions')),
 """In SQL Server, %s, %s, and %s are your tools for auditing who can do what — run them before every compliance review, not after the auditor asks.""" % (code('sys.database_permissions'), code('sys.server_permissions'), code('fn_my_permissions'))),

# 12 RLS intro
("""Both PostgreSQL and SQL Server support RLS, and both work on the same conceptual model: you define a policy that adds a filter expression to queries against a table. When a user queries the table, the database engine automatically appends that filter condition, as though the user had written it in their WHERE clause — except they can't remove it.""",
 """SQL Server supports Row-Level Security on a simple conceptual model: you define a policy that adds a filter expression to queries against a table. When a user queries the table, the engine automatically appends that filter condition, as though the user had written it in their WHERE clause — except they can't remove it."""),

# 13 RLS mechanics
("""In PostgreSQL, RLS must be explicitly enabled on a table. Table owners bypass RLS by default (superusers do too, unless you use %s). The policy definition specifies whether it applies to %s, %s, %s, %s, or %s commands, and defines a %s expression for read policies and a %s expression for write policies.""" % (code('SET row_security = force'), code('SELECT'), code('INSERT'), code('UPDATE'), code('DELETE'), code('ALL'), code('USING'), code('WITH CHECK')),
 """In SQL Server, RLS is implemented with a predicate function — an inline table-valued function returning 1 for allowed rows — bound to the table via %s. The filter predicate applies to reads; block predicates can reject writes that would violate the policy. Members of %s bypass RLS predicates by default, so design your ETL and service accounts with that in mind rather than discovering it during a test.""" % (code('CREATE SECURITY POLICY'), code('db_owner'))),

# 14 RLS bypass nuance
("""A nuance in PostgreSQL's RLS: if you have a role that needs to bypass RLS for administrative purposes (running ETL, batch updates, producing audit reports), you can use %s — but this requires the %s role attribute, which should be granted sparingly. For application roles, the policy is always enforced.""" % (code('SET row_security = off'), code('BYPASSRLS')),
 """A nuance: if a role needs to bypass RLS for administrative purposes (running ETL, batch updates, producing audit reports), it must be %s or the policy must explicitly exempt it — grant that sparingly, and document why. For application roles, the policy is always enforced. Test RLS with %s to verify each role sees exactly its rows before you declare the feature done.""" % (code('db_owner'), code('EXECUTE AS'))),

# 15 pgaudit -> SQL Server Audit
("""PostgreSQL doesn't ship with a built-in audit framework. The native logging controlled by %s can capture statements (%s), connection events (%s, %s), and DDL. This is a starting point, but it's not a proper audit trail — logs are sequential text files, they're not queryable, they don't have per-table granularity, and they can be rotated away. For production audit requirements, the standard approach is the %s extension, which integrates with PostgreSQL's logging infrastructure but provides object-level and statement-level audit categories with proper session context.""" % (code('postgresql.conf'), code("log_statement = 'all'"), code('log_connections'), code('log_disconnections'), code('pgaudit')),
 """SQL Server ships a built-in audit framework: <strong class="text-white">SQL Server Audit</strong>. Server audits write to the Security log, the Application log, or files; database audit specifications capture statement-level and object-level events with proper session context. Unlike text logs, audit output is structured and queryable via %s. Write audit output to a volume the DBAs don't casually browse, and ship it off the database server — an audit trail the audited party can edit is theater, not compliance.""" % code('sys.fn_get_audit_file')),

# 16 pgaudit config -> audit config
("""After installing %s, you configure it via %s (for session-level auditing) or via the role attribute %s (for object-level auditing of specific tables or columns):""" % (code('pgaudit'), code('postgresql.conf'), code('pgaudit.role')),
 """You configure SQL Server Audit with %s (where output goes, and what happens on audit failure — shut the server down or keep running), then %s for the events you care about: SELECT/INSERT/UPDATE/DELETE on sensitive tables, failed logins, permission and role changes. Audit at the granularity your compliance regime requires; auditing everything is how you fill a disk at 3 a.m.:""" % (code('CREATE SERVER AUDIT'), code('CREATE DATABASE AUDIT SPECIFICATION'))),

# 17 TLS
("""Both databases use TLS for encrypting connections. In PostgreSQL, TLS support is compiled in and enabled by setting %s in %s, providing a certificate and key, and configuring %s with %s entries. Client connections can be required to use SSL by setting %s (verifies the connection is encrypted) or %s (verifies the connection is encrypted and that the server certificate is valid and matches the hostname). In production, %s is the right choice — %s without verification is susceptible to man-in-the-middle attacks.""" % (code('ssl = on'), code('postgresql.conf'), code('pg_hba.conf'), code('hostssl'), code('sslmode=require'), code('sslmode=verify-full'), code('verify-full'), code('require')),
 """SQL Server encrypts connections with TLS using a certificate installed in the machine certificate store, configured via SQL Server Configuration Manager. Enable the Force Encryption flag so unencrypted connections are refused, and on the client use %s with %s so the certificate chain is actually validated. In production, full verification is the right choice — encryption without certificate verification is susceptible to man-in-the-middle attacks.""" % (code('Encrypt=yes'), code('TrustServerCertificate=no'))),

# 18 TDE
("""PostgreSQL does not have an equivalent TDE implementation at the storage engine level (as of PostgreSQL 16, though development work is ongoing). The conventional approach is to use filesystem-level encryption — dm-crypt/LUKS on Linux, or BitLocker on Windows — which encrypts the entire volume containing the PostgreSQL data directory. This provides the same protection against physical media theft but is managed at the OS level rather than the database level. Some cloud-managed PostgreSQL offerings implement their own storage encryption transparently.""",
 """SQL Server's Transparent Data Encryption encrypts data files, log files, and backups at the storage engine level via a database encryption key protected by a certificate in master. Enable it with %s followed by %s — then immediately back up the certificate and private key and store them off-server, because without them your backups are unrecoverable. TDE protects against physical media theft; it does not protect against a compromised sysadmin, which is what auditing and Always Encrypted are for.""" % (code('CREATE DATABASE ENCRYPTION KEY'), code('ALTER DATABASE ... SET ENCRYPTION ON'))),

# 19 pgcrypto -> Always Encrypted
("""PostgreSQL's %s extension provides %s and %s functions for symmetric encryption, and asymmetric variants for key management scenarios. SQL Server offers Always Encrypted, which keeps the column-level encryption keys on the client side — the database server itself never sees the plaintext, which protects against a compromised DBA or backup theft.""" % (code('pgcrypto'), code('pgp_sym_encrypt'), code('pgp_sym_decrypt')),
 """For column-level protection, SQL Server offers <strong class="text-white">Always Encrypted</strong>: the column encryption keys live on the client side — the database server itself never sees the plaintext, which protects against a compromised DBA or backup theft. The tradeoff is limited query capability on encrypted columns (deterministic encryption supports equality, randomized does not) and driver requirements on every client. Use it for specific high-sensitivity fields like SSNs or card numbers, not whole tables."""),

# 20 defaults
("""The defaults in both PostgreSQL and SQL Server are designed for broad compatibility and ease of getting started, not for security. The %s schema in PostgreSQL historically granted %s to all users — a change made in PostgreSQL 15 restricts this, but environments on older versions may still carry it. In SQL Server, the %s role has %s permission on a set of system stored procedures by default, which is a larger attack surface than most organizations realize.""" % (code('public'), code('CREATE'), code('public'), code('EXECUTE')),
 """The defaults in SQL Server are designed for broad compatibility and ease of getting started, not for security. The %s role has %s permission on a set of system stored procedures by default, which is a larger attack surface than most organizations realize — audit public-role grants and revoke what applications don't need. Also review the %s user in each database and disable it where it isn't required.""" % (code('public'), code('EXECUTE'), code('guest'))),

# 21 ports
("""Database ports (5432 for PostgreSQL, 1433 for SQL Server) should be reachable only from application servers, not from developer laptops, not from the general office network, and certainly not from the internet.""",
 """The SQL Server port (1433 by default) should be reachable only from application servers, not from developer laptops, not from the general office network, and certainly not from the internet."""),

# 22 sa/postgres takeaway
("""Superuser and %s-level accounts deserve special treatment. Their use should be exceptional, logged, and ideally require a break-glass procedure. In SQL Server, %s should be disabled. In PostgreSQL, %s should have password authentication required even locally, and all routine administrative tasks should be performed as application-specific roles with only the necessary privileges.""" % (code('sa'), code('sa'), code('postgres')),
 """%s-level accounts deserve special treatment. Their use should be exceptional, logged, and ideally require a break-glass procedure. %s should be disabled and renamed; all routine administrative tasks should be performed as AD service accounts or application logins carrying only the necessary privileges.""" % (code('sa'), code('sa'))),

# 23 object ownership
("""Object ownership is another overlooked surface. In PostgreSQL, the role that owns a schema or table can drop it, alter it, or change its permissions — regardless of what other roles are configured. Application roles should not own production objects. A dedicated %s role (which holds no login attribute) should own production schemas, and that role should be used only when DDL changes are made, not for routine application connections.""" % code('schema_owner'),
 """Object ownership is another overlooked surface. In SQL Server, the schema owner (often %s) controls the objects — application roles should not own production schemas. And beware <strong class="text-white">ownership chaining</strong>: when a stored procedure and the tables it touches share the same owner, the procedure can access those tables without explicit grants on them. That's convenient, but it means a compromised procedure account inherits broad read access — review chained access paths, not just direct grants.""" % code('dbo')),

# 24 takeaway auth
("""Authentication configuration lives in `pg_hba.conf` (PostgreSQL) and in the server's authentication mode setting (SQL Server); both should be audited for weak methods (`trust`, unencrypted `md5`, `sa` left enabled) rather than trusted to have been configured correctly once and left alone.""",
 """Authentication configuration lives in the server's authentication mode setting and in the login inventory (`sys.server_principals`, `sys.sql_logins`); audit for weak methods (`CHECK_POLICY=OFF`, `sa` left enabled, NTLM where Kerberos was intended) rather than trusting it was configured correctly once and left alone."""),

# 25 takeaway roles
("""PostgreSQL's unified role model and SQL Server's two-tier login/user model achieve the same goal — least-privilege access — through different mechanics; grant permissions to roles, not individual users, so access changes are auditable and reversible.""",
 """SQL Server's two-tier login/user model exists to serve least-privilege access; grant permissions to roles, not individual users, so access changes are auditable and reversible — and hunt orphaned users after every restore or migration."""),

# 26 takeaway RLS
("""Row-Level Security, enforced by the database engine itself in both PostgreSQL and SQL Server, is the right tool when access needs to be restricted by row content (like tenant isolation) rather than by table — but predicate columns must be indexed or performance suffers badly at scale.""",
 """Row-Level Security, enforced by the database engine itself, is the right tool when access needs to be restricted by row content (like tenant isolation) rather than by table — but predicate columns must be indexed or performance suffers badly at scale, and always verify with `EXECUTE AS` before shipping."""),

# 27 takeaway auditing
("""Auditing requires a real strategy, not just default logging: PostgreSQL needs the `pgaudit` extension for a queryable, object-level audit trail, while SQL Server ships Server Audit with tamper-evident output built in; either way, audit logs should be shipped off the database server itself.""",
 """Auditing requires a real strategy, not just default logging: SQL Server Audit gives you a structured, queryable, object-level audit trail built in — but audit logs must be shipped off the database server itself, or they protect no one."""),

# 28 takeaway encryption
("""Encryption is three separate problems — in transit (TLS with full certificate verification), at rest (TDE in SQL Server; OS-level disk encryption in PostgreSQL), and at the column level for specific high-sensitivity fields (`pgcrypto` or Always Encrypted) — and hardening a production database is an ongoing discipline tied to change management, not a one-time checklist.""",
 """Encryption is three separate problems — in transit (TLS with full certificate verification), at rest (TDE, with the certificate backed up off-server or your backups are worthless), and at the column level for specific high-sensitivity fields (Always Encrypted) — and hardening a production database is an ongoing discipline tied to change management, not a one-time checklist."""),
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
    print(f'ch08: all {len(REPLACEMENTS)} replacements applied')

main()
