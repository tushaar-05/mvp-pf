-- Add address fields to customer_gigs table
ALTER TABLE customer_gigs
ADD COLUMN address_line1 VARCHAR(255) AFTER category,
ADD COLUMN address_line2 VARCHAR(255) AFTER address_line1,
ADD COLUMN city VARCHAR(100) AFTER address_line2,
ADD COLUMN state VARCHAR(100) AFTER city,
ADD COLUMN pincode VARCHAR(20) AFTER state,
ADD COLUMN landmark VARCHAR(255) AFTER pincode;
