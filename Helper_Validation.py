import secrets
from datetime import datetime, timedelta
import importlib
import sys
import subprocess
import types
from typing import TypeAlias, Callable
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


class ListMismatch(Exception):
    """As it suggests, The values of 2 different lists or more Don't match, in other words the number of elements are inequal"""
    pass


class ElementNotContained(Exception):
    """Well, The error rises when a list is Not a subset of another list, (it is very specifically used), The error Would Not rise during Normal User use"""
    pass


class Helper:
    _cache: dict = {}

    def __init__(self):
        pass

    @staticmethod
    def Ensure_Library(module_name: str, pip_accepted_name: None | str = None) -> None:
        pip_accepted_name: str = module_name if pip_accepted_name is None else pip_accepted_name
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
        libraries: list = ['argon2']
        pip_accepted: list = ['argon2-cffi']
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
        code: str = str(100000 + secrets.randbelow(900000))
        expiry_time: str = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        return code, expiry_time

    # REMEMBER WHENEVER YOU SEND ANY sender_password here, PLEASE MAKE SURE it's NOT your actual password
    # You need to get a special password, Known as the APP password from GOOGLE
    # also pull it out from either environ.get or something else so YOUR APP PASS DOESN'T GET STOLEN
    @staticmethod
    def email_send(sender_email: str, recipient_email: str, subject: str, message: str, sender_password: str) -> bool:
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
    EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[\w.-]+\.[a-zA-Z]{2,}$')
    COUNTRY_CODE_SET: set[str] = {
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
    LIST_OF_FIELDS: set[str] = {'user', 'password', 'email', 'country_code', 'number'}

    @classmethod
    def strong_password(cls, password: str) -> tuple[bool, str | None]:
        if password.strip() == '':
            return False, 'Password cannot be an empty string'
        strong: str | None = cls.ALLOWED_PASS_RE.search(password)
        if not strong:
            return False, 'Password has to be between 8-16 characters'
        has_upper: bool = any(c.isupper() for c in password)
        has_lower: bool = any(c.islower() for c in password)
        has_digit: bool = any(c.isdigit() for c in password)
        has_spec: bool = any(not c.isalnum() for c in password)
        if not (has_upper and has_lower and has_digit and has_spec):
            return False, 'Password must include at least a uppercase, lowercase, digit, and special characters'
        return True, None

    @classmethod
    def valid_email(cls, email: str) -> tuple[bool, str | None]:
        state = cls.EMAIL_RE.match(email) is not None
        if not state:
            return False, 'Invalid email format (xyz@gmail.com)'
        return True, None

    @classmethod
    def check_country_code(cls, country_code: str) -> tuple[bool, str | None]:
        state = country_code in cls.COUNTRY_CODE_SET
        if not state:
            return False, 'Invalid country code'
        return True, None

    @classmethod
    def valid_number(cls, number: str) -> tuple[bool, str | None]:
        state = cls.CONTACT_RE.match(number) is not None
        if not state:
            return False, 'Invalid Number Must be between 4-14 digits and must only be numbers'
        return True, None

    @classmethod
    def valid_user(cls, user: str) -> tuple[bool, str | None]:
        state = cls.USER_RE.match(user) is not None
        if not state:
            return False, 'Invalid User, must be between 3-20 characters'
        return True, None

    FUNCTION_MAP: dict[str, Callable] = {}

    @classmethod
    def _get_func_map(cls) -> dict[str, Callable]:
        if not cls.FUNCTION_MAP:
            cls.FUNCTION_MAP = {
                'user': cls.valid_user,
                'email': cls.valid_email,
                'country_code': cls.check_country_code,
                'number': cls.valid_number,
                'password': cls.strong_password}
        return cls.FUNCTION_MAP

    # Ok so basically field_to_check and field_values are checked left to right matching one for each other, so yeah
    @classmethod
    def validate(cls, field_to_check: list[str], field_values: list[str]) -> tuple[bool, str | None]:
        cls.FUNCTION_MAP = cls._get_func_map()
        value_match = set(field_to_check).issubset(cls.LIST_OF_FIELDS)
        if not value_match:
            raise ElementNotContained(
                'The Value Inputted Does Not match the already Created Class Variable Sets (Dont make changes to it, fix your function call)')
        if len(field_to_check) != len(field_values):
            raise ListMismatch(
                'Well, Your lists do not have the same number of elements, please recheck your function call')
        for key, value in zip(field_to_check, field_values):
            validator_func = cls.FUNCTION_MAP[key]
            output: tuple[bool, str | None] = validator_func(value)
            is_valid, msg = output
            if not is_valid:
                return False, f'{msg}'
        return True, None
