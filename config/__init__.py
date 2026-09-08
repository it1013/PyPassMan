#https://flask.palletsprojects.com/en/stable/api/#flask.Flask
#https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/#check-the-sqlalchemy-documentation

from configparser import ConfigParser
from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import base64
import hashlib

import re

from config import MasterAccess
from config import MasterSettings
from config import ManPassEntry
import config

class ConfigFile:
    def __init__(self, configfile:str,config_section:str="CENTRAL"):
        self.configfile = configfile #the string path to the file and the file name
        self.config = ConfigParser()
        self.config.read(configfile)
        self.dbuser = self.config.get(config_section.upper(), "dbuser")
        self.dbpass = self.config.get(config_section.upper(), "dbpass")
        self.cryptkey = self.config.get(config_section.upper(), "cryptkey")
        self.dbhost = self.config.get(config_section.upper(), "dbhost")
        self.dbport = self.config.get(config_section.upper(), "dbport")

    def get_dbpass (self,config_section:str="CENTRAL",debug:bool=False):
        if self.dbpass == "":
            return None
        if debug:
            print("PASS = "+ self.dbpass)
        return base64.b64decode(self.dbpass).decode("utf-8")

    def get_dbuser(self,config_section:str="CENTRAL",debug:bool=False):
        if self.dbuser == "":
            return None
        if debug:
            print("USER = "+ self.dbuser)
        return self.dbuser

    def get_crypt(self,config_section:str="CENTRAL",debug:bool=False):
        if self.cryptkey == "":
            return None
        if debug:
            print("cryptkey = "+ self.cryptkey)
        return self.cryptkey

    def get_crypt_phrase(self,config_section:str="CENTRAL",debug:bool=False):
        if self.cryptkey == "":
            return None
        if debug:
            print("crypt phrase = " + base64.b64decode(self.cryptkey).decode("utf-8"))
        return base64.b64decode(self.cryptkey).decode("utf-8")

    def new_cryptkey(self,config_section:str,debug:bool=False):
        if self.cryptkey == "":
            #key = Fernet.generate_key()
            self.cryptkey = Fernet.generate_key().__str__()
            self.config.set(config_section.upper(), 'cryptkey', self.cryptkey)
            print("Created "+config_section.upper()+" new cryptkey = " + self.cryptkey)
            with open(self.configfile, 'w') as configfile:
                self.config.write(configfile)
        else:
            print("Crypt key already exists, not creating. Please erase "+config_section.upper()+" cryptkey")

    def set_crypt(self,config_section:str ,setvalue:str,debug=False):
        try:
            self.config.set(config_section.upper(), 'cryptkey', setvalue)
            self.cryptkey = setvalue
            with open(self.configfile, 'w') as configfile:
                self.config.write(configfile)
            self.config.read(self.configfile)
        except Exception as e:
            print("Unable to set db host ended with exception: " + e.__str__() + setvalue)
        if debug:
            print(config_section.upper()+" CryptKey set to: " + setvalue)

    def get_host(self,config_section="CENTRAL",debug=False):
        if self.dbhost == "":
            return None
        if debug:
            print("db host = " + self.dbhost )
        return self.dbhost

    def get_port(self,config_section="CENTRAL",debug=False):
        if self.dbport == "":
            return None
        if debug:
            print("db port = " + self.dbport)
        return self.dbport

    def get_server(self,config_section="CENTRAL",debug=False):
        if self.dbhost == "" or self.dbport == "":
            return None
        if debug:
            print("db server = " + self.dbhost + ":" + self.dbport)
        return self.dbhost + ":" + self.dbport

    def set_host(self,config_section:str ,setvalue:str,debug=False):
        try:
            self.config.set(config_section.upper(),'dbhost',setvalue)
            self.dbhost = setvalue
            with open(self.configfile,'w') as configfile:
                self.config.write(configfile)
            self.config.read(self.configfile)
        except Exception as e:
            print("Unable to set db host ended with exception: " + e.__str__() + setvalue)
        if debug:
            print(config_section.upper()+" Host set to: " + setvalue)

    def set_port(self,config_section:str,setvalue:str,debug=False):
        try:
            self.config.set(config_section.upper(),'dbport',setvalue)
            self.dbport = setvalue
            with open(self.configfile,'w') as configfile:
                self.config.write(configfile)
            self.config.read(self.configfile)
        except Exception as e:
            return "Unable to set dbport ended with exception: " + e.__str__()
        if debug:
            print(config_section.upper()+" Port set to: " + setvalue)
        return True

if __name__ == "__main__":
 pass