from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64

from sqlalchemy.exc import IntegrityError

from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'master_access'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), index=True, nullable=False)
    pswd = db.Column(db.String(255), index=True, unique=False)
    cryptkey = db.Column(db.String(255), index=True, nullable=False)
    email_address = db.Column(db.String(255), index=True, unique=True, nullable=False)
    create_date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_logon = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    passman_entries = db.relationship(
        "PassmanEntry",
        back_populates="master",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return '<User %r>' % self.name

class PassmanEntry(UserMixin, db.Model):
    __tablename__ = "passman_entries"
    eid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    uid = db.Column(
        db.Integer,
        db.ForeignKey("master_access.id",ondelete="CASCADE",onupdate="CASCADE"),
        nullable=False
    )
    entry_username = db.Column(db.String(255),nullable=False)
    entry_password = db.Column(db.String(255),nullable=False)
    site_url = db.Column(db.String(500),nullable=True)
    entry_name = db.Column(db.String(255),nullable=False)
    create_date = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    last_modified = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
    master = db.relationship("User",back_populates="passman_entries")

def create_passman_entry(uid,entry_name,entry_username,entry_password,site_url=None):
        #Create a new password entry. The entry_password is encrypted before being stored.
    user = db.session.get(User, uid)
    if user is None:
        raise ValueError("User does not exist.")
    if not user.cryptkey:
        raise ValueError("User does not have a valid cryptkey.")
    encrypted_password = encrypt_password(entry_password,user.cryptkey,user.id)
    try:
        entry = PassmanEntry(uid=user.id,entry_name=entry_name,entry_username=entry_username,entry_password=encrypted_password,site_url=site_url)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        return f"Error: {e}"
    return entry

def get_passman_entry(uid, eid):
        #Get a single password entry belonging to the specified user.
    user = db.session.get(User, uid)
    if user is None:
        raise ValueError("User does not exist.")
    entry = PassmanEntry.query.filter_by(eid=eid,uid=user.id).first()
    if entry is None:
        return None
    entry.entry_password = decrypt_password(entry.entry_password,user.cryptkey,user.id)
    return entry

def get_passman_entries(uid):
        #Get all password entries for a user.
        #passwords are decrypted before being returned.
    user = db.session.get(User, uid)
    if user is None:
        raise ValueError("User does not exist.")
    entries = PassmanEntry.query.filter_by(uid=user.id).all()
    for entry in entries:
        entry.entry_password = decrypt_password(entry.entry_password,user.cryptkey,user.id)
    return entries

def update_passman_entry(uid,eid,entry_name,entry_username,entry_password,site_url=None):
        #Update an existing password entry.
        #The new password is encrypted before being stored.
    user = db.session.get(User, uid)
    if user is None:
        raise ValueError("User does not exist.")
    entry = PassmanEntry.query.filter_by(eid=eid,uid=user.id).first()
    if entry is None:
        return None
    encrypted_password = encrypt_password(entry_password,user.cryptkey,user.id)
    entry.entry_name = entry_name
    entry.entry_username = entry_username
    entry.entry_password = encrypted_password
    entry.site_url = site_url
    db.session.commit()
    return entry

def delete_passman_entry(eid):
    entry = db.session.get(PassmanEntry, eid)
    if entry is None:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True

def derive_encryption_key(cryptkey, uid):
        #Derive a Fernet-compatible encryption key from the user's
        #cryptkey phrase and master_access.id.
    if not cryptkey:
        raise ValueError("Cryptkey cannot be empty.")
        # Use the user's database ID as part of the salt.
    salt = f"PyPassMan:{uid}".encode("utf-8")
        # Convert the cryptkey phrase into a 32-byte key.
    kdf = hashlib.pbkdf2_hmac("sha256",cryptkey.encode("utf-8"),salt,600_000,dklen=32)
        # Fernet requires a URL-safe base64 encoded 32-byte key.
    return base64.urlsafe_b64encode(kdf)

def encrypt_password(password, cryptkey, uid):
        #Encrypt a password using the user's cryptkey and UID.
    if password is None:
        raise ValueError("Password cannot be None.")
    key = derive_encryption_key(cryptkey,uid)
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode("utf-8"))
    return encrypted_password.decode("utf-8")

def decrypt_password(encrypted_password, cryptkey, uid):
        #Decrypt a password using the user's cryptkey and UID.
    if encrypted_password is None:
        raise ValueError("Encrypted password cannot be None.")
    key = derive_encryption_key(cryptkey,uid)
    fernet = Fernet(key)
    try:
        decrypted_password = fernet.decrypt(encrypted_password.encode("utf-8"))
        return decrypted_password.decode("utf-8")

    except InvalidToken:
        raise ValueError(
            "Unable to decrypt password. "
            "The cryptkey may be incorrect or the encrypted "
            "password may have been corrupted."
        )
""""
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

CREATE TABLE passman_entries (
    eid INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    uid INT UNSIGNED NOT NULL,

    entry_username VARCHAR(255) NOT NULL,
    entry_password VARCHAR(255) NOT NULL,
    site_url VARCHAR(500),
    entry_name VARCHAR(255) NOT NULL,

    create_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_passman_entries_master
        FOREIGN KEY (uid)
        REFERENCES master_access(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_passman_entries_master_id (master_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
  
ALTER TABLE passman_entries
DROP FOREIGN KEY fk_passman_entries_master,
CHANGE COLUMN master_id uid INT UNSIGNED NOT NULL,
ADD CONSTRAINT fk_passmanentry_uid
    FOREIGN KEY (uid)
    REFERENCES master_access(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;
  
"""