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
    user_id int,
    date_created	DATETIME ,
    report_type TEXT CHECK(report_type IN ('Financial', 'Occupancy', 'Maintenance')),    
    FOREIGN KEY (user_id) REFERENCES User(user_id)



);


/* --- KEEPING EXISTING DATA (ROLES & LOCATIONS) --- */
INSERT INTO Role (role_name) VALUES 
('Front-desk Staff'), ('Finance Manager'), ('Maintenance Staff'), 
('Administrators'), ('Manager'), ('Tenant');

INSERT INTO Location (city_name) VALUES 
('Bristol'), ('Cardiff'), ('London'), ('Manchester');

/* --- USERS (1-25 EXISTING + 26-35 NEW) --- */
INSERT INTO User (user_id, city_id, first_name, surname) VALUES
(1, 1, 'Ahmed', 'Ali'), (2, 2, 'Sophie', 'Taylor'), (3, 3, 'Mohamed', 'Ibrahim'),
(4, 4, 'Lucas', 'Martin'), (5, 1, 'Zainab', 'Hassan'), (6, 2, 'Oliver', 'Jones'),
(7, 3, 'Aisha', 'Khan'), (8, 4, 'Noah', 'Clark'), (9, 1, 'System', 'Admin'), 
(10, 2, 'Area', 'Manager'), (11, 1, 'Test', 'Tenant'), (12, 1, 'Emily', 'Cook'), 
(13, 1, 'Jack', 'Morgan'), (14, 1, 'Mark', 'Spencer'), (15, 2, 'David', 'Wilson'), 
(16, 2, 'Lily', 'Davies'), (17, 3, 'Maya', 'Patel'), (18, 4, 'Sarah', 'Jenkins'), 
(19, 4, 'William', 'Scott'), (20, 1, 'Liam', 'Davies'), (21, 3, 'James', 'Sterling'), 
(22, 3, 'Elena', 'Ricci'), (23, 4, 'Marcus', 'Brown'), (24, 1, 'Chloe', 'Wilder'), 
(25, 2, 'Dan', 'Evans'),
-- New Users to ensure 6+ per city
(26, 2, 'Gareth', 'Pugh'),    -- Cardiff
(27, 3, 'Sienna', 'Miller'),   -- London
(28, 3, 'Victor', 'Chen'),     -- London
(29, 4, 'George', 'Higgins'),  -- Manchester
(30, 4, 'Elena', 'Varn'),      -- Manchester
(31, 4, 'Pete', 'Townsend'),   -- Manchester
(32, 1, 'Alice', 'Thompson'),  -- Bristol
(33, 2, 'Bethan', 'Price'),    -- Cardiff
(34, 3, 'Amara', 'Okoro'),     -- London
(35, 4, 'Marcus', 'Rashford'); -- Manchester

/* --- USER ACCESS (ACCOUNTS) --- */
INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES
(1, 'hash1', 6, 'ahmed@tenant.com'), (2, 'hash2', 6, 'sophie@tenant.com'),
(3, 'hash3', 6, 'mohamed@tenant.com'), (4, 'hash4', 5, 'lucas@manager.com'),
(5, 'hash5', 6, 'zainab@tenant.com'), (6, 'hash6', 1, 'oliver@frontdesk.com'),
(7, 'hash7', 3, 'aisha@maintenance.com'), (8, 'hash8', 2, 'noah@finance.com'),
(9, '1234', 4, '1234'), (10, '123', 5, '123'), (11, '12', 6, '12'),
(12, 'h12', 6, 'emily@t.com'), (13, 'h13', 3, 'jack@m.com'),
(14, 'h14', 6, 'mark@t.com'), (15, 'h15', 6, 'david@t.com'),
(16, 'h16', 1, 'lily@f.com'), (17, 'h17', 6, 'maya@t.com'),
(18, 'h18', 6, 'sarah@t.com'), (19, 'h19', 3, 'will@m.com'),
(20, 'h20', 6, 'liam@t.com'), (21, 'hash21', 6, 'james@london.com'), 
(22, 'hash22', 1, 'elena@frontdesk.com'), (23, 'hash23', 6, 'marcus@manc.com'), 
(24, 'hash24', 6, 'chloe@bristol.com'), (25, 'hash25', 3, 'dan@maintenance.com'),
-- New Accounts
(26, 'hash26', 3, 'gareth.m@cardiff.com'), (27, 'hash27', 6, 'sienna@tenant.com'),
(28, 'hash28', 3, 'victor.m@london.com'), (29, 'hash29', 6, 'george@tenant.com'),
(30, 'hash30', 3, 'elena.m@manc.com'), (31, 'hash31', 6, 'pete@tenant.com'),
(32, 'hash32', 2, 'alice.f@bristol.com'), (33, 'hash33', 1, 'bethan.f@cardiff.com'),
(34, 'hash34', 1, 'amara.f@london.com'), (35, 'hash35', 1, 'marcus.f@manc.com');

