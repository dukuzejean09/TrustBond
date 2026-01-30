-- TrustBond Database Initialization
-- This file seeds the database with initial data after schema creation
-- The schema is created by trustbond_complete_schema.sql or Flask-SQLAlchemy

-- Default Admin User seed (created after tables exist)
-- Password: admin123 (must be hashed with werkzeug in application)
-- INSERT INTO police_users (username, email, password_hash, full_name, role, is_active, is_verified)
-- VALUES ('admin', 'admin@trustbond.rw', '<hashed_password>', 'System Admin', 'super_admin', TRUE, TRUE);

-- This file is supplementary - main schema is in trustbond_complete_schema.sql
-- All 33 tables are defined with complete relationships, constraints, and indices
