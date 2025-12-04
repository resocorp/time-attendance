-- ZK Attendance Pro - Complete Database Schema
-- Run this in Supabase SQL Editor

-- =============================================
-- EMPLOYEES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS employees (
    id BIGSERIAL PRIMARY KEY,
    pin VARCHAR(20) UNIQUE NOT NULL,  -- Device PIN (unique identifier)
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    card_number VARCHAR(50),          -- RFID card number
    is_active BOOLEAN DEFAULT true,
    hire_date DATE,
    photo_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast PIN lookups
CREATE INDEX IF NOT EXISTS idx_employees_pin ON employees(pin);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);

-- =============================================
-- ATTENDANCE LOGS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS attendance_logs (
    id BIGSERIAL PRIMARY KEY,
    pin VARCHAR(20) NOT NULL,         -- Employee PIN
    employee_name VARCHAR(100),       -- Denormalized for quick access
    department VARCHAR(100),          -- Denormalized for quick access
    device_sn VARCHAR(50),            -- Device serial number
    punch_time TIMESTAMPTZ NOT NULL,  -- When the punch occurred
    punch_type VARCHAR(20),           -- CHECK_IN, CHECK_OUT, BREAK_OUT, etc.
    verify_method VARCHAR(20),        -- FINGERPRINT, FACE, CARD, PASSWORD
    work_code VARCHAR(20),
    raw_data JSONB,                   -- Original data from device
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_attendance_pin ON attendance_logs(pin);
CREATE INDEX IF NOT EXISTS idx_attendance_punch_time ON attendance_logs(punch_time DESC);
CREATE INDEX IF NOT EXISTS idx_attendance_device ON attendance_logs(device_sn);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_logs(DATE(punch_time));

-- =============================================
-- DEVICES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS devices (
    serial_number VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    location VARCHAR(200),
    ip_address VARCHAR(45),
    firmware_version VARCHAR(50),
    model VARCHAR(50),
    status VARCHAR(20) DEFAULT 'offline',  -- online, offline, error
    last_seen TIMESTAMPTZ,
    config JSONB,                     -- Device configuration
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- DEVICE COMMANDS TABLE (for queued commands)
-- =============================================
CREATE TABLE IF NOT EXISTS device_commands (
    id BIGSERIAL PRIMARY KEY,
    device_sn VARCHAR(50) NOT NULL,
    command TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, completed, failed
    result TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_commands_device ON device_commands(device_sn);
CREATE INDEX IF NOT EXISTS idx_commands_status ON device_commands(status);

-- =============================================
-- PUNCH TIME WINDOWS TABLE (for automatic punch type)
-- =============================================
CREATE TABLE IF NOT EXISTS punch_time_windows (
    id BIGSERIAL PRIMARY KEY,
    punch_type VARCHAR(20) NOT NULL,      -- CHECK_IN, CHECK_OUT, BREAK_OUT, etc.
    start_time VARCHAR(10) NOT NULL,      -- e.g., "06:00"
    end_time VARCHAR(10) NOT NULL,        -- e.g., "10:00"
    days_of_week VARCHAR(20) DEFAULT '0,1,2,3,4,5,6',  -- 0=Mon, 6=Sun
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- SYSTEM SETTINGS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- USERS TABLE (for authentication)
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100),
    department VARCHAR(100),
    employee_pin VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =============================================
-- ROLES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',       -- Array of permission strings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- USER-ROLE MAPPING TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- =============================================
-- AUDIT LOGS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);

-- =============================================
-- WORK SCHEDULES TABLE (for late/early detection)
-- =============================================
CREATE TABLE IF NOT EXISTS work_schedules (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,       -- e.g., "Standard", "Night Shift"
    work_start TIME NOT NULL,         -- e.g., 09:00
    work_end TIME NOT NULL,           -- e.g., 17:00
    grace_period_minutes INT DEFAULT 15,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default schedule
INSERT INTO work_schedules (name, work_start, work_end, is_default)
VALUES ('Standard', '09:00', '17:00', true)
ON CONFLICT DO NOTHING;

-- =============================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================
-- Enable RLS on all tables
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE punch_time_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (we'll add proper policies with auth later)
-- These policies allow the service role to do everything
CREATE POLICY "Allow all for service role" ON employees FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON attendance_logs FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON devices FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON device_commands FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON work_schedules FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON punch_time_windows FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON system_settings FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON users FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON roles FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON user_roles FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON audit_logs FOR ALL USING (true);

-- =============================================
-- FUNCTIONS
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_devices_updated_at
    BEFORE UPDATE ON devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_punch_time_windows_updated_at
    BEFORE UPDATE ON punch_time_windows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =============================================
-- VIEWS FOR REPORTING
-- =============================================

-- Daily attendance summary view
CREATE OR REPLACE VIEW daily_attendance_summary AS
SELECT 
    DATE(punch_time) as date,
    COUNT(DISTINCT pin) as unique_employees,
    COUNT(*) as total_punches,
    COUNT(*) FILTER (WHERE punch_type = 'CHECK_IN') as check_ins,
    COUNT(*) FILTER (WHERE punch_type = 'CHECK_OUT') as check_outs
FROM attendance_logs
GROUP BY DATE(punch_time)
ORDER BY date DESC;

-- Employee attendance view (for dashboard)
CREATE OR REPLACE VIEW employee_daily_attendance AS
SELECT 
    DATE(punch_time) as date,
    pin,
    MAX(employee_name) as employee_name,
    MAX(department) as department,
    MIN(punch_time) FILTER (WHERE punch_type = 'CHECK_IN') as first_in,
    MAX(punch_time) FILTER (WHERE punch_type = 'CHECK_OUT') as last_out,
    COUNT(*) as total_punches
FROM attendance_logs
GROUP BY DATE(punch_time), pin
ORDER BY date DESC, pin;
