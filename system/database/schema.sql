CREATE TABLE Location (
    city_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name varchar(70)
);


CREATE TABLE Role (
    role_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name varchar(35)
);


CREATE TABLE User (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id  int,
    first_name	VARCHAR(80),
    surname	VARCHAR(80),
    FOREIGN KEY (city_id) REFERENCES Location(city_id)
);



CREATE TABLE User_Access (
    user_id   int,
    password_hash  VARCHAR(255),
    role_id	int,
    email	VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (role_id) REFERENCES Role(role_id)

);


CREATE TABLE Tenant (
    tenant_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  int,
    ni_number	VARCHAR(20),
    telephone	int,
    occupation VARCHAR(120),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);


CREATE TABLE Tenant_Reference (
    reference_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id  int,
    reference	VARCHAR(255),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id)

);



CREATE TABLE Occupancy_Status
 (
    occupancy_status_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    occupancy_status	VARCHAR(30)
);


CREATE TABLE Apartment_Type (
    type_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name	VARCHAR(50)
);


CREATE TABLE Apartments
 (
    apartment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id	int,
    address	  VARCHAR(255),
    num_rooms	int,
    type_id 	int,
    occupancy_status_id 	int,
    FOREIGN KEY (city_id) REFERENCES Location(city_id),
    FOREIGN KEY (type_id) REFERENCES Apartment_Type(type_id),
    FOREIGN KEY (occupancy_status_id) REFERENCES Occupancy_Status(occupancy_status_id)
);




CREATE TABLE Lease
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


CREATE TABLE Payment
 (
    payment_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id 	int,
    due_date	DATE,
    payment_date	DATE,
    amount	REAl,
    Is_late	BOOLEAN,
    FOREIGN KEY (lease_id) REFERENCES Lease(lease_id)


);

CREATE TABLE Maintenance_Request_Status
 (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    status	VARCHAR(50)

);

CREATE TABLE Maintenance_Priority
 (
    priority_id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority	VARCHAR(50)

);

CREATE TABLE Maintenance_Request
 (
    request_id 	INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id 	int,
    tenant_id 	int,
    issue	VARCHAR(255),
    description	VARCHAR(255),
    status_id 	int,
    priority_id 	int,
    created_date	DATETIME,
    resolved_date	DATETIME,
    notes	VARCHAR(255),
    FOREIGN KEY (apartment_id) REFERENCES Apartments(apartment_id),
    FOREIGN KEY (tenant_id) REFERENCES Tenant(tenant_id),
    FOREIGN KEY (status_id) REFERENCES Maintenance_Request_Status(status_id),
    FOREIGN KEY (priority_id) REFERENCES Maintenance_Priority(priority_id)

);


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
    data_to_date	DATE ,
    FOREIGN KEY (apartment_id) REFERENCES Apartments(apartment_id),
    FOREIGN KEY (payment_id) REFERENCES Payment(payment_id)



);




CREATE TABLE Report_Type
 (
  

    report_type_id 	INTEGER PRIMARY KEY AUTOINCREMENT ,
    report_id 	INTEGER ,
    report_type	VARCHAR(50),
    FOREIGN KEY (report_id) REFERENCES Report(report_id)

);


INSERT INTO Role (role_name) VALUES
('Front-desk Staff'),
('Finance Manager'),
('Maintenance Staff'),
('Administrators'),
('Manager'),
('Tenant');

INSERT INTO Location (city_name) VALUES
('Bristol'),
('Cardiff'),
('London'),
('Manchester');

INSERT INTO User (city_id, first_name, surname) VALUES
(1, 'mohamed', 'hamouda'),
(1, 'ava', 'abtin'),
(1, 'leyla', 'Ahmed'),
(1, 'erin', 'williams'),
(1, 'tenant', 'test'),
(1, 'chiko', 'momchil'),
(1, 'test', 'test');

INSERT INTO User_Access (user_id, password_hash, role_id, email) VALUES
(1, 'hash_frontdesk123', 1, 'mohamed@company.com'),
(2, 'hash_finance123', 2, 'ava@company.com'),
(3, 'hash_maint123', 3, 'leyla@company.com'),
(4, 'hash_admin123', 4, 'erin@company.com'),
(5, 'hash_manager123', 5, 'chiko@company.com'),
(6, 'hash_admin123', 6, 'Tenant@company.com'),
(7, '123', 1, '123');


INSERT INTO Tenant (user_id, ni_number, telephone, occupation)
VALUES (6, 'NI123456A', 712345678, 'Student');


INSERT INTO Tenant_Reference (tenant_id, reference)
VALUES (1, 'Previous landlord — paid rent on time');









