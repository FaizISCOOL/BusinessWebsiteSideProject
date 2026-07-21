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
import re
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
        pip_accepted_name : str = module_name if pip_accepted_name is None else pip_accepted_name
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
        libraries : list = ['argon2']
        pip_accepted : list = ['argon2-cffi']
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
        code : str = str(100000 + secrets.randbelow(900000))
        expiry_time : str = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        return code, expiry_time
    # REMEMBER WHENEVER YOU SEND ANY sender_password here, PLEASE MAKE SURE it's NOT your actual password
    # You need to get a special password, Known as the APP password from GOOGLE
    # also pull it out from either environ.get or something else so YOUR APP PASS DOESN'T GET STOLEN
    @staticmethod
    def email_send(sender_email : str, recipient_email : str, subject : str, message : str, sender_password : str ) -> bool:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = sender_email
        email['To'] = recipient_email
        email.set_content(message, subtype='html')
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
class Validator:
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')
    COUNTRY_CODE_SET : set[str] = {
        "+1", "+7", "+20", "+27", "+30", "+31", "+32", "+33", "+34", "+36", "+39", "+40",
        "+41", "+43", "+44", "+45", "+46", "+47", "+48", "+49", "+51", "+52", "+53", "+54",
        "+55", "+56", "+57", "+58", "+60", "+61", "+62", "+63", "+64", "+65", "+66", "+81",
        "+82", "+84", "+86", "+90", "+91", "+92", "+93", "+94", "+95", "+98", "+212", "+213",
        "+216", "+230", "+233", "+234", "+254", "+255", "+256", "+351", "+353", "+358", "+380",
        "+502", "+503", "+504", "+505", "+506", "+507", "+593", "+852", "+853", "+880", "+886",
        "+960", "+961", "+962", "+963", "+964", "+965", "+966", "+968", "+970", "+971", "+972",
        "+973", "+974", "+975", "+977", "+994", "+995"
    }
    CONTACT_RE = re.compile(r"^\d{4,14}$")
    ALLOWED_PASS_RE = re.compile(r"^[a-zA-Z0-9!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]{8,16}$")
    def __init__(self):
        pass
    @classmethod
    def strong_password(cls, password: str) -> tuple[bool, str]:
        pass
