DROP DATABASE IF EXISTS `blood_bank_db`;
CREATE DATABASE `blood_bank_db`;
USE `blood_bank_db`;

CREATE TABLE `roles` ( `role_id` INT NOT NULL AUTO_INCREMENT, `role_name` VARCHAR(50) NOT NULL UNIQUE, PRIMARY KEY (`role_id`) ) ENGINE=InnoDB;
INSERT INTO `roles` (`role_name`) VALUES ('Administrator'), ('Phlebotomist'), ('Lab Technician'), ('Coordinator');

CREATE TABLE `staff` (
  `staff_id` INT NOT NULL AUTO_INCREMENT, `first_name` VARCHAR(100) NOT NULL, `last_name` VARCHAR(100) NOT NULL,
  `employee_number` VARCHAR(50) NOT NULL UNIQUE, `role_id` INT NOT NULL, `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (`staff_id`), CONSTRAINT `fk_staff_role_id` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`)
) ENGINE=InnoDB;

CREATE TABLE `donors` (
  `donor_id` INT NOT NULL AUTO_INCREMENT, `first_name` VARCHAR(100) NOT NULL, `last_name` VARCHAR(100) NOT NULL,
  `date_of_birth` DATE NOT NULL, `blood_group` ENUM('A', 'B', 'AB', 'O') NOT NULL, `rh_factor` ENUM('+', '-') NOT NULL,
  `gender` ENUM('Male', 'Female', 'Other') NULL, `phone_number` VARCHAR(20) NULL, `email` VARCHAR(255) NULL UNIQUE,
  `registration_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`donor_id`)
) ENGINE=InnoDB;

CREATE TABLE `screenings` (
  `screening_id` INT NOT NULL AUTO_INCREMENT, `donor_id` INT NOT NULL, `staff_id` INT NOT NULL,
  `screening_date` DATETIME NOT NULL, `hemoglobin` DECIMAL(5,2) NULL, `blood_pressure_systolic` INT NULL,
  `blood_pressure_diastolic` INT NULL, `weight_kg` DECIMAL(5,2) NULL, `is_eligible` BOOLEAN NOT NULL, `notes` TEXT NULL,
  PRIMARY KEY (`screening_id`),
  CONSTRAINT `fk_screenings_donor_id` FOREIGN KEY (`donor_id`) REFERENCES `donors` (`donor_id`),
  CONSTRAINT `fk_screenings_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB;

CREATE TABLE `donations` (
  `donation_id` INT NOT NULL AUTO_INCREMENT, `donor_id` INT NOT NULL, `screening_id` INT NOT NULL UNIQUE,
  `phlebotomist_staff_id` INT NOT NULL, `donation_date` DATETIME NOT NULL, `collection_site` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`donation_id`),
  CONSTRAINT `fk_donations_donor_id` FOREIGN KEY (`donor_id`) REFERENCES `donors` (`donor_id`),
  CONSTRAINT `fk_donations_screening_id` FOREIGN KEY (`screening_id`) REFERENCES `screenings` (`screening_id`),
  CONSTRAINT `fk_donations_staff_id` FOREIGN KEY (`phlebotomist_staff_id`) REFERENCES `staff` (`staff_id`)
) ENGINE=InnoDB;

-- THIS TABLE WAS MISSING
CREATE TABLE `organization` (
  `org_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  `org_type` ENUM('Hospital', 'NGO', 'Clinic', 'Other') NOT NULL,
  `contact_person` VARCHAR(100) NULL,
  `contact_phone` VARCHAR(20) NULL,
  `contact_email` VARCHAR(255) NULL,
  PRIMARY KEY (`org_id`)
) ENGINE=InnoDB;

CREATE TABLE `blood_units` (
  `unit_id` INT NOT NULL AUTO_INCREMENT, `donation_id` INT NOT NULL UNIQUE,
  `blood_group` ENUM('A', 'B', 'AB', 'O') NOT NULL, `rh_factor` ENUM('+', '-') NOT NULL,
  `collection_date` DATE NOT NULL, `expiry_date` DATE NOT NULL,
  `status` ENUM('In Stock', 'Reserved', 'Issued', 'Quarantined', 'Discarded') NOT NULL,
  `issued_to_org_id` INT NULL, -- This column was missing its table
  PRIMARY KEY (`unit_id`), 
  CONSTRAINT `fk_units_donation_id` FOREIGN KEY (`donation_id`) REFERENCES `donations` (`donation_id`),
  CONSTRAINT `fk_units_org_id` FOREIGN KEY (`issued_to_org_id`) REFERENCES `organization` (`org_id`) -- This relationship was broken
) ENGINE=InnoDB;

-- THIS TABLE WAS MISSING
CREATE TABLE `blood_requests` (
  `request_id` INT NOT NULL AUTO_INCREMENT,
  `org_id` INT NOT NULL,
  `patient_name` VARCHAR(255) NULL,
  `blood_group` ENUM('A', 'B', 'AB', 'O') NOT NULL,
  `rh_factor` ENUM('+', '-') NOT NULL,
  `quantity` INT NOT NULL,
  `status` ENUM('Pending', 'Approved', 'Rejected', 'Fulfilled') NOT NULL DEFAULT 'Pending',
  `request_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`request_id`),
  CONSTRAINT `fk_requests_org_id` FOREIGN KEY (`org_id`) REFERENCES `organization` (`org_id`)
) ENGINE=InnoDB;

CREATE TABLE `tasks` ( `task_id` INT NOT NULL AUTO_INCREMENT, `task_name` VARCHAR(100) NOT NULL UNIQUE, `description` TEXT NULL, PRIMARY KEY (`task_id`) ) ENGINE=InnoDB;
INSERT INTO `tasks` (`task_name`) VALUES ('Donor Screening'), ('Blood Collection'), ('Unit Processing'), ('Inventory Management'), ('Data Entry'), ('System Administration'), ('Donor Outreach');

CREATE TABLE `staff_tasks` (
  `staff_id` INT NOT NULL, `task_id`   INT NOT NULL, PRIMARY KEY (`staff_id`, `task_id`),
  CONSTRAINT `fk_staff_tasks_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_staff_tasks_task_id` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB;