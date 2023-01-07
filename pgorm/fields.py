# Author: Dragon
# Python: 3.10
# Created at 2022/12/25 17:24
# Edit with VS Code
# Filename: pg_orm.py
# Description: Base field for pgorm

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Type

from ._base import Column, Model
from ._exception import CheckError


class OnAction(Enum):
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    NO_ACTION = "NO ACTION"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"


@dataclass
class ForeignKey(Column):
    """The foreign key constraint.

    reference: https://www.postgresql.org/docs/15/ddl-constraints.html#DDL-CONSTRAINTS-FK

    Args:
        to: The model class of the foreign key.
        column(str): The column name of the foreign key
        on_delete(OnAction): The action to take when the referenced row is deleted.
        on_update(OnAction): The action to take when the referenced row is updated.
        group(int): To reference a group of columns, give them the same unique_group number.
    """

    to: Type["Model"]
    column: str = ""
    on_delete: OnAction = OnAction.NO_ACTION
    on_update: OnAction = OnAction.NO_ACTION
    group: int | None = None

    def __sql__(self) -> str:
        if self.group is not None:
            return super().__sql__()
        conditions = [super().__sql__(), f"REFERENCE {self.to.__table_name__}"]
        if self.column:
            conditions.append(f"({self.column})")
        if self.on_delete != OnAction.NO_ACTION:
            conditions.append(f"ON DELETE {self.on_delete.value}")
        if self.on_update != OnAction.NO_ACTION:
            conditions.append(f"ON UPDATE {self.on_update.value}")
        return " ".join(conditions)


@dataclass
class Integer(Column[int], int):
    """Integer data type

    reference: https://www.postgresql.org/docs/15/datatype-numeric.html#DATATYPE-INT

    SpecialArgs:
        size(Literal[2, 4, 8]): The size of the integer. 2 for smallint, 4 for integer, 8 for bigint.
        auto_increment(bool): Whether the column is a serial.
    """
    size: Literal[2, 4, 8] = 4
    auto_increment: bool = False

    def __post_init__(self):
        # cspell:words SMALLSERIAL BIGSERIAL
        match self.size:
            case 2: self._pg_type = "SMALLINT" if not self.auto_increment else "SMALLSERIAL"
            case 4: self._pg_type = "INTEGER" if not self.auto_increment else "SERIAL"
            case 8: self._pg_type = "BIGINT" if not self.auto_increment else "BIGSERIAL"
            case _: raise ValueError("size must be 2, 4 or 8")

    def __sql__(self) -> str:
        if self.auto_increment:
            return f"{self.column_name} {self._pg_type}"
        return super().__sql__()


@dataclass
class Decimal(Column[float], float):
    """Decimal data type

    reference: https://www.postgresql.org/docs/15/datatype-numeric.html#DATATYPE-FLOAT

    SpecialArgs:
        precision(int | None): total number of digits
        scale(int | None): number of digits after the decimal point
    """
    precision: int | None = None
    scale: int | None = None
    _pg_type = "DECIMAL"

    def __post_init__(self):
        assert not self.precision or self.precision > 0, "precision must be positive"
        if self.scale == 0:
            return
        terms = ""
        if self.precision:
            terms += f"{self.precision}"
        if self.scale:
            terms += f",{self.scale}"
        if terms:
            self._pg_type += f"({terms})"


@dataclass
class CharField(Column[str], str):
    """Char, Varchar, Text data type

    reference: https://www.postgresql.org/docs/15/datatype-character.html

    Args:
        length(int): The length for char
    """
    length: int
    _pg_type = "CHAR"

    def __post_init__(self):
        self._pg_type += f"({self.length})"


@dataclass
class VarCharField(CharField):
    """Varchar data type

    reference: https://www.postgresql.org/docs/15/datatype-character.html

    Args:
        length(int): The max length for varchar.
    """
    length: int
    _pg_type = "VARCHAR"


@dataclass
class TextField(Column[str], str):
    _pg_type = "TEXT"



