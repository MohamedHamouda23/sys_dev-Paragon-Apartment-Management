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
INSERT INTO Tenant (tenant_id, user_id, ni_number, telephone, occupation) VALUES
(1, 1, 'NI101A', 700111, 'Student'),
(2, 2, 'NI202B', 700222, 'Teacher'),
(3, 11, 'NI1212T', 71212, 'Tester'),
(4, 12, 'NI444D', 70044, 'Designer'),
(5, 14, 'NI555E', 70055, 'Writer'),
(6, 20, 'NI666F', 70066, 'Solicitor'),
(7, 21, 'NI777G', 700777, 'Architect'),
(8, 23, 'NI888H', 700888, 'Engineer'),
(9, 24, 'NI999I', 700999, 'Nurse'),
(10, 27, 'NI111X', 700112, 'Chef'),
(11, 29, 'NI222Y', 700223, 'Pharmacist'),
(12, 31, 'NI333Z', 700334, 'Musician');

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

/* --- ADDITIONAL GENERATED COVERAGE DATA --- */

/* Staff and tenant users across all cities */
INSERT INTO User (user_id, city_id, first_name, surname) VALUES
(36, 1, 'Ava', 'Harper'), (37, 1, 'Ben', 'Carter'), (38, 1, 'Chloe', 'Reed'),
(39, 1, 'Dylan', 'Brooks'), (40, 1, 'Eva', 'Stone'),
(41, 2, 'Farah', 'Malik'), (42, 2, 'Gareth', 'Lewis'), (43, 2, 'Hana', 'Ahmed'),
(44, 2, 'Idris', 'Owen'), (45, 2, 'Jodie', 'Price'),
(46, 3, 'Karim', 'Shah'), (47, 3, 'Layla', 'Green'), (48, 3, 'Mason', 'Bell'),
(49, 3, 'Nia', 'Ward'), (50, 3, 'Omar', 'Grant'),
(51, 4, 'Priya', 'Cole'), (52, 4, 'Quinn', 'Frost'), (53, 4, 'Ria', 'Khan'),
(54, 4, 'Sam', 'Boyd'), (55, 4, 'Tia', 'Wells'),
(56, 1, 'Theo', 'Miller'), (57, 1, 'Uma', 'Patel'), (58, 1, 'Vinnie', 'Ross'),
(59, 2, 'Willow', 'James'), (60, 2, 'Xander', 'Ali'), (61, 2, 'Yasmin', 'Cook'),
(62, 3, 'Zane', 'White'), (63, 3, 'Aria', 'Young'), (64, 3, 'Blake', 'Noor'),
(65, 4, 'Cora', 'Flynn'), (66, 4, 'Devon', 'Shah'), (67, 4, 'Elio', 'Moore');

INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES
(36, 'hash36', 4, 'ava.admin@bristol.com'),
(37, 'hash37', 5, 'ben.manager@bristol.com'),
(38, 'hash38', 1, 'chloe.frontdesk@bristol.com'),
(39, 'hash39', 3, 'dylan.maintenance@bristol.com'),
(40, 'hash40', 2, 'eva.finance@bristol.com'),
(41, 'hash41', 4, 'farah.admin@cardiff.com'),
(42, 'hash42', 5, 'gareth.manager@cardiff.com'),
(43, 'hash43', 1, 'hana.frontdesk@cardiff.com'),
(44, 'hash44', 3, 'idris.maintenance@cardiff.com'),
(45, 'hash45', 2, 'jodie.finance@cardiff.com'),
(46, 'hash46', 4, 'karim.admin@london.com'),
(47, 'hash47', 5, 'layla.manager@london.com'),
(48, 'hash48', 1, 'mason.frontdesk@london.com'),
(49, 'hash49', 3, 'nia.maintenance@london.com'),
(50, 'hash50', 2, 'omar.finance@london.com'),
(51, 'hash51', 4, 'priya.admin@manc.com'),
(52, 'hash52', 5, 'quinn.manager@manc.com'),
(53, 'hash53', 1, 'ria.frontdesk@manc.com'),
(54, 'hash54', 3, 'sam.maintenance@manc.com'),
(55, 'hash55', 2, 'tia.finance@manc.com'),
(56, 'hash56', 6, 'theo.tenant@bristol.com'),
(57, 'hash57', 6, 'uma.tenant@bristol.com'),
(58, 'hash58', 6, 'vinnie.tenant@bristol.com'),
(59, 'hash59', 6, 'willow.tenant@cardiff.com'),
(60, 'hash60', 6, 'xander.tenant@cardiff.com'),
(61, 'hash61', 6, 'yasmin.tenant@cardiff.com'),
(62, 'hash62', 6, 'zane.tenant@london.com'),
(63, 'hash63', 6, 'aria.tenant@london.com'),
(64, 'hash64', 6, 'blake.tenant@london.com'),
(65, 'hash65', 6, 'cora.tenant@manc.com'),
(66, 'hash66', 6, 'devon.tenant@manc.com'),
(67, 'hash67', 6, 'elio.tenant@manc.com');

