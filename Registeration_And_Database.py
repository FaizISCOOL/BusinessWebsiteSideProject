import pathlib, sqlite3
from Helper_Validation import *
from datetime import datetime
class DatabaseListMismatch(Exception):
    """Error raised when target key lists and data value lists mismatch in length."""
    pass
class DatasetKeyMismatch(Exception):
    """Error raised when keys provided do not match the valid columns within the schema configuration."""
    pass
class EmptyList(Exception):
    """Error raised when operation requirements receive empty collections."""
    pass
class EmptyParams(Exception):
    """Error raised when operation requirements receive empty parameters."""
class InvalidParams(Exception):
    """Error raised when operation requirements receive invalid parameter / Values Which are invalid to the ones stored."""
    pass
# Just to show it's a human writing the code, I live in my house with my parents, ok bye
class Database:
    def __init__(self,db_file : pathlib.Path | str ) -> None:
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.table_name = None
        self.hp = Helper()
        self.schemas = {
            'registration': ['id', 'username', 'email', 'password', 'country_code', 'contact_number', 'account_status',
                             'created_at', 'last_login'],
            'email_verification': ['id', 'email', 'code', 'timestamp']}
        self.table_initialization()
        self.unused_code_deletion()
    def table_initialization(self,table_name : str = 'registration') -> None:
        clean_table_name = "".join(char for char in table_name if char.isalnum() or char == '_')
        self.table_name = clean_table_name
        if clean_table_name not in self.schemas and clean_table_name != 'email_verification':
            self.schemas[clean_table_name] = self.schemas['registration']
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {clean_table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        email TEXT CHECK (email LIKE '%_@__%.%_'),
        password TEXT NOT NULL,
        country_code TEXT DEFAULT '+91' CHECK (length(country_code) <= 5),
        contact_number TEXT NOT NULL CHECK(length(contact_number) BETWEEN 7 AND 15),
        account_status TEXT DEFAULT 'PENDING_VERIFICATION' CHECK(account_status IN ('ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")

        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS email_verification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT CHECK (email LIKE '%_@__%.%_'),
        code TEXT NOT NULL CHECK (length(code) >= 6),
        timestamp DATETIME NOT NULL
        );""")

        self.cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{clean_table_name}_username 
            ON {clean_table_name} (username);
            """)
        self.conn.commit()
    def key_match(self,key_values: list, target_table : str) -> None:
        if target_table not in self.schemas:
            raise DatasetKeyMismatch(f"Table '{target_table}' KEY_LIST IS NOT IN THE SCHEMAS.")
        output = set(key_values).issubset(self.schemas[target_table])
        if not output:
            raise DatasetKeyMismatch(f'The key values provided DO NOT MATCH the schema for {target_table}')
    # To ensure The keys are accurate to the ones made when initializing the table
    def find(self, list_of_values: list = None, list_of_keys: list = None, return_all: bool = False,
             table_name: str | None = None) -> list:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        if table_name is None:
            table_name = self.table_name
        self.key_match(list_of_keys,table_name)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys and return_all:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            return self.cursor.fetchall()
        elif not list_of_keys and not return_all:
            raise EmptyList("NO keys Provided / return_all is set to False")
        query = [f'{key} = ?' for key in list_of_keys]
        where_conditions  = ' AND '.join(query)
        final_query = f'SELECT * FROM {table_name} WHERE {where_conditions}'
        self.cursor.execute(final_query, list_of_values)
        return self.cursor.fetchall()
    def insert(self, list_of_values : list = None, list_of_keys : list = None, table_name : str | None = None) -> None:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        if table_name is None:
            table_name = self.table_name
        self.key_match(list_of_keys,table_name)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys:
            raise EmptyList("NO keys Provided")
        columns = ', '.join(list_of_keys)
        placeholders = ['?' for _ in list_of_keys]
        placeholders = ', '.join(placeholders)
        final_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(final_query, list_of_values)
        self.conn.commit()
    def Delete(self, list_of_values : list = None, list_of_keys : list = None, table_name : str | None = None) -> None:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        if table_name is None:
            table_name = self.table_name
        self.key_match(list_of_keys,table_name)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys:
            raise EmptyList("NO keys Provided")
        conditional_key = [f"{key} = ?" for key in list_of_keys]
        query = ' AND '.join(conditional_key)
        final_query = f"DELETE FROM {table_name} WHERE {query}"
        self.cursor.execute(final_query, list_of_values)
        self.conn.commit()
    def Update(self, update_keys : list = None, update_values : list = None,where_keys : list = None, where_values : list = None, table_name : str | None = None) -> None:
        if update_keys is None: update_keys = []
        if update_values is None: update_values = []
        if where_keys is None: where_keys = []
        if where_values is None: where_values = []
        if table_name is None:
            table_name = self.table_name
        self.key_match(update_keys,table_name)
        self.key_match(where_keys, table_name)
        if (len(update_keys) != len(update_values)) or (len(where_keys) != len(where_values)):
            raise DatabaseListMismatch("List Length Mismatch")
        if not update_keys or not where_keys:
            raise EmptyList("NO keys Provided")
        set_update_keys = [f"{key} = ?" for key in update_keys]
        set_query = ', '.join(set_update_keys)
        where_condition_key = [f'{key2} = ?' for key2 in where_keys]
        where_query = ' AND '.join(where_condition_key)
        final_query = f"UPDATE {table_name} SET {set_query} WHERE {where_query}"
        values = update_values + where_values
        self.cursor.execute(final_query, values)
        self.conn.commit()
    # Remember Folks, ONLY USERNAME AND EMAIL ALLOWED since they are special for each account registered
    def extract_id_main(self, method : str | None = None, value : str | None = None, table_name : str | None =None) -> int:
        if method is None:
            raise InvalidParams("Method is None")
        if method not in ['username','email']:
            raise InvalidParams("Method is invalid, Must only be 'username' or 'email'")
        if value is None:
            raise InvalidParams("Value is None, Only 1 ID can be sent back")
        result = self.find(list_of_keys=[method], list_of_values=[value], table_name=table_name)
        if not result:
            raise InvalidParams("The method/Value's are NOT registered IN THE LIST")
        return result[0][0]
    def change_state(self,state_to_change_to : str = None, ID : int = 0) -> None:
        if state_to_change_to is None:
            raise EmptyParams('The parameter state_to_change_to was not provided.')
        if state_to_change_to not in ['ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION']:
            raise InvalidParams('Parameters DO NOT MATCH THE LIST IN FUNCTION (change_state)')
        if ID == 0:
            raise InvalidParams('The ID was NOT provided.')
        self.cursor.execute(f"SELECT 1 FROM registration WHERE id = ?", (ID,))
        if not self.cursor.fetchone():
            raise InvalidParams('The ID provided does not exist in the table.')

        self.Update(update_keys=['account_status'], update_values=[state_to_change_to], where_keys=['id'],
                    where_values=[ID],table_name='registration')
    def check_for_death_time(self,death_time : str) -> bool:
        norm_time = datetime.strptime(death_time, '%Y-%m-%d %H:%M:%S')
        return norm_time < datetime.now()
    # PERSONAL EDITED FOR ONLY THE EMAIL TABLE
    def check_if_correct_code(self,code_provided : str | int,email_user : str) -> tuple[bool,str]:
        packet = self.find(list_of_keys=['email'],list_of_values=[email_user],table_name='email_verification')
        if not packet:
            return False, 'Incorrect email'
        packet_better = packet[0]
        code_stored = packet_better[2]
        if self.check_for_death_time(packet_better[3]):
            return False, 'Code Expired'
        if str(code_stored) != str(code_provided):
            return False, 'Code IS INVALID'
        else:
            return True, 'Code IS AUTHENTICATED'
    def unused_code_deletion(self) -> None:
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            "DELETE FROM email_verification WHERE timestamp < ?",
            (current_time_str,)
        )
        self.conn.commit()
