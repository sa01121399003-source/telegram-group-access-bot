-- Database initialization script for Docker PostgreSQL
-- This file is automatically executed when the PostgreSQL container starts for the first time

-- Create database (if using Docker, the database is created automatically)
-- CREATE DATABASE telegram_bot_db;

-- Connect to the database
\c telegram_bot_db;

-- Create extension for better performance (optional)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the user (if needed)
-- GRANT ALL PRIVILEGES ON DATABASE telegram_bot_db TO telegram_bot_user;

-- The actual table creation is handled by the application's models.py
-- This file can be used for additional setup if needed

-- Insert some default data or settings if required
-- For example, you could set up default group settings here

-- Create indexes for better performance (these will also be created by the app)
-- But having them here ensures they exist from the start

-- You can add any additional setup commands here