DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Role;
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS User_Access;
DROP TABLE IF EXISTS Tenant;
DROP TABLE IF EXISTS Tenant_Reference;
DROP TABLE IF EXISTS Apartments;
DROP TABLE IF EXISTS Lease;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Maintenance_Request;
DROP TABLE IF EXISTS Complaints;
DROP TABLE IF EXISTS Employee;
DROP TABLE IF EXISTS Maintenance_Assignment;
DROP TABLE IF EXISTS Report;
DROP TABLE IF EXISTS Buildings;


CREATE TABLE IF NOT EXISTS Location (
    city_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name varchar(70)
);


CREATE TABLE IF NOT EXISTS Role (
    role_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name varchar(35)
);


CREATE TABLE IF NOT EXISTS User (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id  int,
    first_name	VARCHAR(80),
    surname	VARCHAR(80),
    FOREIGN KEY (city_id) REFERENCES Location(city_id)
);



CREATE TABLE IF NOT EXISTS User_Access (
    user_id   int,
    password_hash  VARCHAR(255),
    role_id	int,
    email	VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (role_id) REFERENCES Role(role_id)

);




CREATE TABLE IF NOT EXISTS Tenant (
    tenant_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  int,
    ni_number	VARCHAR(20),
    telephone	int,
    occupation VARCHAR(120),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

ALTER TABLE Tenant ADD COLUMN apartment_type VARCHAR(50);
ALTER TABLE Tenant ADD COLUMN lease_period VARCHAR(50);


CREATE TABLE IF NOT EXISTS Tenant_Reference (
    reference_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id  int,
    reference	VARCHAR(255),
    reference_email VARCHAR(255),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)

);



CREATE TABLE IF NOT EXISTS Apartments
 (
    apartment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id	int,
    building_id int,
    num_rooms	int,
    type 	TEXT CHECK(type IN ('Studio', 'Apartment', 'Penthouse')),
    occupancy_status 	TEXT CHECK(occupancy_status IN ('Occupied', 'Vacant', 'Unavailable')),
    FOREIGN KEY (city_id) REFERENCES Location(city_id),
    FOREIGN KEY (building_id) REFERENCES Buildings(building_id));



CREATE TABLE IF NOT EXISTS Buildings
 (
    building_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id	int,
    street VARCHAR(70),
    postcode VARCHAR(10),
    FOREIGN KEY (city_id) REFERENCES Location(city_id));


CREATE TABLE IF NOT EXISTS Lease
 (
    lease_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id 	int,
    tenant_id 	int,
    start_date	DATE,
    end_date	DATE,
    deposit	REAL,
    early_termination_fee	REAL,
    Agreed_rent	REAL,
    FOREIGN KEY (apartment_id) REFERENCES Apartments(apartment_id),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)

);


CREATE TABLE IF NOT EXISTS Payment
 (
    payment_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id 	int,
    due_date	DATE,
    payment_date	DATE,
    amount	REAl,
    Is_late	BOOLEAN,
    FOREIGN KEY (lease_id) REFERENCES Lease(lease_id)


);



CREATE TABLE IF NOT EXISTS Maintenance_Request
 (
    request_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id 	int,
    tenant_id 	int,
    issue	VARCHAR(255),
    description	VARCHAR(255),
    Maintenance_status TEXT DEFAULT 'Open' CHECK(Maintenance_status IN ('Open','Approved','In Progress', 'Resolved', 'Denied')),
    priority TEXT check(priority IN ('Low', 'Medium', 'High')),
    created_date	DATETIME,
    resolved_date	DATETIME,
    repair_time INTEGER,     
    repair_cost REAL,       
    notes	VARCHAR(255),
    FOREIGN KEY (apartment_id) REFERENCES Apartments(apartment_id),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id));


CREATE TABLE Complaints
 (
  
    complaint_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    description	VARCHAR(255),
    date_submitted	DATE,
    tenant_id 	int,
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)


);





