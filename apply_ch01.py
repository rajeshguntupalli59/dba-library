#!/usr/bin/env python3
"""Apply ch01 prose rewrites. Fails loudly on any non-unique match."""
import sys

PATH = '/home/hatch/workspace/dba-library/book/ch01-introduction.html'

REPLACEMENTS = [
# --- h3 heading ---
("""PostgreSQL and SQL Server — Two Platforms, One Discipline""",
 """SQL Server — One Engine, One Discipline"""),

# --- intro paragraph ---
("""It explains why relational databases remain the backbone of modern software systems, how PostgreSQL and SQL Server each earned their place in the industry, and what it means to truly master a database platform rather than simply know how to write queries. By the end of this chapter, you will understand the philosophy behind this book, the type of thinking that separates a competent DBA from an exceptional one, and why comparing two world-class database systems side by side is one of the fastest ways to deepen your understanding of both.""",
 """It explains why relational databases remain the backbone of modern software systems, how SQL Server earned its place as the enterprise workhorse of the industry, and what it means to truly master a database platform rather than simply know how to write queries. By the end of this chapter, you will understand the philosophy behind this book, the type of thinking that separates a competent DBA from an exceptional one, and why going deep on a single world-class engine — its internals, its failure modes, its operational rhythms — is one of the fastest ways to deepen your understanding of databases in general."""),

# --- "not a book that dismisses other technologies" ---
("""and PostgreSQL itself has grown to handle many of them natively.""",
 """and the SQL Server platform itself has grown to cover many of them — JSON support, graph tables, columnstore analytics, and machine learning services all live inside the engine today."""),

# --- the whole "two platforms" section body (5 paras -> 4) ---
("""<p class="text-gray-300 leading-relaxed">PostgreSQL and Microsoft SQL Server represent two very different paths to the same destination: a production-grade relational database that organizations can stake their business on.</p>

<p class="text-gray-300 leading-relaxed">PostgreSQL began as a university research project at UC Berkeley in the 1980s, grew into an open-source community effort, and has since become one of the most feature-rich and standards-compliant relational databases available. It runs on Linux, macOS, Windows, and virtually every cloud platform. Its license costs nothing. Its source code is open to inspection. Its extension ecosystem — PostGIS for geospatial data, TimescaleDB for time-series, pgvector for machine learning embeddings — is extraordinary. PostgreSQL's community is global and highly active, releasing a major version every year. For these reasons, it has become the default choice for startups, SaaS companies, and an increasing number of enterprises that want power without vendor lock-in.</p>

<p class="text-gray-300 leading-relaxed">SQL Server, on the other hand, is a commercial product built by Microsoft, first released in 1989, and deeply integrated with the Windows and Azure ecosystems. It has historically dominated enterprise environments in finance, healthcare, and manufacturing — industries where long-standing vendor relationships, Active Directory integration, and Microsoft's support infrastructure carry significant weight. SQL Server's tooling, particularly SQL Server Management Studio (SSMS) and the broader Business Intelligence stack, has long been a reference point for database administration UX. In recent years, SQL Server has expanded to Linux and containers, and Azure SQL Database has made it a viable cloud-native platform.</p>

<p class="text-gray-300 leading-relaxed">The two systems share more than they differ. Both implement SQL-92 and much of SQL:2016. Both support transactions, foreign keys, triggers, views, stored procedures, partitioning, replication, and full-text search. Both have sophisticated query optimizers, rich monitoring infrastructure, and a mature ecosystem of tools. But their syntax diverges in important ways, their internal architectures make different trade-offs, and the communities around them have developed different cultures of best practice.</p>

<p class="text-gray-300 leading-relaxed">This book teaches both platforms in parallel because that comparison is itself a learning tool. When you see how PostgreSQL and SQL Server solve the same problem differently, you stop treating either system's approach as the only natural way. You start seeing the *design decisions* underneath the syntax, and that is when real database mastery begins.</p>""",
 """<p class="text-gray-300 leading-relaxed">Microsoft SQL Server represents decades of engineering aimed at a single destination: a production-grade relational database that organizations can stake their business on.</p>

<p class="text-gray-300 leading-relaxed">SQL Server began in 1989 as a collaboration between Microsoft, Ashton-Tate, and Sybase, and grew into the database backbone of the enterprise world. It has historically dominated environments in finance, healthcare, manufacturing, and government — industries where long-standing vendor relationships, Active Directory integration, and Microsoft's support infrastructure carry significant weight. In recent years it has expanded well beyond its Windows roots: it runs on Linux, in Docker containers, at the edge, and as a fully managed cloud service in Azure SQL Database.</p>

<p class="text-gray-300 leading-relaxed">SQL Server's tooling, particularly SQL Server Management Studio (SSMS) and Azure Data Studio, has long been a reference point for database administration UX. Beneath the tooling sits an unusually transparent engine: the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys</code> schema of catalog views and dynamic management views (DMVs), Query Store's flight-recorder history of plan performance, and Extended Events' lightweight tracing give working DBAs a clear window into internals that many platforms keep opaque. The community culture of best practice is equally deep — from Ola Hallengren's maintenance solution to shared runbooks for corruption recovery — and this book draws on it throughout.</p>

<p class="text-gray-300 leading-relaxed">This book teaches SQL Server in depth because depth is itself a learning tool. When you see how one world-class engine solves hard problems — concurrency without blocking readers, recovery without data loss, scale without downtime — you stop treating any single approach as the only natural way. You start seeing the *design decisions* underneath the syntax, and that is when real database mastery begins.</p>"""),

# --- "How to Read This Book": examples paragraph ---
("""Every chapter that covers a technical operation includes SQL examples for both PostgreSQL and SQL Server. This is a firm commitment throughout all 40 chapters. The examples are not toy demonstrations. They use realistic table names, realistic data volumes, and realistic operational contexts. Where the two platforms differ meaningfully — in syntax, in behavior, or in recommended practice — those differences are explained rather than glossed over.""",
 """Every chapter that covers a technical operation includes T-SQL examples written for SQL Server. This is a firm commitment throughout all 40 chapters. The examples are not toy demonstrations. They use realistic table names, realistic data volumes, and realistic operational contexts. Where SQL Server offers more than one way to do something — in syntax, in behavior, or in recommended practice — the trade-offs are explained rather than glossed over."""),

# --- "How to Read This Book": lab setup paragraph ---
("""To get the most from this book, you should have access to at least one of the two databases. A local installation of PostgreSQL is free and takes five minutes to set up. SQL Server has a free Developer Edition and Express Edition that are fully functional for learning. Cloud options — Amazon RDS, Azure Database, Google Cloud SQL — all provide managed instances you can provision in minutes.""",
 """To get the most from this book, you should have access to a SQL Server instance. SQL Server has a free Developer Edition and Express Edition that are fully functional for learning, and an official container image you can run with a single <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">docker run</code> command. Cloud options — Azure SQL Database, Amazon RDS for SQL Server, Google Cloud SQL for SQL Server — all provide managed instances you can provision in minutes."""),

# --- "A First Look": metadata paragraph ---
("""Notice the difference in approach immediately. PostgreSQL exposes much of its metadata through views in the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_catalog</code> schema and through built-in functions like <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_database_size()</code>. SQL Server surfaces the same information through the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys</code> schema, which contains dynamic management views (DMVs) and catalog views that will appear throughout this book. Both systems give you the information you need — they just ask you to look in different places.""",
 """Notice the approach immediately. SQL Server surfaces instance and database metadata through the <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys</code> schema, which contains dynamic management views (DMVs) and catalog views that will appear throughout this book. The <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys</code> schema is the DBA's primary window into the engine — version information, database states, file layouts, session activity — all queryable with ordinary T-SQL, no special tooling required."""),

# --- "A First Look": pulse monitor paragraph ---
("""<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">pg_stat_activity</code> in PostgreSQL and <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_sessions</code> combined with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code> in SQL Server are two views you will return to constantly. They are the pulse monitors of a running database instance.""",
 """<code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_sessions</code> combined with <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-xs">sys.dm_exec_requests</code> are views you will return to constantly. They are the pulse monitors of a running SQL Server instance — who is connected, what each session is running, how long it has been running, and what it is waiting on."""),

# --- takeaway: side-by-side ---
("""PostgreSQL and SQL Server are both world-class platforms with distinct histories, ecosystems, and communities; studying them side by side reveals the design decisions that underlie their surface differences and accelerates mastery of both.""",
 """SQL Server is a world-class platform with decades of enterprise history and a deep ecosystem; studying one engine in depth — its internals, its trade-offs, its failure modes — reveals the design decisions beneath the syntax and accelerates true mastery."""),

# --- takeaway: examples/metadata ---
("""Every SQL example in this book is shown for both PostgreSQL and SQL Server using correct, platform-native syntax; metadata lives in `pg_catalog` and `information_schema` in PostgreSQL, and in `sys.*` views and DMVs in SQL Server.""",
 """Every example in this book is written in T-SQL for SQL Server; instance and database metadata lives in the `sys` schema — catalog views for static metadata, DMVs for live engine state."""),
]

def main():
    text = open(PATH).read()
    for i, (old, new) in enumerate(REPLACEMENTS):
        count = text.count(old)
        if count != 1:
            print(f'FAIL replacement {i}: found {count} occurrences')
            sys.exit(1)
        text = text.replace(old, new, 1)
    open(PATH, 'w').write(text)
    print(f'ch01: all {len(REPLACEMENTS)} replacements applied')

main()
