# Don't use this, it is an experiment

---
If you must, create mariadb:
```
CREATE DATABASE IF NOT EXISTS pypassman_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE pypassman_db;

CREATE TABLE `master_access` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `pswd` varchar(255) NOT NULL,
  `cryptkey` varchar(255) NOT NULL,
  `email_address` varchar(255) NOT NULL,
  `create_date` datetime DEFAULT NULL,
  `last_logon` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_master_access_name` (`name`),
  UNIQUE KEY `uq_master_access_email` (`email_address`)
) ENGINE=InnoDB 
  AUTO_INCREMENT=2 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `passman_entries` (
    `eid` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `uid` INT UNSIGNED NOT NULL,
    `entry_username` VARCHAR(255) NOT NULL,
    `entry_password` VARCHAR(255) NOT NULL,
    `site_url` VARCHAR(500),
    `entry_name` VARCHAR(255) NOT NULL,
    `create_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_modified` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_passman_entries_master`
        FOREIGN KEY (`uid`)
        REFERENCES `master_access` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX `idx_passman_entries_master_id` (`master_id`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
 ```
You also need to provide the db connection details in `pypassman.conf`. The cryptkey value needs to exist, but it really doesn't.