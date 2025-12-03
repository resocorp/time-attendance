-- ZK Attendance Pro - Initial Database Schema
-- Run this in Supabase SQL Editor

-- =============================================
-- EMPLOYEES TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pin VARCHAR(20) NOT NULL,         -- Employee PIN
    employee_name VARCHAR(100),       -- Denormalized for quick access
    department VARCHAR(100),          -- Denormalized for quick access
    device_sn VARCHAR(50) NOT NULL,   -- Device serial number
    punch_time TIMESTAMPTZ NOT NULL,  -- When the punch occurred
    punch_type VARCHAR(20),           -- CHECK_IN, CHECK_OUT, BREAK_OUT, etc.
    verify_method VARCHAR(20),        -- FINGERPRINT, FACE, CARD, PASSWORD
    work_code VARCHAR(20),
    raw_data JSONB,                   -- Original data from device
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key to employees (optional - allows logs for unknown PINs)
    CONSTRAINT fk_employee FOREIGN KEY (pin) REFERENCES employees(pin) ON DELETE SET NULL
);

-- Remove the foreign key constraint to allow logs for unregistered employees
ALTER TABLE attendance_logs DROP CONSTRAINT IF EXISTS fk_employee;

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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_sn VARCHAR(50) NOT NULL REFERENCES devices(serial_number),
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
-- WORK SCHEDULES TABLE (for late/early detection)
-- =============================================
CREATE TABLE IF NOT EXISTS work_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- For now, allow all operations (we'll add proper policies with auth later)
-- These policies allow the service role to do everything
CREATE POLICY "Allow all for service role" ON employees FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON attendance_logs FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON devices FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON device_commands FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON work_schedules FOR ALL USING (true);

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
