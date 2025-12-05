DB:

CREATE TABLE account (
    acc_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('super_admin','department_admin','inventory_admin', 'employee')),
    department VARCHAR(100)
);

CREATE TABLE employee (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
	acc_id INT NOT NULL REFERENCES account(acc_id),
    contact_type VARCHAR(10) DEFAULT 'N/A',
    contact_value VARCHAR(100) DEFAULT 'N/A',
    position VARCHAR(50),
    department VARCHAR(50),
    date_joined DATE DEFAULT CURRENT_DATE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (acc_id) REFERENCES account(acc_id)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) NOT NULL
);

CREATE TABLE requisition (
    requisition_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    date_requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(40) NOT NULL DEFAULT 'Pending Approval'
        CHECK (status IN (
            'Pending Approval',
            'Approved',
            'Denied',
            'Partially Approved – Pending Purchase',
            'Pending Purchase',
            'Purchased',
            'Ready for Pickup'
        )),
    last_status_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY (employee_id) REFERENCES employee(employee_id)
);

CREATE TABLE requisition_item (
    id SERIAL PRIMARY KEY,
    requisition_id INT NOT NULL REFERENCES requisition(requisition_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity DECIMAL(10,2) NOT NULL
);

CREATE TABLE stock_in (
    stock_in_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
	acc_id INT NOT NULL REFERENCES account(acc_id),
    unit VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    quantity_meters DECIMAL(10,2) DEFAULT 0,
    quantity_klg DECIMAL(10,2) DEFAULT 0,
    date_in DATE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (acc_id) REFERENCES account(acc_id)
);

CREATE TABLE stock_out (
    stock_out_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
	acc_id INT NOT NULL REFERENCES account(acc_id),
    unit VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    quantity_meters DECIMAL(10,2) DEFAULT 0,
    quantity_klg DECIMAL(10,2) DEFAULT 0,
    date_out DATE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (acc_id) REFERENCES account(acc_id)
);

CREATE TABLE inventory_balance (
    balance_id SERIAL PRIMARY KEY,
    product_id INT UNIQUE NOT NULL,
    unit VARCHAR(20) NOT NULL,
    opening_inventory DECIMAL(10,2) DEFAULT 0,
    quantity_unit DECIMAL(10,2) DEFAULT 0,
    quantity_meters DECIMAL(10,2) DEFAULT 0,
    quantity_klg DECIMAL(10,2) DEFAULT 0,
    min_stock DECIMAL(10,2) DEFAULT 0,
    procurement_suggestion DECIMAL(10,2) DEFAULT 0,


ALTER TABLE employee ADD COLUMN status VARCHAR(10) DEFAULT 'active';
ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0;
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
