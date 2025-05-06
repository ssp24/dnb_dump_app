import sys
from cx_Freeze import setup, Executable

include_files = ['logo.gif', (r'C:\Users\Steffi\anaconda3\pkgs\zlib-1.2.13-h8cc25b3_1\zlib.dll', 'zlib.dll')]
packages = ['requests', 'bs4', 'PyQt5', 'cryptography', 'brotli', 'zstandard', 'chardet', 'html5lib', 'simplejson', 'sockschain', 'h2']
exclude_modules = ['PyQt5.QtQml']  # QtQml explizit ausschließen

tcl_includes = []
for tcl_lib in sys.modules:
    if tcl_lib.startswith('tcl'):
        tcl_includes.append(tcl_lib)

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "SRUQueryTool.py",
        base=base,
        icon="logo_square_small.ico",
    )
]

setup(
    name="SRUQueryTool",
    version="0.9",
    description="Ein Tool zum Abfragen der SRU-Schnittstelle der DNB",
    author="SNI",
    options={
        "build_exe": {
            "include_files": include_files,
            "packages": packages,
            "excludes": exclude_modules,
            "include_msvcr": True,
            'include_files': include_files,
            'includes': tcl_includes,
        }
    },
    executables=executables
)
