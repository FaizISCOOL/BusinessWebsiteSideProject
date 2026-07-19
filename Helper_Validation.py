import secrets
from datetime import datetime, timedelta
import importlib
import sys
import subprocess
import types
from typing import TypeAlias
ImportModule: TypeAlias = types.ModuleType
class ImportingListMismatch(Exception):
    """Error raised when pip package name and runtime module name lists do not match in size."""
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