/* --- BUILDINGS & APARTMENTS --- */
INSERT INTO Buildings (building_id, city_id, street, postcode) VALUES
(1, 1, '10 City Road', 'BS1 1AA'), (2, 2, '5 Atlantic Wharf', 'CF10 4XY'),
(3, 3, '1 London Bridge', 'SE1 9SG'), (4, 4, '88 Oxford Rd', 'M13 9PL'),
(5, 1, '22 Temple Meads', 'BS1 6QS'), (6, 1, '45 Clifton Village', 'BS8 4EB'),
(7, 3, '55 Canary Wharf', 'E14 5AB'), (8, 2, '12 Queen St', 'CF10 2AF'), (9, 4, '20 Deansgate', 'M3 3WR');

INSERT INTO Apartments (apartment_id, city_id, building_id, num_rooms, type, occupancy_status) VALUES
(1, 1, 1, 1, 'Studio', 'Occupied'), (2, 2, 2, 2, 'Apartment', 'Occupied'),
(3, 3, 3, 4, 'Penthouse', 'Occupied'), (4, 4, 4, 1, 'Studio', 'Vacant'),
(5, 1, 5, 2, 'Apartment', 'Occupied'), (6, 1, 5, 1, 'Studio', 'Vacant'),
(7, 1, 6, 3, 'Apartment', 'Occupied'), (8, 1, 6, 1, 'Studio', 'Occupied'),
(9, 1, 1, 2, 'Apartment', 'Vacant'), (10, 3, 7, 2, 'Apartment', 'Vacant'),
(11, 4, 4, 2, 'Apartment', 'Occupied'), (12, 3, 3, 1, 'Studio', 'Occupied'),
(13, 2, 8, 2, 'Apartment', 'Occupied'), (14, 4, 9, 1, 'Studio', 'Occupied'), (15, 3, 7, 3, 'Apartment', 'Occupied');

/* --- TENANTS & LEASES --- */
INSERT INTO Tenant (tenant_id, user_id, ni_number, telephone, occupation, apartment_type, lease_period) VALUES
(1, 1, 'NI101A', 700111, 'Student', 'Studio', '6 months'),
(2, 2, 'NI202B', 700222, 'Teacher', 'Apartment', '12 months'),
(3, 11, 'NI1212T', 71212, 'Tester', 'Penthouse', '24 months'),
(4, 12, 'NI444D', 70044, 'Designer', 'Apartment', '12 months'),
(5, 14, 'NI555E', 70055, 'Writer', 'Apartment', '6 months'),
(6, 20, 'NI666F', 70066, 'Solicitor', 'Studio', '12 months'),
(7, 21, 'NI777G', 700777, 'Architect', 'Penthouse', '12 months'),
(8, 23, 'NI888H', 700888, 'Engineer', 'Apartment', '12 months'),
(9, 24, 'NI999I', 700999, 'Nurse', 'Apartment', '6 months'),
(10, 27, 'NI111X', 700112, 'Chef', 'Apartment', '12 months'),
(11, 29, 'NI222Y', 700223, 'Pharmacist', 'Studio', '6 months'),
(12, 31, 'NI333Z', 700334, 'Musician', 'Apartment', '12 months');

INSERT INTO Lease (lease_id, apartment_id, tenant_id, start_date, end_date, deposit, Agreed_rent) VALUES
(1, 1, 1, '2026-01-01', '2026-07-01', 800, 900), (2, 2, 2, '2026-02-01', '2027-02-01', 1200, 1300),
(3, 7, 3, '2026-03-01', '2028-03-01', 3000, 2500), (4, 5, 4, '2026-04-01', '2027-04-01', 1100, 1100),
(5, 7, 5, '2026-05-01', '2026-11-01', 900, 950), (6, 8, 6, '2026-03-15', '2027-03-15', 850, 850),
(7, 12, 7, '2026-06-01', '2027-06-01', 3500, 3000), (8, 11, 8, '2026-01-10', '2027-01-10', 1000, 1050),
(9, 5, 9, '2026-02-15', '2026-08-15', 1100, 1100), (10, 15, 10, '2026-01-01', '2027-01-01', 2000, 1800),
(11, 14, 11, '2026-05-01', '2027-05-01', 750, 750), (12, 11, 12, '2026-01-01', '2027-01-01', 1000, 1000);

/* --- FINANCIAL (PAYMENTS) --- */
INSERT INTO Payment (lease_id, due_date, payment_date, amount, Is_late) VALUES
(1, '2026-01-05', '2026-01-04', 900, 0),
(1, '2026-02-05', '2026-02-11', 900, 1),
(2, '2026-02-05', '2026-02-05', 1300, 0),
(2, '2026-03-05', NULL, 1300, 1),
(3, '2026-03-10', '2026-03-09', 2500, 0),
(3, '2026-04-10', NULL, 2500, 0),
(4, '2026-04-03', NULL, 1100, 0),
(4, '2026-05-03', NULL, 1100, 0),
(5, '2026-05-07', NULL, 950, 0),
(5, '2026-06-07', NULL, 950, 0),
(6, '2026-03-20', '2026-03-19', 850, 0),
(6, '2026-04-20', NULL, 850, 0),
(7, '2026-06-05', NULL, 3000, 0),
(7, '2026-07-05', NULL, 3000, 0),
(8, '2026-01-15', '2026-01-16', 1050, 1),
(8, '2026-02-15', '2026-02-15', 1050, 0),
(9, '2026-02-20', '2026-02-20', 1100, 0),
(9, '2026-03-20', NULL, 1100, 1),
(10, '2026-01-05', '2026-01-03', 1800, 0),
(10, '2026-02-05', '2026-02-09', 1800, 1),
(11, '2026-05-08', NULL, 750, 0),
(11, '2026-06-08', NULL, 750, 0),
(12, '2026-01-10', '2026-01-10', 1000, 0),
(12, '2026-02-10', NULL, 1000, 1);

/* --- MAINTENANCE (COMPLAINTS) --- */
INSERT INTO Maintenance_Request (request_id, apartment_id, tenant_id, issue, Maintenance_status, priority) VALUES
(1, 1, 1, 'Leaking Pipe', 'In Progress', 'High'),
(2, 5, 4, 'Broken Window', 'Open', 'Medium'),
(3, 7, 3, 'Heating Failure', 'Open', 'High'),
(4, 13, 2, 'Faulty Door Lock', 'Open', 'High'),
(5, 15, 10, 'Mold in Bathroom', 'In Progress', 'Medium'),
(6, 14, 11, 'No Hot Water', 'Open', 'High');

/* --- EMPLOYEES & ASSIGNMENTS --- */
INSERT INTO Employee (employee_id, request_id, Full_name, salary, hire_date) VALUES
(1, 1, 'John Repair', 35000, '2024-05-10'),
(2, 2, 'Jack Bristol', 32000, '2025-01-15'),
(3, 3, 'Sarah Bristol', 33000, '2025-02-20');

INSERT INTO Maintenance_Assignment (request_id, employee_id, assigned_date, is_current) VALUES
(1, 1, '2026-03-21', 1), (2, 2, '2026-04-11', 1), (3, 3, '2026-06-02', 1),
(4, 2, '2026-04-05', 1), (6, 1, '2026-05-12', 1);