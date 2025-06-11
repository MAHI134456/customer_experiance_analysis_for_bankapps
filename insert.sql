-- Delete existing schema to clear all conflicts
BEGIN
    EXECUTE IMMEDIATE 'DROP USER bank_reviews CASCADE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -1918 THEN
            RAISE;
        END IF;
END;
/

-- Create new user
CREATE USER bank_reviews IDENTIFIED BY BankReviews123
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  QUOTA UNLIMITED ON USERS;

-- Grant all necessary permissions
GRANT CONNECT, RESOURCE, CREATE SESSION, CREATE TABLE TO bank_reviews;

-- Switch to bank_reviews schema
ALTER SESSION SET CURRENT_SCHEMA = bank_reviews;

-- Create Banks table
CREATE TABLE banks (
    bank_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bank_name VARCHAR2(100) NOT NULL UNIQUE,
    country VARCHAR2(50) DEFAULT 'Ethiopia',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant REFERENCES on Banks to bank_reviews
GRANT REFERENCES ON banks TO bank_reviews;

-- Create Reviews table (matches your CSV)
CREATE TABLE reviews (
    review_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bank_id NUMBER NOT NULL,
    review_text VARCHAR2(4000),
    rating NUMBER CHECK (rating BETWEEN 1 AND 5),
    review_date DATE,
    source VARCHAR2(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_id) REFERENCES banks(bank_id)
);

-- Create index
CREATE INDEX idx_reviews_bank_id ON reviews(bank_id);

-- Switch back to SYS
ALTER SESSION SET CURRENT_SCHEMA = SYS;