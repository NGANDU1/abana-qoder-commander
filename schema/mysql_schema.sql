-- MySQL schema for: Smart Waste Management System
-- Note: This matches the SQLAlchemy models in app/models.py.
-- In the prototype you can also use SQLite by setting DATABASE_URL=sqlite:///smart_waste.db

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(120) NULL UNIQUE,
  first_name VARCHAR(80) NULL,
  last_name VARCHAR(80) NULL,
  phone_number VARCHAR(30) NULL,
  employee_id VARCHAR(50) NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL,
  last_login_at DATETIME NULL,
  INDEX idx_users_username (username),
  INDEX idx_users_email (email),
  INDEX idx_users_employee_id (employee_id)
);

CREATE TABLE IF NOT EXISTS trucks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL,
  plate_no VARCHAR(30) NOT NULL UNIQUE,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  last_seen_at DATETIME NULL,
  driver_id INT NULL,
  CONSTRAINT fk_trucks_driver FOREIGN KEY (driver_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bin_code VARCHAR(30) NOT NULL UNIQUE,
  location_name VARCHAR(140) NOT NULL,
  area VARCHAR(80) NULL,
  latitude DOUBLE NOT NULL,
  longitude DOUBLE NOT NULL,
  waste_type VARCHAR(30) NOT NULL DEFAULT 'General',
  fill_level INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'Empty',
  last_updated_at DATETIME NOT NULL,
  INDEX idx_bins_code (bin_code),
  INDEX idx_bins_area (area)
);

CREATE TABLE IF NOT EXISTS sensor_readings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bin_id INT NOT NULL,
  fill_level INT NOT NULL,
  status VARCHAR(20) NOT NULL,
  source VARCHAR(20) NOT NULL DEFAULT 'sim',
  recorded_at DATETIME NOT NULL,
  INDEX idx_readings_bin_id (bin_id),
  INDEX idx_readings_recorded_at (recorded_at),
  CONSTRAINT fk_readings_bin FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bin_id INT NOT NULL,
  level VARCHAR(20) NOT NULL,
  message VARCHAR(255) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL,
  resolved_at DATETIME NULL,
  INDEX idx_alerts_bin_id (bin_id),
  INDEX idx_alerts_active (is_active),
  INDEX idx_alerts_created (created_at),
  CONSTRAINT fk_alerts_bin FOREIGN KEY (bin_id) REFERENCES bins(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS routes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  route_code VARCHAR(30) NOT NULL UNIQUE,
  date_for DATE NOT NULL,
  algorithm VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'planned',
  total_distance_km DOUBLE NULL,
  created_at DATETIME NOT NULL,
  created_by_id INT NULL,
  truck_id INT NULL,
  driver_id INT NULL,
  INDEX idx_routes_code (route_code),
  CONSTRAINT fk_routes_created_by FOREIGN KEY (created_by_id) REFERENCES users(id),
  CONSTRAINT fk_routes_truck FOREIGN KEY (truck_id) REFERENCES trucks(id),
  CONSTRAINT fk_routes_driver FOREIGN KEY (driver_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS route_stops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  route_id INT NOT NULL,
  seq INT NOT NULL,
  bin_id INT NOT NULL,
  distance_from_prev_km DOUBLE NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  collected_at DATETIME NULL,
  INDEX idx_route_stops_route_id (route_id),
  CONSTRAINT fk_route_stops_route FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
  CONSTRAINT fk_route_stops_bin FOREIGN KEY (bin_id) REFERENCES bins(id)
);

CREATE TABLE IF NOT EXISTS collection_events (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bin_id INT NOT NULL,
  route_id INT NULL,
  collector_id INT NULL,
  before_fill_level INT NOT NULL,
  notes VARCHAR(255) NULL,
  collected_at DATETIME NOT NULL,
  INDEX idx_events_bin_id (bin_id),
  INDEX idx_events_route_id (route_id),
  INDEX idx_events_collector_id (collector_id),
  INDEX idx_events_collected_at (collected_at),
  CONSTRAINT fk_events_bin FOREIGN KEY (bin_id) REFERENCES bins(id),
  CONSTRAINT fk_events_route FOREIGN KEY (route_id) REFERENCES routes(id),
  CONSTRAINT fk_events_collector FOREIGN KEY (collector_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notification_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  alert_id INT NULL,
  channel VARCHAR(20) NOT NULL,
  recipient VARCHAR(120) NULL,
  message VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL,
  INDEX idx_notif_alert_id (alert_id),
  INDEX idx_notif_created_at (created_at),
  CONSTRAINT fk_notif_alert FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

CREATE TABLE IF NOT EXISTS generated_reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(140) NOT NULL,
  report_type VARCHAR(30) NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  content_json TEXT NOT NULL,
  created_at DATETIME NOT NULL,
  created_by_id INT NULL,
  INDEX idx_reports_created_at (created_at),
  INDEX idx_reports_created_by (created_by_id),
  CONSTRAINT fk_reports_created_by FOREIGN KEY (created_by_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bin_reports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  bin_id INT NOT NULL,
  reporter_id INT NULL,
  reported_level INT NULL,
  message VARCHAR(255) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL,
  reviewed_at DATETIME NULL,
  INDEX idx_reports_bin_id (bin_id),
  INDEX idx_reports_reporter_id (reporter_id),
  INDEX idx_reports_status (status),
  INDEX idx_reports_created_at (created_at),
  CONSTRAINT fk_bin_reports_bin FOREIGN KEY (bin_id) REFERENCES bins(id),
  CONSTRAINT fk_bin_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id)
);