/* More apartments to cover every type and occupancy option */
INSERT INTO Apartments (apartment_id, city_id, building_id, num_rooms, type, occupancy_status) VALUES
(16, 1, 1, 3, 'Penthouse', 'Unavailable'),
(17, 1, 5, 2, 'Apartment', 'Vacant'),
(18, 1, 6, 1, 'Studio', 'Occupied'),
(19, 2, 2, 3, 'Penthouse', 'Unavailable'),
(20, 2, 8, 2, 'Apartment', 'Occupied'),
(21, 2, 8, 1, 'Studio', 'Vacant'),
(22, 3, 3, 3, 'Penthouse', 'Occupied'),
(23, 3, 7, 2, 'Apartment', 'Unavailable'),
(24, 3, 7, 1, 'Studio', 'Vacant'),
(25, 4, 4, 3, 'Penthouse', 'Vacant'),
(26, 4, 9, 2, 'Apartment', 'Unavailable'),
(27, 4, 9, 1, 'Studio', 'Occupied');

/* Additional tenant and lease records */
INSERT INTO Tenant (tenant_id, user_id, ni_number, telephone, occupation) VALUES
(13, 56, 'AB123456C', 770001, 'Analyst'),
(14, 57, 'CD223344A', 770002, 'Nurse'),
(15, 58, 'EF334455B', 770003, 'Chef'),
(16, 59, 'GH445566C', 770004, 'Designer'),
(17, 60, 'JK556677D', 770005, 'Engineer'),
(18, 61, 'LM667788A', 770006, 'Teacher'),
(19, 62, 'NP778899B', 770007, 'Consultant'),
(20, 63, 'QR889900C', 770008, 'Developer'),
(21, 64, 'ST990011D', 770009, 'Architect'),
(22, 65, 'UV101112A', 770010, 'Scientist'),
(23, 66, 'WX121314B', 770011, 'Planner'),
(24, 67, 'YZ141516C', 770012, 'Accountant');

INSERT INTO Lease (lease_id, apartment_id, tenant_id, start_date, end_date, deposit, Agreed_rent) VALUES
(13, 16, 13, '2026-03-01', '2027-03-01', 1800, 1700),
(14, 17, 14, '2026-03-15', '2027-03-15', 1000, 1150),
(15, 18, 15, '2026-04-01', '2027-04-01', 900, 950),
(16, 19, 16, '2026-04-10', '2027-04-10', 1900, 1850),
(17, 20, 17, '2026-04-20', '2027-04-20', 1100, 1200),
(18, 21, 18, '2026-05-01', '2027-05-01', 850, 900),
(19, 22, 19, '2026-05-10', '2027-05-10', 2100, 2000),
(20, 23, 20, '2026-05-15', '2027-05-15', 1200, 1300),
(21, 24, 21, '2026-05-20', '2027-05-20', 850, 920),
(22, 25, 22, '2026-06-01', '2027-06-01', 2000, 1950),
(23, 26, 23, '2026-06-10', '2027-06-10', 1250, 1350),
(24, 27, 24, '2026-06-15', '2027-06-15', 900, 980);

