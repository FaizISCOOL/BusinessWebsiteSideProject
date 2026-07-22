from Registeration_And_Database import Database
from Helper_Validation import Helper,Validator
from datetime import datetime,timedelta
class BadDesignError(Exception):
    """Runs when my future self decides to be a bit too over smart"""
    pass

class LOGIN:
    validator: Validator
    helper: Helper
    db: Database
    def __init__(self):
        self.helper = Helper()
        self.db = Database()
        self.validator = Validator()
        self.module = self.helper.library_initialization()
    # returns 2 booleans, 1st boolean is used to identify if email is still required, (state == Pending)
    # 2nd boolean is used to identify whether it is active or a banned account
    # For 1st Boolean Pending means bool would be True else False
    # 2nd Bool True Would mean active else would mean banned
    def check_verified_state(self, username_or_email : str) -> tuple[bool, bool | str]:
        is_email, _ = self.validator.valid_email(username_or_email)
        if is_email:
            search_key = 'email'
        else:
            search_key = 'username'
            valid_user, msg = self.validator.valid_user(username_or_email)
            if not valid_user:
                return False, msg
        # Assuming that you run db.find() in the main front end before running an email verification check
        found = self.db.find(list_of_keys=[search_key],list_of_values=[username_or_email])
        if len(found) == 0:
            raise BadDesignError('Username not found, Maybe go ahead and check your Login_Managing File AND YOUR check_verified_state function')
        state = found[0][6]
        if state == 'PENDING_VERIFICATION':
            return True, False
        elif state == 'SUSPENDED':
            return False, False
        return False, True
    # ASSUMING YOU CHECK THE USERNAME BEFORE SENDING THE VALUE HERE
    # The main function should always create a row containing username (Login function) before sending them
    # Lockout = True, Not locked Out = False
    def check_locked_state(self,username : str) -> tuple[bool, bool | str]:
        state,_ = self.validator.valid_user(username)
        if not state:
            raise BadDesignError('LIKE I SAID CHECK YOUR VALUES (username) BEFORE SENDING THEM IN HELPER FUNCTIONS')
        found = self.db.find(list_of_keys=['username'],list_of_values=[username],table_name='temp_login_block')
        if len(found) == 0:
            return False, False
        output = found[0]
        lockout_temp = output[3]
        cleansed_lockout_temp = datetime.strptime(lockout_temp, '%Y-%m-%d %H:%M:%S')
        if cleansed_lockout_temp > datetime.now():
            return True, 'YOU ARE LOCKED OUT FOR REPEATED LOGIN ATTEMPTS'
        return False, False