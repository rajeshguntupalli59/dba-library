#!/usr/bin/env python3
"""Apply ch33 phrase-level rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch33-zero-trust.html'
C = 'bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs'
def code(x): return '<code class="%s">%s</code>' % (C, x)

REPLACEMENTS = [
("Both PostgreSQL and SQL Server offer multiple authentication mechanisms, and the choice matters enormously in a zero-trust context.",
 "SQL Server offers multiple authentication mechanisms, and the choice matters enormously in a zero-trust context."),

("<strong class=\"text-white\">PostgreSQL Authentication</strong>",
 "<strong class=\"text-white\">Hardening SQL Server Authentication</strong>"),

("""PostgreSQL's authentication is controlled through the %s file, which defines rules for how each connection is authenticated based on connection type, database, user, and source address. In a zero-trust environment, the configuration should lean heavily toward certificate-based authentication (via %s method) or SCRAM-SHA-256 rather than plaintext passwords (%s) or the insecure %s method.""" % (code('pg_hba.conf'), code('cert'), code('password'), code('md5')),
 """SQL Server has no pg_hba equivalent — authentication policy lives in the logins themselves and the protocols the instance listens on. The zero-trust baseline: disable the %s account and never use it for applications; require Windows or Microsoft Entra authentication for humans; restrict SQL logins to service accounts with long generated passwords stored in a secrets manager; and disable unused protocols and the Browser service so the attack surface is just TCP/IP on the trusted interface.""" % code('sa')),

("A properly locked-down %s for a production environment looks like this:" % code('pg_hba.conf'),
 "A hardened login baseline for a production environment looks like this:"),

("""<code># Reject all by default
# local connections for the postgres superuser only, using peer
local   all             postgres                                peer

# Application accounts via SSL with certificate validation
hostssl appdb           appuser         10.0.10.0/24            scram-sha-256

# Reject everything else
host    all             all             0.0.0.0/0               reject</code>""",
 """<code>-- Disable sa; it should never authenticate in production
ALTER LOGIN sa DISABLE;

-- Least-privilege service login: no server roles, explicit grants only
CREATE LOGIN etl_service WITH PASSWORD = N'&lt;from secrets manager&gt;';
-- then grant CONNECT + database role membership per database; never sysadmin

-- Audit which logins can still authenticate at the server level
SELECT name, type_desc, is_disabled
FROM sys.server_principals
WHERE type_desc IN ('SQL_LOGIN', 'WINDOWS_LOGIN', 'EXTERNAL_LOGIN')
  AND is_disabled = 0
ORDER BY name;</code>"""),

("""The %s method requires that the connection use TLS — without it, the connection is rejected before a password is even asked for. Combined with SCRAM-SHA-256, this means passwords are never sent in plaintext and are verified using a challenge-response mechanism that prevents replay attacks.""" % code('hostssl'),
 """Requiring TLS plus strong authentication means credentials are never sent in plaintext. Combined with %s on the instance, every login — human or service — travels over an encrypted channel before credentials are even presented.""" % code('Force Encryption')),

("""For service accounts in automated systems, certificate authentication eliminates passwords entirely. The database validates the client certificate's CN (Common Name) against the username being claimed:""",
 """For service accounts in automated systems, certificate-based logins or Microsoft Entra managed identities eliminate passwords entirely — the database trusts the identity provider's token, not a shared secret stored in a config file:"""),

("""<code>hostssl appdb           etl_service     10.0.20.0/24            cert clientcert=verify-full</code>""",
 """<code>-- Managed identity: no password exists to steal or rotate
CREATE USER [myapp-identity] FROM EXTERNAL PROVIDER;
ALTER ROLE db_app_readwrite ADD MEMBER [myapp-identity];</code>"""),

("""Multi-factor authentication (MFA) deserves specific mention here. For human DBA accounts connecting to production databases, MFA is non-negotiable in a zero-trust model. PostgreSQL does not implement MFA natively, but it can be layered in through PAM (Pluggable Authentication Modules) on Linux, which allows integration with RADIUS-based MFA systems, Duo Security, or TOTP mechanisms. SQL Server integrates with Azure AD Conditional Access policies that enforce MFA before a token is issued, which means MFA enforcement happens at the identity provider layer rather than at the database layer — the right place for it.""",
 """Multi-factor authentication (MFA) deserves specific mention here. For human DBA accounts connecting to production databases, MFA is non-negotiable in a zero-trust model. SQL Server integrates with Microsoft Entra Conditional Access policies that enforce MFA before a token is issued — MFA enforcement happens at the identity provider layer rather than at the database layer, the right place for it. For on-premises estates, Windows Authentication with smart cards or Windows Hello provides the second factor without any database-side MFA plumbing."""),

("Both PostgreSQL and SQL Server implement role-based access control (RBAC).",
 "SQL Server implements role-based access control (RBAC)."),

("In PostgreSQL, roles and users are unified concepts. A well-structured role model for an application database looks like this:",
 "In SQL Server, server logins, database users, and database roles are distinct concepts. A well-structured role model for an application database looks like this:"),

("PostgreSQL's Row-Level Security (RLS) allows you to define policies that filter rows based on the current user context.",
 "SQL Server's Row-Level Security (RLS) allows you to define policies that filter rows based on the current user context."),