/* Additional payment rows */
INSERT INTO Payment (lease_id, due_date, payment_date, amount, Is_late) VALUES
(13, '2026-04-05', '2026-04-04', 1700, 0), (13, '2026-05-05', NULL, 1700, 1),
(14, '2026-04-10', '2026-04-12', 1150, 1), (14, '2026-05-10', '2026-05-08', 1150, 0),
(15, '2026-04-08', '2026-04-08', 950, 0), (15, '2026-05-08', NULL, 950, 1),
(16, '2026-04-15', '2026-04-14', 1850, 0), (16, '2026-05-15', NULL, 1850, 1),
(17, '2026-04-22', '2026-04-25', 1200, 1), (17, '2026-05-22', '2026-05-20', 1200, 0),
(18, '2026-05-05', NULL, 900, 1), (18, '2026-06-05', '2026-06-04', 900, 0),
(19, '2026-05-12', '2026-05-12', 2000, 0), (19, '2026-06-12', NULL, 2000, 1),
(20, '2026-05-18', '2026-05-17', 1300, 0), (20, '2026-06-18', NULL, 1300, 1),
(21, '2026-05-25', NULL, 920, 1), (21, '2026-06-25', '2026-06-24', 920, 0),
(22, '2026-06-05', '2026-06-07', 1950, 1), (22, '2026-07-05', '2026-07-04', 1950, 0),
(23, '2026-06-12', NULL, 1350, 1), (23, '2026-07-12', '2026-07-12', 1350, 0),
(24, '2026-06-18', '2026-06-18', 980, 0), (24, '2026-07-18', NULL, 980, 1);


/* Maintenance statuses and priorities coverage */
INSERT INTO Maintenance_Request (
    request_id, apartment_id, tenant_id, issue, description,
    Maintenance_status, priority, created_date, resolved_date,
    repair_time, repair_cost, notes
) VALUES
(7, 16, 13, 'Smoke Alarm Fault', 'Alarm beeps constantly', 'Approved', 'Low', '2026-06-01', NULL, NULL, NULL, 'Queued'),
(8, 17, 14, 'Door Hinge Loose', 'Bedroom door not closing', 'Approved', 'Medium', '2026-06-02', NULL, NULL, NULL, 'Awaiting parts'),
(9, 18, 15, 'Extractor Fan Noise', 'Kitchen fan rattles', 'Approved', 'High', '2026-06-03', NULL, NULL, NULL, 'Escalated'),
(10, 19, 16, 'Socket Replacement', 'Living room socket broken', 'Resolved', 'Low', '2026-06-04', '2026-06-06', 2, 75, 'Replaced outlet'),
(11, 20, 17, 'Leak Under Sink', 'Water pooling in cabinet', 'Resolved', 'Medium', '2026-06-05', '2026-06-07', 3, 120, 'Seal replaced'),
(12, 21, 18, 'Window Handle Jammed', 'Cannot lock window', 'Resolved', 'High', '2026-06-06', '2026-06-08', 2, 90, 'Handle replaced'),
(13, 22, 19, 'Wall Paint Request', 'Cosmetic repaint request', 'Denied', 'Low', '2026-06-07', NULL, NULL, NULL, 'Cosmetic non-urgent'),
(14, 23, 20, 'Custom Flooring', 'Tenant requested flooring upgrade', 'Denied', 'Medium', '2026-06-08', NULL, NULL, NULL, 'Not covered'),
(15, 24, 21, 'Balcony Extension', 'Structural extension request', 'Denied', 'High', '2026-06-09', NULL, NULL, NULL, 'Not permitted'),
(16, 25, 22, 'Boiler Pressure Drop', 'Heating intermittent', 'Open', 'Low', '2026-06-10', NULL, NULL, NULL, 'Initial triage'),
(17, 26, 23, 'Hallway Lighting', 'Lights flicker at night', 'Open', 'Medium', '2026-06-11', NULL, NULL, NULL, 'Pending technician'),
(18, 27, 24, 'Bathroom Vent', 'Vent stopped working', 'Open', 'High', '2026-06-12', NULL, NULL, NULL, 'Urgent in queue'),
(19, 16, 13, 'Intercom Static', 'Audio not clear', 'In Progress', 'Low', '2026-06-13', NULL, 1, 30, 'Testing wiring'),
(20, 20, 17, 'Radiator Cold Spot', 'Half radiator is cold', 'In Progress', 'Medium', '2026-06-14', NULL, 2, 60, 'Bleeding system'),
(21, 22, 19, 'Garage Door Sensor', 'Door reverses unexpectedly', 'In Progress', 'High', '2026-06-15', NULL, 3, 140, 'Sensor ordered');

