-- Reference schema if you want to run this on MySQL directly instead of
-- letting SQLAlchemy's db.create_all() generate it for you.
-- Matches models.py exactly.

CREATE DATABASE IF NOT EXISTS fixmyglasses CHARACTER SET utf8mb4;
USE fixmyglasses;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(15) NOT NULL UNIQUE,
    name VARCHAR(80) DEFAULT 'Guest User',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE frames (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    color_hex VARCHAR(7) DEFAULT '#A6673A',
    price INT NOT NULL,
    stock INT DEFAULT 0
);

CREATE TABLE campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    subtitle VARCHAR(240),
    bg_gradient VARCHAR(160) DEFAULT 'linear-gradient(135deg,#A6673A,#8A5230)',
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_code VARCHAR(20) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    frame_id INT NOT NULL,
    power_type VARCHAR(20),
    lens_type VARCHAR(30),
    right_eye_power VARCHAR(20),
    left_eye_power VARCHAR(20),
    prescription_file VARCHAR(255),
    lens_price INT DEFAULT 0,
    total_amount INT NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (frame_id) REFERENCES frames(id)
);

CREATE TABLE admin_settings (
    `key` VARCHAR(60) PRIMARY KEY,
    value VARCHAR(255)
);

-- Seed frames
INSERT INTO frames (name, color_hex, price, stock) VALUES
('Aviator Classic', '#A6673A', 1499, 8),
('Round Tortoise', '#6B4A33', 1299, 3),
('Wayfarer Matte', '#211C17', 1199, 0),
('Cat Eye Blush', '#B85C6B', 1699, 12),
('Rimless Steel', '#7C8A93', 1899, 5),
('Square Navy', '#3F5D6B', 1399, 9);

-- Seed campaigns
INSERT INTO campaigns (title, subtitle, bg_gradient, active) VALUES
('Monsoon Sale — Flat 40% Off', 'On all powered lenses, this week only', 'linear-gradient(135deg,#A6673A,#8A5230)', TRUE),
('Buy 1 Get 1 — Sunglasses', 'Every second pair free at checkout', 'linear-gradient(135deg,#3F5D6B,#26414C)', TRUE),
('Progressive Lens Launch', 'Introductory price ₹1799 only', 'linear-gradient(135deg,#4C7A5D,#355C43)', FALSE);

-- Seed admin settings
INSERT INTO admin_settings (`key`, value) VALUES
('qr_enabled', 'true'),
('payment_note', 'Scan with any UPI app');