class Register:
    def __init__(self,helper : Helper, db : Database , username: str, password: str, email: str, contact: str, country_code: str) -> None:
        self.db = db
        self.helper = helper
        self.modules: dict[str, ImportModule] = self.helper.library_initialization()
        self.username: str = username
        self.email: str = email
        self.contact: str = contact
        self.country_code: str = country_code
        self.password_hash: str | None = None
        self.hash_password(password)
        self.email_subject = 'Action Required: Verify Your Account'
    def hash_password(self, password : str) -> None:
        passwordhasher = self.modules['argon2'].PasswordHasher
        ph = passwordhasher()
        self.password_hash = ph.hash(password)
    def check_existence(self, list_of_fields: list, list_of_values: list) -> bool:
        return True if len(self.db.find(list_of_keys=list_of_fields, list_of_values=list_of_values)) > 0 else False
    def save_to_database(self) -> bool:
        if self.check_existence(list_of_fields=['username'], list_of_values=[self.username]):
            print(f"The username '{self.username}' is already taken.")
            return False
        if self.check_existence(list_of_fields=['email'], list_of_values=[self.email]):
            print(f"The email '{self.email}' is already in use.")
            return False
        db_keys = ['username', 'email', 'password', 'country_code', 'contact_number']
        db_values = [self.username, self.email, self.password_hash, self.country_code, self.contact]
        try:
            self.db.insert(list_of_keys=db_keys, list_of_values=db_values)
            print(f"Account for '{self.username}' successfully created!")
            return True
        except sqlite3.Error as e:
            print(f" Database error encountered during save: {e}")
            return False
    def small_little_message_creator(self,verification_code : str) -> str:
        message = \