CREATE TABLE Employee
 (
  
    employee_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id 	int,
    Full_name	VARCHAR(120),
    salary	REAL,
    hire_date	DATE,
    FOREIGN KEY (request_id) REFERENCES Maintenance_Request(request_id)


);


CREATE TABLE Maintenance_Assignment
 (
  
    assignment_id 	INTEGER PRIMARY KEY AUTOINCREMENT ,
    request_id 	int ,
    employee_id 	int ,
    assigned_date	DATETIME ,
    is_current	BOOLEAN,
    FOREIGN KEY (request_id) REFERENCES Maintenance_Request(request_id),
    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)



);






CREATE TABLE Report
 (
  
    report_id 	INTEGER PRIMARY KEY AUTOINCREMENT ,
    apartment_id 	int ,
    payment_id  	int ,
    date_created	DATETIME ,
    data_from_date	DATE ,
    report_type TEXT CHECK(report_type IN ('Financial', 'Occupancy', 'Maintenance')),    
    data_to_date	DATE ,
    FOREIGN KEY (apartment_id) REFERENCES Apartments(apartment_id),
    FOREIGN KEY (payment_id) REFERENCES Payment(payment_id)



);

-- ========================================================
-- 1. LOOKUP DATA
-- ========================================================
INSERT INTO Role (role_name) VALUES 
('Front-desk Staff'), ('Finance Manager'), ('Maintenance Staff'), 
('Administrators'), ('Manager'), ('Tenant');

INSERT INTO Location (city_name) VALUES 
('Bristol'), ('Cardiff'), ('London'), ('Manchester');

-- ========================================================
-- 2. USERS & ACCESS (1:1 BALANCE - TOTAL 20 USERS)
-- ========================================================
INSERT INTO User (user_id, city_id, first_name, surname) VALUES
(1, 1, 'Ahmed', 'Ali'), (2, 2, 'Sophie', 'Taylor'), (3, 3, 'Mohamed', 'Ibrahim'),
(4, 4, 'Lucas', 'Martin'), (5, 1, 'Zainab', 'Hassan'), (6, 2, 'Oliver', 'Jones'),
(7, 3, 'Aisha', 'Khan'), (8, 4, 'Noah', 'Clark'), 
(9, 1, 'System', 'Admin'),   -- Bristol Admin (1234)
(10, 2, 'Area', 'Manager'),  -- Manager (123)
(11, 3, 'Test', 'Tenant'),   -- Tenant (12)
(12, 1, 'Emily', 'Cook'), (13, 1, 'Jack', 'Morgan'), (14, 1, 'Mark', 'Spencer'),
(15, 2, 'David', 'Wilson'), (16, 2, 'Lily', 'Davies'), (17, 3, 'Maya', 'Patel'),
(18, 4, 'Sarah', 'Jenkins'), (19, 4, 'William', 'Scott'), (20, 1, 'Liam', 'Davies');

INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES
(1, 'hash1', 6, 'ahmed@tenant.com'), (2, 'hash2', 6, 'sophie@tenant.com'),
(3, 'hash3', 6, 'mohamed@tenant.com'), (4, 'hash4', 5, 'lucas@manager.com'),
(5, 'hash5', 6, 'zainab@tenant.com'), (6, 'hash6', 1, 'oliver@frontdesk.com'),
(7, 'hash7', 3, 'aisha@maintenance.com'), (8, 'hash8', 2, 'noah@finance.com'),
(9, '1234', 4, '1234'),      -- Admin Creds: 1234 / 1234
(10, '123', 5, '123'),       -- Manager Creds: 123 / 123
(11, '12', 6, '12'),         -- Tenant Creds: 12 / 12
(12, 'h12', 6, 'emily@t.com'), (13, 'h13', 3, 'jack@m.com'),
(14, 'h14', 6, 'mark@t.com'), (15, 'h15', 6, 'david@t.com'),
(16, 'h16', 1, 'lily@f.com'), (17, 'h17', 6, 'maya@t.com'),
(18, 'h18', 6, 'sarah@t.com'), (19, 'h19', 3, 'will@m.com'),
(20, 'h20', 6, 'liam@t.com');