("""PostgreSQL enforces TLS through %s in %s and the use of %s entries in %s. Setting %s in %s ensures that outdated protocol versions like TLS 1.0 and TLS 1.1 are rejected. TLS 1.3 is recommended where client library support allows.""" % (code('ssl = on'), code('postgresql.conf'), code('hostssl'), code('pg_hba.conf'), code("ssl_min_protocol_version = 'TLSv1.2'"), code('postgresql.conf')),
 """SQL Server enforces TLS through the %s setting in SQL Server Configuration Manager, where a server certificate is bound to the instance. Clients request encryption with %s and %s; the minimum TLS version is set via Schannel registry settings on Windows, or through the portal's minimum-TLS-version setting (1.2 or higher) on Azure SQL Database. TLS 1.3 is recommended where client library support allows.""" % (code('Force Encryption'), code('Encrypt=yes'), code('TrustServerCertificate=no'))),

("Security groups or firewall rules allow inbound traffic only on the database port (5432 for PostgreSQL, 1433 for SQL Server) from specific application subnets or instance IDs.",
 "Security groups or firewall rules allow inbound traffic only on the database port (1433) from specific application subnets or instance IDs."),

("Vault connects to PostgreSQL or SQL Server using a privileged account,",
 "Vault connects to SQL Server using a privileged account,"),

("On the PostgreSQL side, Vault's management role needs permission to create and drop roles:",
 "On the SQL Server side, Vault's management login needs permission to create and drop logins:"),

("AWS IAM authentication for RDS PostgreSQL and Aurora takes this further by eliminating passwords entirely for IAM-aware applications.",
 "AWS IAM authentication for RDS for SQL Server takes this further by eliminating passwords entirely for IAM-aware applications."),

("<strong class=\"text-white\">PostgreSQL Audit Logging</strong>",
 "<strong class=\"text-white\">Configuring SQL Server Audit</strong>"),

("""PostgreSQL's built-in logging parameters capture many of these events, but %s — an open-source extension — provides structured, role-aware audit logging that is designed specifically for compliance and security use cases.""" % code('pgaudit'),
 """SQL Server Audit captures server- and database-level events to a file, the Security log, or the Application log. A production baseline audits failed logins, permission changes, and DDL — enough to reconstruct who did what, without drowning in row-level noise:"""),

("""<code>-- Install pgaudit (after loading the shared library in postgresql.conf)
-- shared_preload_libraries = 'pgaudit'

-- Configure audit logging at the session level
SET pgaudit.log = 'ddl, role, read, write';

-- Or configure globally in postgresql.conf:
-- pgaudit.log = 'ddl, role'
-- pgaudit.log_relation = on
-- pgaudit.log_parameter = on

-- Check current pgaudit configuration
SHOW pgaudit.log;
SHOW pgaudit.log_relation;</code>""",
 """<code>-- Server-level audit: failed logins and permission changes
CREATE SERVER AUDIT ProdAudit
TO FILE (FILEPATH = N'C:\\Audit\\', MAXSIZE = 100 MB, MAX_ROLLOVER_FILES = 20)
WITH (ON_FAILURE = FAIL_OPERATION);
CREATE SERVER AUDIT SPECIFICATION ProdServerSpec
FOR SERVER AUDIT ProdAudit
ADD (FAILED_LOGIN_GROUP),
ADD (SERVER_PERMISSION_CHANGE_GROUP);
ALTER SERVER AUDIT ProdAudit WITH (STATE = ON);

-- Database-level audit: DDL and permission changes
CREATE DATABASE AUDIT SPECIFICATION ProdDbSpec
FOR SERVER AUDIT ProdAudit
ADD (SCHEMA_OBJECT_CHANGE_GROUP),
ADD (DATABASE_PERMISSION_CHANGE_GROUP)
WITH (STATE = ON);</code>"""),

("PostgreSQL's standard logging parameters, independent of pgaudit, should also be configured:",
 "The error log complements the audit trail — make sure login auditing captures at least failed logins, and that ERRORLOG files are retained:"),

("""<code>log_connections = on
log_disconnections = on
log_failed_connections = on
log_statement = 'ddl'         -- at minimum; 'all' for high-security environments
log_duration = on
log_min_duration_statement = 1000  -- log slow queries (over 1 second)
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '</code>""",
 """<code>-- SSMS: Server Properties &gt; Security &gt; Login auditing = "Failed logins only" (minimum)
-- Retain history: cycle the error log on a schedule and keep 30+ archives
EXEC sp_cycle_errorlog;
-- Verify the audit is actually running
SELECT name, status_desc FROM sys.dm_server_audit_status;</code>"""),

("Every connection to the database must authenticate using strong mechanisms — SCRAM-SHA-256 or certificate-based authentication for PostgreSQL, Kerberos or Azure AD with MFA for SQL Server — regardless of where the connection originates.",
 "Every connection to the database must authenticate using strong mechanisms — Kerberos or Microsoft Entra with MFA for humans, certificate-based logins or managed identities for services — regardless of where the connection originates."),
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
    print(f'ch33: all {len(REPLACEMENTS)} replacements applied')

main()