f"""
<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
  <h2 style="color: #333333; margin-top: 0;">Verify Your Account</h2>
  <p style="color: #555555; font-size: 15px;">Use the code below to complete your registration. It is valid for <strong>5 minutes</strong>.</p>
  <div style="background-color: #f4f4f6; padding: 16px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #111111; border-radius: 6px; margin: 20px 0;">
    {verification_code}
  </div>
  <p style="color: #888888; font-size: 12px; margin-bottom: 0;">If you didn't request this email, no further action is required.</p>
</div>
"""
        return message
    def send_email(self,sender_email,app_pass):
        receiver_email : str = self.email
        verification_code, timestamp  = self.helper.generate_verification_code()
        subject : str = self.email_subject
        message : str = self.small_little_message_creator(verification_code)
        self.db.Delete(list_of_keys=['email'], list_of_values=[receiver_email],table_name='email_verification')
        self.db.insert(list_of_keys=['email','code','timestamp'], list_of_values=[receiver_email, verification_code, timestamp], table_name='email_verification')
        self.helper.email_send(sender_email=sender_email,sender_password=app_pass,recipient_email=receiver_email,subject=subject,message=message)
    def resend(self,sender_email : str, app_pass : str):
        email : str = self.email
        subject : str = self.email_subject
        new_code, timestamp  = self.helper.generate_verification_code()
        message : str = self.small_little_message_creator(new_code)
        self.db.Update(where_keys=['email'],where_values=[email],table_name='email_verification',update_keys=['code','timestamp'],update_values=[new_code,timestamp])
        self.helper.email_send(sender_email=sender_email,sender_password=app_pass,recipient_email=email,subject=subject,message=message)
    def verify_account(self,code_submitted : str, email : str) -> tuple[bool, str]:
        is_valid, msg = self.db.check_if_correct_code(code_provided=code_submitted,email_user=email)
        if not is_valid:
            return False, msg
        id = self.db.extract_id_main(method='email',value=email,table_name='registration')
        self.db.change_state(state_to_change_to='ACTIVE',ID=id)
        self.db.Delete(list_of_keys=['email'], list_of_values=[email], table_name='email_verification')
        return True, msg
    def tired(self):
        pass
    # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
    def tiredday2(self):
        pass
    # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz even more zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
    def tiredday3(self):
        pass
    # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz zzzzzzzzzzzzzzzzzzz
    def tiredday4(self):
        pass
    # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz