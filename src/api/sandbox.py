import uuid
import tempfile
import os
import ast
import traceback
import sys
import io
import time
import signal
from pathlib import Path
from typing import Any
from contextlib import contextmanager
import multiprocessing

import pandas as pd
import numpy as np

from src.config.settings import settings


class SandboxError(Exception):
    pass


class SandboxTimeoutError(SandboxError):
    pass


class SandboxSecurityError(SandboxError):
    pass


FORBIDDEN_IMPORTS = {
    "os", "subprocess", "sys", "shutil", "socket", "requests",
    "urllib", "http", "ftplib", "smtplib", "telnetlib",
    "pickle", "marshal", "ctypes", "multiprocessing",
    "threading", "signal", "importlib",
}

FORBIDDEN_AST_NODES = {
    "Import", "ImportFrom",
}

ALLOWED_MODULES = {
    "pandas", "numpy", "matplotlib", "plotly",
    "scipy", "sklearn", "statsmodels", "prophet",
    "builtins", "math", "statistics", "datetime",
    "collections", "itertools", "functools", "json",
    "csv", "io", "copy", "typing",
}


def _validate_code_ast(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SandboxSecurityError(f"Syntax error in generated code: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_MODULES:
                    raise SandboxSecurityError(
                        f"Import of '{alias.name}' is not allowed in sandbox."
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] not in ALLOWED_MODULES:
                raise SandboxSecurityError(
                    f"Import from '{node.module}' is not allowed in sandbox."
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "os":
                        raise SandboxSecurityError("os module calls are forbidden.")
                    if node.func.value.id == "subprocess":
                        raise SandboxSecurityError("subprocess module calls are forbidden.")


def _exec_in_sandbox(code: str, local_vars: dict, result_queue: multiprocessing.Queue):
    try:
        import signal as _signal
        if hasattr(_signal, "SIGALRM"):
            _signal.signal(_signal.SIGALRM, lambda s, f: (_ for _ in ()).throw(TimeoutError))

        exec_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "type": type,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "StopIteration": StopIteration,
                "None": None,
                "True": True,
                "False": False,
                "__import__": __import__,
            },
            "pd": pd,
            "np": np,
        }

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        try:
            exec(code, exec_globals, local_vars)
            result = local_vars.get("result", local_vars.get("__result__"))
            stdout_content = stdout_capture.getvalue()
            result_queue.put({
                "success": True,
                "result": result,
                "stdout": stdout_content,
                "stderr": stderr_capture.getvalue(),
            })
        except Exception as e:
            result_queue.put({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
            })
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    except Exception as e:
        result_queue.put({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        })


class PythonSandbox:
    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, code: str, df_registry: dict[str, pd.DataFrame] | None = None) -> dict[str, Any]:
        _validate_code_ast(code)

        local_vars = {}
        if df_registry:
            local_vars.update(df_registry)
            if "df" not in local_vars:
                first_key = next(iter(df_registry))
                local_vars["df"] = df_registry[first_key]

        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=_exec_in_sandbox,
            args=(code, local_vars, result_queue),
        )
        process.start()

        timeout = settings.SANDBOX_TIMEOUT_SECONDS
        process.join(timeout=timeout)

        if process.is_alive():
            process.terminate()
            process.join(timeout=3)
            if process.is_alive():
                process.kill()
            raise SandboxTimeoutError(
                f"Code execution timed out after {timeout} seconds."
            )

        if result_queue.empty():
            return {"success": False, "error": "No result produced.", "traceback": ""}

        output = result_queue.get()
        return output


def execute_with_retry(
    sandbox: PythonSandbox,
    code_generator_fn,
    intent: dict,
    df_registry: dict[str, pd.DataFrame],
    max_retries: int = 3,
) -> dict[str, Any]:
    """Execute code with automatic retry on error."""
    last_error = None

    for attempt in range(max_retries):
        if attempt == 0:
            code = code_generator_fn(intent)
        else:
            code = code_generator_fn(intent, error_context=last_error)

        try:
            result = sandbox.execute(code, df_registry)
            if result.get("success"):
                return result
            last_error = result.get("error", "Unknown error")
        except SandboxError as e:
            last_error = str(e)

    return {
        "success": False,
        "error": f"Failed after {max_retries} attempts. Last error: {last_error}",
        "traceback": "",
    }
