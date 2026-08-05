from ui import _update_code_language, _update_file_types
r1 = _update_code_language('Java')
r2 = _update_file_types('Java')
print(type(r1).__name__, r1)
print(type(r2).__name__, r2)
