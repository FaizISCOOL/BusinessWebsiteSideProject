from Registeration_And_Database import Database, Register
from Helper_Validation import Helper, Validator
from datetime import datetime, timedelta


class BadDesignError(Exception):
    """Runs when my future self decides to be a bit too over smart"""
    pass


class Login:
    validator: Validator
    helper: Helper
    db: Database

    def __init__(self):
        self.helper = Helper()
        self.db = Database()
        self.validator = Validator()
        self.module = self.helper.library_initialization()
        self.Threshold = [(20, 5), (50, 10), (100, 20), (200, 30), (500, 40), (1000, 50), (2000, 60), (5000, 70)]

    # returns 2 booleans, 1st boolean is used to identify if email is still required, (state == Pending)
    # 2nd boolean is used to identify whether it is active or a banned account
    # For 1st Boolean Pending means bool would be True else False
    # 2nd Bool True Would mean active else would mean banned
    def check_if_email_or_user(self, suspect: str) -> str:
        is_email, _ = self.validator.validate(field_to_check=['email'], field_values=[suspect])
        search_key = ''
        if is_email:
            search_key = 'email'
        else:
            is_user, _ = self.validator.validate(field_to_check=['user'], field_values=[suspect])
            if not is_user:
                raise BadDesignError(
                    'CHECK YOUR VARIABLES IN MAIN FUNCTION BEFORE PASSING THEM IN A HELPER FUNCTION YOU STUPID')
            search_key = 'username'
        return search_key

    def check_verified_state(self, username_or_email: str) -> tuple[bool, bool | str]:
        search_key = self.check_if_email_or_user(username_or_email)
        # Assuming that you run db.find() in the main front end before running an email verification check
        found = self.db.find(list_of_keys=[search_key], list_of_values=[username_or_email])
        if len(found) == 0:
            raise BadDesignError(
                'Username not found, Maybe go ahead and check your Login_Managing File AND YOUR check_verified_state function')
        state = found[0][6]
        if state == 'PENDING_VERIFICATION':
            return True, False
        elif state == 'SUSPENDED':
            return False, False
        return False, True

    # ASSUMING YOU CHECK THE USERNAME BEFORE SENDING THE VALUE HERE
    # The main function should always create a row containing username (Login function) before sending them
    # Lockout = True, Not locked Out = False
    def check_locked_state(self, username_or_email: str) -> tuple[bool, bool | str]:
        search_key = self.check_if_email_or_user(username_or_email)
        found = self.db.find(list_of_keys=[search_key], list_of_values=[username_or_email],
                             table_name='temp_login_block')
        if len(found) == 0:
            return False, False
        output = found[0]
        lockout_temp = output[3]
        if not lockout_temp:
            return False, False
        cleansed_lockout_temp = datetime.fromisoformat(lockout_temp.replace(' ', 'T'))
        if cleansed_lockout_temp > datetime.now():
            return True, 'YOU ARE LOCKED OUT FOR REPEATED LOGIN ATTEMPTS'
        return False, False

    # ON GOD BRO, MAKE SURE YOU AT LEAST CHECK FOR IF A USER IS REGISTERED OR NOT GOD FORBID
    def penalty_row_creator(self, username_or_email):
        rotator = ['username', 'email']
        search_key = self.check_if_email_or_user(username_or_email)
        inverse = rotator[rotator.index(search_key) - 1]
        index_in_main_db = {'username': 1, 'email': 2}
        output = self.db.find(list_of_keys=[search_key], list_of_values=[username_or_email], table_name='registration')
        the_other = output[0][index_in_main_db[inverse]]
        self.db.insert(list_of_keys=[search_key, inverse], list_of_values=[username_or_email, the_other],
                       table_name='temp_login_block', )

    # Custom Thresholds I thought of, I have no clue on how actual websites scale their lockdown length
    # IF 20+ attempts apply threshold
    # ((x-20) * 1.5) + 1 seconds = lockdown time from datetime.now()
    # For attempts expiry, attempts = x, 50<x>20 = 10 minute expiry, 100<x>50 = 20 minutes, 200<x>100 , 30 minutes, 500<x>200 , 40 min and so on (ill set a threshold table)

    def calculate_update_penalties(self, username_or_email: str) -> None:
        search_key = self.check_if_email_or_user(username_or_email)
        output = self.db.find(table_name='temp_login_block', list_of_keys=[search_key],
                              list_of_values=[username_or_email])
        if len(output) == 0:
            self.penalty_row_creator(username_or_email)
            output = self.db.find(table_name='temp_login_block', list_of_keys=[search_key],
                                  list_of_values=[username_or_email])
        attempts = output[0][2]
        now = datetime.now()
        attempts_expire_raw = output[0][4]
        if attempts_expire_raw:
            attempts_expire_dt = datetime.fromisoformat(attempts_expire_raw.replace(' ','T'))
            if now > attempts_expire_dt:
                attempts = 0
        new_attempt = attempts + 1
        if new_attempt >= 20:
            lockout_penalty = ((new_attempt - 20) * 1.5) + 1
            final_lockdown_penalty = datetime.now() + timedelta(seconds=lockout_penalty)
        else:
            final_lockdown_penalty = now
        attempt_expiry = 70
        for higher_bound, expiry in self.Threshold:
            if new_attempt <= higher_bound:
                attempt_expiry = expiry
                break
        final_attempts_expire = now + timedelta(minutes=attempt_expiry)
        lockout_format = final_lockdown_penalty.isoformat(sep=' ')
        expire_format = final_attempts_expire.isoformat(sep=' ')
        self.db.update(update_keys=['attempts', 'lockout', 'attempts_expire'],
                       update_values=[new_attempt, lockout_format, expire_format], where_keys=[search_key],
                       where_values=[username_or_email], table_name='temp_login_block')

    # MAKE SURE YOU CHECK FOR EXISTENCE
    def delete_peaceful_ppl(self, username_or_email: str) -> None:
        search_key = self.check_if_email_or_user(username_or_email)
        output = self.db.find(table_name='registration', list_of_keys=[search_key], list_of_values=[username_or_email])
        some_other_output = self.db.find(table_name='temp_login_block', list_of_keys=[search_key],
                                         list_of_values=[username_or_email])
        if len(output) == 0:
            raise BadDesignError('Like, JUST CHECK IN THE MAIN FUNCTION GOD DAMN IT')
        if len(some_other_output) > 0:
            self.db.delete(list_of_keys=[search_key], table_name='temp_login_block', list_of_values=[username_or_email])

    def update_login_time(self, username_or_email: str) -> None:
        search_key = self.check_if_email_or_user(username_or_email)
        output = self.db.find(table_name='registration', list_of_keys=[search_key],
                              list_of_values=[username_or_email])
        if len(output) == 0:
            raise BadDesignError('Its as simple as writing A LINE OF CODE TO CHECK IF THE ROW EXISTS OR NOT')
        now = datetime.now().isoformat(sep=' ')
        self.db.update(update_keys=['last_login'], update_values=[now], where_keys=[search_key],
                       where_values=[username_or_email], table_name='registration')

    # DON'T STORE THE PASSWORD IN ANYTHING DIRECTLY PASS IT AND HASH IT
    def login(self, username_or_email: str, password_received: str) -> tuple[bool, bool | str]:
        search_key = self.check_if_email_or_user(username_or_email)
        value = username_or_email
        ph = self.module['argon2'].PasswordHasher()
        output = self.db.find(table_name='registration', list_of_keys=[search_key], list_of_values=[value])
        if len(output) == 0:
            return False, 'Incorrect Password or Username/Email'
        value_bool, msg = self.check_locked_state(username_or_email)
        if value_bool:
            return False, msg
        stored_hash = output[0][3]
        try:
            ph.verify(stored_hash, password_received)
        except Exception:
            self.calculate_update_penalties(username_or_email)
            return False, "Incorrect Password or Username/Email"
        self.delete_peaceful_ppl(username_or_email)
        self.update_login_time(username_or_email)
        return True, 'Success'


class ForgotPass:
    def __init__(self):
        self.db = Database()
        self.helper = Helper()
        self.module = self.helper.library_initialization()
        self.validator = Validator()
        self.login = Login()

    def only_email(self,username_or_email : str) -> str:
        decider = self.login.check_if_email_or_user(username_or_email)
        if decider == 'email':
            return username_or_email
        output = self.db.find(table_name='registration',list_of_keys=[decider],list_of_values=[username_or_email])
        if len(output) == 0:
            raise BadDesignError('CHECK Existence In the Main Function')
        return output[0][2]