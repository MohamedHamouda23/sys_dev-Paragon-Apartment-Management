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






-- ==========================================
-- 1. LEVEL 1: INDEPENDENT TABLES
-- ==========================================
INSERT INTO Role (role_name) VALUES
('Front-desk Staff'), ('Finance Manager'), ('Maintenance Staff'), 
('Administrators'), ('Manager'), ('Tenant');

-- ID 1: Bristol, 2: Cardiff, 3: London, 4: Manchester
INSERT INTO Location (city_name) VALUES
('Bristol'), ('Cardiff'), ('London'), ('Manchester');

-- ==========================================
-- 2. LEVEL 2: BUILDINGS & USERS
-- ==========================================
INSERT INTO Buildings (city_id, street, postcode) VALUES
(1, '123 Bristol St', 'BS1 4ST'),
(2, '456 Cardiff Rd', 'CF10 1EP'),
(3, '789 London Ave', 'E1 6AN'),
(4, '321 Manchester Blvd', 'M1 2AB');

INSERT INTO User (city_id, first_name, surname) VALUES
(1, 'mohamed', 'hamouda'), -- User ID 1
(1, 'ava', 'abtin'),       -- User ID 2
(1, 'leyla', 'Ahmed'),     -- User ID 3
(1, 'erin', 'williams'),   -- User ID 4
(1, 'tenant', 'test'),     -- User ID 5
(1, 'chiko', 'momchil'),   -- User ID 6
(1, 'test', 'test'),       -- User ID 7
(1, 'Bristol', 'Admin'),   -- User ID 8
(2, 'Cardiff', 'Admin'),   -- User ID 9
(3, 'London', 'Admin'),    -- User ID 10
(4, 'Manchester', 'Admin'),-- User ID 11
(4, 'Omar', 'Nasser');      -- User ID 12

-- ==========================================
-- 3. LEVEL 3: USER ACCESS (Old Emails/Passwords)
-- ==========================================
INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES
(1, 'hash_frontdesk123', 1, 'mohamed@company.com'),
(2, 'hash_finance123', 2, 'ava@company.com'),
(3, 'hash_maint123', 3, 'leyla@company.com'),
(4, 'hash_admin123', 4, 'erin@company.com'),
(5, '1234', 5, '1234'), 
(6, '12', 6, '12'),
(7, '123', 4, '123'),
(8, 'admin123', 4, 'bristol_admin@company.com'),
(9, 'admin123', 4, 'cardiff_admin@company.com'),
(10, 'admin123', 4, 'london_admin@company.com'),
(11, 'admin123', 4, 'manchester_admin@company.com'),
(12, 'tenant123', 6, 'omar@tenant.com');

-- ==========================================
-- 4. LEVEL 4: TENANTS & APARTMENTS
-- ==========================================
-- Tenant 1 is user 6 (Chiko), Tenant 2 is user 12 (Omar)
INSERT INTO Tenant (user_id, ni_number, telephone, occupation, apartment_type, lease_period) VALUES 
(6, 'NI123456A', 712345678, 'Student', 'Studio', '6 months'),
(12, 'NI999999M', 799999999, 'Engineer', 'Apartment', '12 months');

INSERT INTO Apartments (city_id, building_id, num_rooms, type, occupancy_status) VALUES
(1, 1, 1, 'Studio', 'Occupied'),    -- Apt 1
(2, 2, 2, 'Apartment', 'Occupied'), -- Apt 2
(3, 3, 4, 'Penthouse', 'Vacant'),   -- Apt 3
(4, 4, 2, 'Apartment', 'Occupied'); -- Apt 4

-- ==========================================
-- 5. LEVEL 5: LEASES (Agreed Rent Examples)
-- ==========================================
INSERT INTO Lease (apartment_id, tenant_id, start_date, end_date, deposit, early_termination_fee, Agreed_rent) VALUES
(1, 1, '2026-01-01', '2026-12-31', 1000, 500, 1200), -- Lease 1
(4, 2, '2026-01-01', '2026-12-31', 1000, 500, 1100); -- Lease 2

-- ==========================================
-- 6. LEVEL 6: PAYMENTS (Test Cases)
-- ==========================================
INSERT INTO Payment (lease_id, due_date, payment_date, amount, Is_late) VALUES
(1, '2026-04-01', '2026-04-01', 1200, 0), -- FULLY PAID
(2, '2026-05-01', '2026-05-01', 500, 0);  -- PARTIAL (Agreed 1100, Paid 500)