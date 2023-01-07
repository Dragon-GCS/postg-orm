# Author: Dragon
# Python: 3.10
# Created at 2023/01/07 19:45
# Edit with VS Code
# Filename: _exception.py
# Description: pgorm's exception


class CheckError(Exception):
    """Raised when a check constraint is violated."""
