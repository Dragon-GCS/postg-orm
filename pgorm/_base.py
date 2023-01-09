# Author: Dragon
# Python: 3.10
# Created at 2022/12/28 22:14
# Edit with VS Code
# Filename: _base.py
# Description: Orm base class

from abc import ABC
from dataclasses import KW_ONLY, dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class IndexMethod(Enum):
    """ Index method. """

    BTREE = "btree"
    HASH = "hash"
    GIST = "gist"
    SPGIST = "spgist"
    GIN = "gin"
    BRIN = "brin"


@dataclass
class Column(Generic[T]):
    """ The base class for all field types. It contains the common attributes of all field types.

    reference:
        https://www.postgresql.org/docs/15/ddl-constraints.html
        https://www.postgresql.org/docs/15/sql-createtable.html

    Args:
        default: The default value of the field.
        pg_default(str): The default value of the field setting in postgresql.
        column_name(str): The column name, default is field name.
        nullable(bool): Whether the field can be null.
        primary_key(bool): Whether the field is the primary key.
        unique(bool): Whether the field is unique.
        unique_group(int): To define a unique constraint for a group of columns,
            give them the same unique_group number.
        null_not_distinct(bool): Whether the field is unique and null is not distinct,
            only valid when unique=True.
        check(Callable|str|None): The check constraint. It will write to postgresql
            when it is a string, else it only works in python as a function.
        generated(Callable|str|None): The generated constraint. It will write to postgresql
            when it is a string, else it only works in python as a function.
        generated_args(list[str]|None): Field names which should pass to generated function.
        exclude(IndexMethod|None): Table will add exclude constraint when set with an IndexMethod.
        exclude_op(str): The operator for exclude constraint, default is "=".
            Reference: https://www.postgresql.org/docs/15/functions.html
    """

    _pg_type = ""
    _: KW_ONLY
    default: T | None = None
    pg_default: T | None = None                    # default value in postgresql
    column_name: str = ""                          # column name
    nullable: bool = True                          # field type NOT NULL
    primary_key: bool = False                      # field type PRIMARY KEY
    unique: bool = False                           # field type UNIQUE
    unique_group: int | None = None                # UNIQUE (field1, field2, ...)
    null_not_distinct: bool = False                # field type UNIQUE NULLS NOT DISTINCT, only available with unique
    check: Callable[[T], bool] | str | None = None # field type CHECK (field > 0)
    generated: Callable[
        [T], T] | str | None = None                # field type GENERATED ALWAYS AS (height_cm / 2.54) STORED
    generated_args: list[str] | None = None        # field type GENERATED ALWAYS AS (height_cm / 2.54) STORED
    exclude: IndexMethod | None = None             # field type EXCLUDE USING index_method (field WITH =)
    exclude_op: str = "="

    def __new__(cls, *args, **kwargs):
        """Override __new__ to avoid calling another parent class's __new__ method
        For calling super().__new__ correctly, don't pass any parameters to it.
        These parameters will be passed to object.__init__().
        """

        return super().__new__(cls)

    def __sql__(self) -> str:
        """Generate the SQL statement for the field type with the specified attributes"""

        conditions = [self.column_name]
        if self._pg_type:
            conditions.append(self._pg_type)
        if not self.nullable:
            conditions.append("NOT NULL")
        if isinstance(self.check, str):
            conditions.append(f"CHECK ({self.check})")
        if self.pg_default is not None:
            conditions.append(f"DEFAULT {self.pg_default}")
        if isinstance(self.generated, str):
            conditions.append(f"GENERATED ALWAYS AS ({self.generated}) STORED")
        if self.unique and self.unique_group is None:
            conditions.append("UNIQUE")
            if self.null_not_distinct:
                conditions.append("NULLS NOT DISTINCT")
        if self.primary_key:
            conditions.append("PRIMARY KEY")
        return " ".join(conditions)

    def _set_column_name(self, name: str):
        if not self.column_name:
            self.column_name = name
        return self


class Model(ABC):
    __table_name__: str = "model"

    def __init_subclass__(cls) -> None:
        if not cls.__table_name__:
            cls.__table_name__ = cls.__name__.lower()

    @classmethod
    def create(cls):
        ...
