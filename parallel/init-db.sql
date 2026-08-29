SELECT 'CREATE DATABASE parallel_identity_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'parallel_identity_db')\gexec
SELECT 'CREATE DATABASE parallel_context' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'parallel_context')\gexec
SELECT 'CREATE DATABASE projects_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'projects_db')\gexec
SELECT 'CREATE DATABASE pios_workspace' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pios_workspace')\gexec
SELECT 'CREATE DATABASE pios_goals' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pios_goals')\gexec
SELECT 'CREATE DATABASE pios_github' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pios_github')\gexec
