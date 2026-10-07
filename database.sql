CREATE DATABASE IF NOT EXISTS machine_health_db;
USE machine_health_db;

CREATE TABLE IF NOT EXISTS department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS machine_type (
    type_id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS machine (
    machine_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_name VARCHAR(100) NOT NULL,
    type_id INT,
    department_id INT,
    installation_date DATE,
    operating_hours INT DEFAULT 0,
    FOREIGN KEY (type_id) REFERENCES machine_type(type_id),
    FOREIGN KEY (department_id) REFERENCES department(department_id)
);

CREATE TABLE IF NOT EXISTS sensor (
    sensor_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    FOREIGN KEY (machine_id) REFERENCES machine(machine_id)
);

CREATE TABLE IF NOT EXISTS sensor_reading (
    reading_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT NOT NULL,
    temperature DECIMAL(6,2),
    vibration DECIMAL(6,2),
    pressure DECIMAL(6,2),
    reading_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensor(sensor_id)
);

CREATE TABLE IF NOT EXISTS technician (
    technician_id INT AUTO_INCREMENT PRIMARY KEY,
    technician_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT NOT NULL,
    technician_id INT,
    maintenance_type VARCHAR(50),
    maintenance_date DATE,
    cost DECIMAL(10,2),
    remarks VARCHAR(500),
    FOREIGN KEY (machine_id) REFERENCES machine(machine_id),
    FOREIGN KEY (technician_id) REFERENCES technician(technician_id)
);

CREATE TABLE IF NOT EXISTS spare_part (
    part_id INT AUTO_INCREMENT PRIMARY KEY,
    part_name VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 0,
    price DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS maintenance_parts (
    maintenance_id INT,
    part_id INT,
    quantity_used INT,
    PRIMARY KEY (maintenance_id, part_id),
    FOREIGN KEY (maintenance_id) REFERENCES maintenance(maintenance_id),
    FOREIGN KEY (part_id) REFERENCES spare_part(part_id)
);

CREATE TABLE IF NOT EXISTS prediction (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT NOT NULL,
    health_status VARCHAR(20),
    failure_probability DECIMAL(5,2),
    predicted_action VARCHAR(255),
    prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machine(machine_id)
);

INSERT INTO department (department_name)
SELECT 'Production' WHERE NOT EXISTS
(SELECT 1 FROM department WHERE department_name='Production');

INSERT INTO department (department_name)
SELECT 'Machining' WHERE NOT EXISTS
(SELECT 1 FROM department WHERE department_name='Machining');

INSERT INTO department (department_name)
SELECT 'Maintenance' WHERE NOT EXISTS
(SELECT 1 FROM department WHERE department_name='Maintenance');

INSERT INTO machine_type (type_name)
SELECT 'CNC' WHERE NOT EXISTS
(SELECT 1 FROM machine_type WHERE type_name='CNC');

INSERT INTO machine_type (type_name)
SELECT 'Lathe' WHERE NOT EXISTS
(SELECT 1 FROM machine_type WHERE type_name='Lathe');

INSERT INTO machine_type (type_name)
SELECT 'Milling' WHERE NOT EXISTS
(SELECT 1 FROM machine_type WHERE type_name='Milling');

INSERT INTO machine_type (type_name)
SELECT 'Drilling' WHERE NOT EXISTS
(SELECT 1 FROM machine_type WHERE type_name='Drilling');

INSERT INTO machine_type (type_name)
SELECT 'Grinding' WHERE NOT EXISTS
(SELECT 1 FROM machine_type WHERE type_name='Grinding');

INSERT INTO machine
(machine_name, type_id, department_id, installation_date, operating_hours)
SELECT 'CNC Machine 01',
       (SELECT type_id FROM machine_type WHERE type_name='CNC'),
       (SELECT department_id FROM department WHERE department_name='Production'),
       '2022-05-10', 8500
WHERE NOT EXISTS (SELECT 1 FROM machine WHERE machine_name='CNC Machine 01');

INSERT INTO machine
(machine_name, type_id, department_id, installation_date, operating_hours)
SELECT 'Lathe Machine 01',
       (SELECT type_id FROM machine_type WHERE type_name='Lathe'),
       (SELECT department_id FROM department WHERE department_name='Machining'),
       '2021-08-15', 10200
WHERE NOT EXISTS (SELECT 1 FROM machine WHERE machine_name='Lathe Machine 01');
