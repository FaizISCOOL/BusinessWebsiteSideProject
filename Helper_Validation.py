import secrets
from datetime import datetime, timedelta
import importlib
import sys
import subprocess
import types
from typing import TypeAlias
import smtplib
from email.message import EmailMessage
ImportModule: TypeAlias = types.ModuleType
class ImportingListMismatch(Exception):
    """Error raised when pip package name and runtime module name lists do not match in size."""
    pass
class EmailFailure(Exception):
    """Error raised when emailing fails."""
    pass

class Helper:
    _cache: dict = {}
    def __init__(self):
        pass
    @staticmethod
    def Ensure_Library(module_name: str, pip_accepted_name: None | str = None) -> None:
        pip_accepted_name = module_name if pip_accepted_name is None else pip_accepted_name
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_accepted_name], check=True)
                importlib.invalidate_caches()
            except Exception:
                sys.exit(1)
    def library_initialization(self) -> dict:
        if Helper._cache:
            return Helper._cache
        libraries = ['argon2']
        pip_accepted = ['argon2-cffi']
        if len(libraries) != len(pip_accepted):
            raise ImportingListMismatch('The Lists DO NOT MATCH')
        modules_to_import: dict[str, ImportModule] = {}
        for lib_name, pip_name in zip(libraries, pip_accepted):
            self.Ensure_Library(module_name=lib_name, pip_accepted_name=pip_name)
            modules_to_import[lib_name] = importlib.import_module(lib_name)
        Helper._cache = modules_to_import
        return Helper._cache
    @staticmethod
    def generate_verification_code() -> tuple[str, str]:
        code = str(100000 + secrets.randbelow(900000))
        expiry_time = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        return code, expiry_time
    # REMEMBER WHENEVER YOU SEND ANY sender_password here, PLEASE MAKE SURE its NOT your actual password
    # You need to get a special password, Known as the APP password from google
    # also pull it out from either environ.get or something else so YOUR APP PASS DOSENT GET STOLEN
    def email_send(self,sender_email : str, recipient_email : str, subject : str, message : str, sender_password : str ) -> bool:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = sender_email
        email['To'] = recipient_email
        email.set_content(message)
        smtp_server = "smtp.gmail.com"
        ssl_port = 465
        try:
            with smtplib.SMTP_SSL(smtp_server, ssl_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(email)
            return True
        except Exception as e:
            print(e)
            return False