-- ========================================================
-- 3. BUILDINGS & APARTMENTS (HUGE EXPANSION)
-- ========================================================
INSERT INTO Buildings (building_id, city_id, street, postcode) VALUES
(1, 1, '10 City Road', 'BS1 1AA'), (2, 2, '5 Atlantic Wharf', 'CF10 4XY'),
(3, 3, '1 London Bridge', 'SE1 9SG'), (4, 4, '88 Oxford Rd', 'M13 9PL'),
(5, 1, '22 Temple Meads', 'BS1 6QS'), (6, 1, '45 Clifton Village', 'BS8 4EB');

INSERT INTO Apartments (apartment_id, city_id, building_id, num_rooms, type, occupancy_status) VALUES
(1, 1, 1, 1, 'Studio', 'Occupied'), (2, 2, 2, 2, 'Apartment', 'Occupied'),
(3, 3, 3, 4, 'Penthouse', 'Occupied'), (4, 4, 4, 1, 'Studio', 'Vacant'),
(5, 1, 5, 2, 'Apartment', 'Occupied'), (6, 1, 5, 1, 'Studio', 'Vacant'),
(7, 1, 6, 3, 'Apartment', 'Occupied'), (8, 1, 6, 1, 'Studio', 'Occupied'),
(9, 1, 1, 2, 'Apartment', 'Vacant'); -- Vacant for Bristol Admin testing

-- ========================================================
-- 4. TENANTS & LEASES (BALANCED FOR BRISTOL ADMIN)
-- ========================================================
INSERT INTO Tenant (tenant_id, user_id, ni_number, telephone, occupation, apartment_type, lease_period) VALUES
(1, 1, 'NI101A', 700111, 'Student', 'Studio', '6 months'),
(2, 2, 'NI202B', 700222, 'Teacher', 'Apartment', '12 months'),
(3, 11, 'NI1212T', 71212, 'Tester', 'Penthouse', '24 months'),
(4, 12, 'NI444D', 70044, 'Designer', 'Apartment', '12 months'),
(5, 14, 'NI555E', 70055, 'Writer', 'Apartment', '6 months'),
(6, 20, 'NI666F', 70066, 'Solicitor', 'Studio', '12 months');

INSERT INTO Lease (lease_id, apartment_id, tenant_id, start_date, end_date, deposit, Agreed_rent) VALUES
(1, 1, 1, '2026-01-01', '2026-07-01', 800, 900),
(2, 2, 2, '2026-02-01', '2027-02-01', 1200, 1300),
(3, 3, 3, '2026-03-01', '2028-03-01', 3000, 2500),
(4, 5, 4, '2026-04-01', '2027-04-01', 1100, 1100), -- Bristol
(5, 7, 5, '2026-05-01', '2026-11-01', 900, 950),   -- Bristol
(6, 8, 6, '2026-03-15', '2027-03-15', 850, 850);   -- Bristol

-- ========================================================
-- 5. PAYMENTS & MAINTENANCE
-- ========================================================
INSERT INTO Payment (lease_id, due_date, payment_date, amount, Is_late) VALUES
(4, '2026-04-01', '2026-04-01', 1100, 0),
(6, '2026-03-15', '2026-03-20', 850, 1),
(3, '2026-04-01', NULL, 2500, 1);

INSERT INTO Maintenance_Request (request_id, apartment_id, tenant_id, issue, Maintenance_status, priority) VALUES
(1, 1, 1, 'Leaking Pipe', 'In Progress', 'High'),
(2, 5, 4, 'Broken Window', 'Open', 'Medium');

INSERT INTO Employee (employee_id, request_id, Full_name, salary, hire_date) VALUES
(1, 1, 'John Repair', 35000, '2024-05-10'),
(2, 2, 'Jack Bristol', 32000, '2025-01-15');

INSERT INTO Maintenance_Assignment (request_id, employee_id, assigned_date, is_current) VALUES
(1, 1, '2026-03-21', 1), (2, 2, '2026-04-11', 1);