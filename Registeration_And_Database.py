import shutil, pathlib, os, importlib,sys,subprocess, sqlite3
import types
from typing import TypeAlias
from time import sleep

ImportModule : TypeAlias = types.ModuleType

class ImportingListMismatch(Exception):
    """Error raised when pip package name and runtime module name lists do not match in size."""
    pass
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
    def __init__(self,db_file : pathlib.Path | str) -> None:
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.table_name = None
        self.schemas = {
            'registration': ['id', 'username', 'email', 'password', 'country_code', 'contact_number', 'account_status',
                             'created_at', 'last_login'],
            'email_verification': ['id', 'email', 'code', 'timestamp']}
        self.Table_initialization()

    def Table_initialization(self,table_name : str = 'registration') -> None:
        clean_table_name = "".join(char for char in table_name if char.isalnum() or char == '_')
        self.table_name = clean_table_name
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {clean_table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        email TEXT CHECK (email LIKE '%_@__%.%_'),
        password TEXT NOT NULL,
        country_code TEXT DEFAULT '+91' CHECK (length(country_code) <= 5),
        contact_number INTEGER NOT NULL CHECK(length(cast(contact_number as TEXT)) BETWEEN 7 AND 15),
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
    def find(self,list_of_values : list = None, list_of_keys : list = None, return_all : bool = False, table_name : str | None = None) -> list:
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

    def change_state(self,state_to_change_to : str = None, ID : int = 0) -> None:
        if state_to_change_to is None:
            raise EmptyParams('The parameter state_to_change_to was not provided.')
        if state_to_change_to not in ['ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION']:
            raise InvalidParams('Parameters DO NOT MATCH THE LIST IN FUNCTION (change_state)')
        if ID == 0:
            raise InvalidParams('The ID was NOT provided.')
        self.cursor.execute(f"SELECT MAX(id) FROM {self.table_name}")
        actual_max_id = self.cursor.fetchone()[0] or 0
        if ID > actual_max_id:
            raise InvalidParams('The ID provided is Greater then the entries in the Table')
        self.Update(update_keys=['account_status'], update_values=[state_to_change_to], where_keys=['id'],
                    where_values=[ID], table_name=self.table_name)


class Register:
    def __init__(self, db : Database | pathlib.Path, username: str, password: str, email: str, contact: int, country_code: str) -> None:
        self.db = db
        self.modules: dict[str, ImportModule] = self.library_initialization()
        self.username: str = username
        self.email: str = email
        self.contact: int = contact
        self.country_code: str = country_code
        self.password_hash: str | None = None
        self.hash_password(password)
    # Importing Libraries
    @staticmethod
    def Ensure_Library(module_name: str, pip_accepted_name: None | str = None) -> None:
        pip_accepted_name = module_name if pip_accepted_name is None else pip_accepted_name
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_accepted_name])
                importlib.invalidate_caches()
            except Exception:
                sys.exit(1)
    def library_initialization(self) -> dict:
        libraries = ['argon2']
        pip_accepted = ['argon2-cffi']
        if len(libraries) != len(pip_accepted):
            raise ImportingListMismatch('The Lists DO NOT MATCH')

        modules_to_import : dict[str,ImportModule] = {}
        for lib_name, pip_name in zip(libraries, pip_accepted):
            self.Ensure_Library(module_name=lib_name, pip_accepted_name=pip_name)
            modules_to_import[lib_name] = importlib.import_module(lib_name)
        return modules_to_import
    def hash_password(self, password : str) -> None:
        passwordhasher = self.modules['argon2'].PasswordHasher
        ph = passwordhasher()
        self.password_hash = ph.hash(password)

    def check_existence(self, list_of_fields: list, list_of_values: list) -> bool:
        return True if len(self.db.find(list_of_keys=list_of_fields, list_of_values=list_of_values)) > 0 else False

    @property
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
    def tired(self):
        pass
    # zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz