import random
import string
import pytest
from Registeration_And_Database import Database, Register, DatasetKeyMismatch
from Login_Managing import Login, ForgotPass, BadDesignError
from Helper_Validation import Helper, Validator, ListMismatch, ElementNotContained


class Generator:
    def __init__(self, db: str) -> None:
        self.db = Database(db)
        self.login = Login()
        self.forgot_pass = ForgotPass()
        self.helper = Helper()
        self.email_providers = tuple({
            # Main Global Big Players
            "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
            "live.com", "msn.com", "yahoo.com", "ymail.com", "rocketmail.com",
            "icloud.com", "me.com", "mac.com", "aol.com", "aim.com",
            # Privacy & Developer Focused
            "proton.me", "protonmail.com", "tuta.io", "tutanota.com",
            "fastmail.com", "hey.com", "zoho.com", "mail.com", "gmx.com",
            "posteo.de", "runbox.com", "hushmail.com", "startmail.com",
            # International & Regional Giants
            "mail.ru", "yandex.ru", "rambler.ru", "qq.com", "163.com", "126.com",
            "naver.com", "daum.net", "hanmail.net", "web.de", "gmx.de",
            "t-online.de", "libero.it", "virgilio.it", "wp.pl", "onet.pl",
            "uol.com.br", "bol.com.br", "rediffmail.com", "abv.bg", "sapo.pt",
            # ISP / Telecom Legacy Domains
            "comcast.net", "sbcglobal.net", "att.net", "verizon.net", "cox.net",
            "charter.net", "optonline.net", "earthlink.net", "centurytel.net",
            "centurylink.net", "juno.com", "netzero.net", "frontier.com",
            "windstream.net", "btinternet.com", "virginmedia.com", "sky.com",
            "talktalk.net", "rogers.com", "shaw.ca", "sympatico.ca", "bigpond.com",
            # Regional Variations (Microsoft & Yahoo)
            "hotmail.co.uk", "hotmail.fr", "hotmail.de", "hotmail.es", "hotmail.it",
            "hotmail.ca", "yahoo.co.uk", "yahoo.ca", "yahoo.fr", "yahoo.de",
            "yahoo.it", "yahoo.es", "yahoo.co.in", "yahoo.in", "yahoo.com.au",
            "yahoo.com.br", "yahoo.com.mx", "yahoo.com.tw", "yahoo.com.hk",
            "live.co.uk", "live.fr", "live.ca", "live.com.au", "live.de", "live.nl"
        })
        self.map = {
            'username': self.user_generator,
            'password': self.password_generator,
            'email': self.email_generator,
            'contact': self.contact,
            'country_code': self.country_code
        }

    @staticmethod
    def random_string_generator(start_length: int = 3, end_length: int = 20, custom_length: bool = False) -> str:
        random_length = random.randint(3, 20) if not custom_length else random.randint(start_length, end_length)
        return ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=random_length))

    def email_generator(self) -> str:
        username = self.random_string_generator(start_length=3, end_length=30, custom_length=True)
        domain = random.choice(self.email_providers)
        return f'{username}@{domain}'

    def password_generator(self) -> str:
        upper = random.choice(string.ascii_uppercase)
        lower = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        symbol = random.choice("!@#$%^&*()_+-=")
        password_length = random.randint(4, 12)
        rest = random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_+-=",
                              k=password_length)
        combined = list(upper + lower + digit + symbol + rest)
        random.shuffle(combined)
        joined = "".join(combined)
        return self.helper.hash_password(joined)

    def user_generator(self) -> str:
        return self.random_string_generator()

    @staticmethod
    def country_code():
        country_codes = tuple({
            "+1", "+7", "+20", "+27", "+30", "+31", "+32", "+33", "+34", "+36", "+39", "+40",
            "+41", "+43", "+44", "+45", "+46", "+47", "+48", "+49", "+51", "+52", "+53", "+54",
            "+55", "+56", "+57", "+58", "+60", "+61", "+62", "+63", "+64", "+65", "+66", "+81",
            "+82", "+84", "+86", "+90", "+91", "+92", "+93", "+94", "+95", "+98", "+212", "+213",
            "+216", "+230", "+233", "+234", "+254", "+255", "+256", "+351", "+353", "+358", "+380",
            "+502", "+503", "+504", "+505", "+506", "+507", "+593", "+852", "+853", "+880", "+886",
            "+960", "+961", "+962", "+963", "+964", "+965", "+966", "+968", "+970", "+971", "+972",
            "+973", "+974", "+975", "+977", "+994", "+995"
        })
        return random.choice(country_codes)

    @staticmethod
    def contact():
        return ''.join(random.choices(string.digits, k=random.randint(4, 14)))

    def generator(self, variables_to_generate: list) -> list:
        if any(var not in self.map for var in variables_to_generate):
            raise DatasetKeyMismatch('Variable Mentioned does not exist')
        if len(variables_to_generate) > 5:
            raise ElementNotContained('Maximum variables possible should be 5')
        return [self.map[var]() for var in variables_to_generate]
