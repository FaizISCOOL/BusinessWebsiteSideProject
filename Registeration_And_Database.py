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

class Database:
    def __init__(self,db_file : pathlib.Path | str) -> None:
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.table_name = None
        self.Table_initialization()
        self.list_table_keys = ['id', 'username', 'email', 'password', 'country_code', 'contact_number',
                                'account_status', 'created_at', 'last_login']
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
        account_status TEXT DEFAULT 'ACTIVE' CHECK(account_status IN ('ACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP);""")

        self.cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{clean_table_name}_username 
            ON {clean_table_name} (username);
            """)
        self.conn.commit()
    def key_match(self,key_values: list) -> None:
        output = set(key_values).issubset(self.list_table_keys)
        if not output:
            raise DatasetKeyMismatch('The key values provided DOES NOT MATCH the table')
    # To ensure The keys are accurate to the ones made when initializing the table
    def find(self,list_of_values : list = None, list_of_keys : list = None, return_all : bool = False) -> list:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        self.key_match(list_of_keys)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys and return_all:
            self.cursor.execute(f"SELECT * FROM {self.table_name}")
            return self.cursor.fetchall()
        elif not list_of_keys and not return_all:
            raise EmptyList("NO keys Provided / return_all is set to False")
        query = [f'{key} = ?' for key in list_of_keys]
        where_conditions  = ' AND '.join(query)
        final_query = f'SELECT * FROM {self.table_name} WHERE {where_conditions}'
        self.cursor.execute(final_query, list_of_values)
        return self.cursor.fetchall()
    def insert(self, list_of_values : list = None, list_of_keys : list = None) -> None:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        self.key_match(list_of_keys)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys:
            raise EmptyList("NO keys Provided")
        columns = ', '.join(list_of_keys)
        placeholders = ['?' for _ in list_of_keys]
        placeholders = ', '.join(placeholders)
        final_query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(final_query, list_of_values)
        self.conn.commit()
    def Delete(self, list_of_values : list = None, list_of_keys : list = None) -> None:
        if list_of_values is None: list_of_values = []
        if list_of_keys is None: list_of_keys = []
        self.key_match(list_of_keys)
        if len(list_of_values) != len(list_of_keys):
            raise DatabaseListMismatch("List Length Mismatch")
        if not list_of_keys:
            raise EmptyList("NO keys Provided")
        conditional_key = [f"{key} = ?" for key in list_of_keys]
        query = ' AND '.join(conditional_key)
        final_query = f"DELETE FROM {self.table_name} WHERE {query}"
        self.cursor.execute(final_query, list_of_values)
        self.conn.commit()
    def Update(self, update_keys : list = None, update_values : list = None,where_keys : list = None, where_values : list = None) -> None:
        if update_keys is None: update_keys = []
        if update_values is None: update_values = []
        if where_keys is None: where_keys = []
        if where_values is None: where_values = []
        self.key_match(update_keys)
        self.key_match(where_keys)
        if (len(update_keys) != len(update_values)) or (len(where_keys) != len(where_values)):
            raise DatabaseListMismatch("List Length Mismatch")
        if not update_keys or not where_keys:
            raise EmptyList("NO keys Provided")
        set_update_keys = [f"{key} = ?" for key in update_keys]
        set_query = ', '.join(set_update_keys)
        where_condition_key = [f'{key2} = ?' for key2 in where_keys]
        where_query = ' AND '.join(where_condition_key)
        final_query = f"UPDATE {self.table_name} SET {set_query} WHERE {where_query}"
        values = update_values + where_values
        self.cursor.execute(final_query, values)
        self.conn.commit()

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
    def check_existence(self,list_of_fields : list, list_of_values: list) -> bool:
        return True if len(self.db.find(list_of_values,list_of_fields)) > 0 else False
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