/* Complaints coverage */
INSERT INTO Complaints (complaint_id, description, date_submitted, tenant_id) VALUES
(1, 'Noise from corridor after midnight', '2026-06-01', 13),
(2, 'Lift is frequently unavailable', '2026-06-02', 14),
(3, 'Bin collection delayed this week', '2026-06-03', 15),
(4, 'Parking bay occupied by unknown car', '2026-06-04', 16),
(5, 'Entry gate closes too quickly', '2026-06-05', 17),
(6, 'Hallway has strong damp smell', '2026-06-06', 18),
(7, 'Gym area not cleaned regularly', '2026-06-07', 19),
(8, 'Lobby AC not working properly', '2026-06-08', 20),
(9, 'Mailroom lock is difficult to use', '2026-06-09', 21),
(10, 'CCTV blind spot near rear exit', '2026-06-10', 22),
(11, 'Recycling area overfilled', '2026-06-11', 23),
(12, 'Common Wi-Fi is unstable', '2026-06-12', 24);

/* Additional employees and assignments */
INSERT INTO Employee (employee_id, request_id, Full_name, salary, hire_date) VALUES
(4, 7, 'Mia Turner', 34000, '2024-07-01'),
(5, 8, 'Noel Harris', 33500, '2024-08-15'),
(6, 9, 'Olga Peters', 34500, '2024-09-10'),
(7, 10, 'Paul Knight', 35500, '2024-10-20'),
(8, 11, 'Ravi Cooper', 34800, '2025-01-05'),
(9, 12, 'Sana Blake', 34200, '2025-02-11'),
(10, 16, 'Troy Dixon', 33800, '2025-03-03'),
(11, 17, 'Una Morris', 33600, '2025-04-22'),
(12, 18, 'Vera Quinn', 33900, '2025-05-30');

INSERT INTO Maintenance_Assignment (request_id, employee_id, assigned_date, is_current) VALUES
(7, 4, '2026-06-01', 1), (8, 5, '2026-06-02', 1), (9, 6, '2026-06-03', 1),
(10, 7, '2026-06-04', 0), (11, 8, '2026-06-05', 0), (12, 9, '2026-06-06', 0),
(13, 4, '2026-06-07', 0), (14, 5, '2026-06-08', 0), (15, 6, '2026-06-09', 0),
(16, 10, '2026-06-10', 1), (17, 11, '2026-06-11', 1), (18, 12, '2026-06-12', 1),
(19, 10, '2026-06-13', 1), (20, 11, '2026-06-14', 1), (21, 12, '2026-06-15', 1);

/* Report coverage (at least 3 per report type) */
INSERT INTO Report (report_id, user_id, date_created, report_type) VALUES
(1, 8, '2026-06-01 10:00:00', 'Financial'),
(2, 40, '2026-06-02 10:15:00', 'Financial'),
(3, 55, '2026-06-03 10:30:00', 'Financial'),
(4, 4, '2026-06-01 11:00:00', 'Occupancy'),
(5, 10, '2026-06-02 11:15:00', 'Occupancy'),
(6, 47, '2026-06-03 11:30:00', 'Occupancy'),
(7, 7, '2026-06-01 12:00:00', 'Maintenance'),
(8, 25, '2026-06-02 12:15:00', 'Maintenance'),
(9, 54, '2026-06-03 12:30:00', 'Maintenance');