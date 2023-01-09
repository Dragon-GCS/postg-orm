# Author: Dragon
# Python: 3.10
# Created at 2022/12/25 17:24
# Edit with VS Code
# Filename: pg_orm.py
# Description: Base field for pgorm

import datetime
import json
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Type, TypeVar
from uuid import UUID, uuid4

from ._base import Column, Model


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


"""
Here defines some basic type for postgresql.
Including: Integer, Decimal, CharField, VarCharField, TextField, DateField, TimeField, TimeStampField, BooleanField
"""


@dataclass
class IntegerField(Column[int], int):
    """Reference: https://www.postgresql.org/docs/15/datatype-numeric.html#DATATYPE-INT

    SpecialArgs:
        size(Literal[2, 4, 8]): The size of the integer. 2 for smallint, 4 for integer, 8 for bigint.
        auto_increment(bool): Whether the column is a serial.
    """
    size: Literal[2, 4, 8] = 4
    auto_increment: bool = False

    def __post_init__(self):
        # cspell:words SMALLSERIAL BIGSERIAL
        assert self.size in (2, 4, 8), "size must be 2, 4 or 8"
        match self.size:
            case 2: self._pg_type = "SMALLSERIAL" if self.auto_increment else "SMALLINT"
            case 4: self._pg_type = "SERIAL" if self.auto_increment else "INTEGER"
            case 8: self._pg_type = "BIGSERIAL" if self.auto_increment else "BIGINT"

    def __sql__(self) -> str:
        if self.auto_increment:
            return f"{self.column_name} {self._pg_type}"
        return super().__sql__()


@dataclass
class DecimalField(Column[float], float):
    """Reference: https://www.postgresql.org/docs/15/datatype-numeric.html#DATATYPE-FLOAT

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
    """Reference: https://www.postgresql.org/docs/15/datatype-character.html

    SpecialArgs:
        length(int): The length for char
    """
    length: int
    _pg_type = "CHAR"

    def __post_init__(self):
        self._pg_type += f"({self.length})"


@dataclass
class VarCharField(CharField):
    """Reference: https://www.postgresql.org/docs/15/datatype-character.html

    SpecialArgs:
        length(int): The max length for varchar.
    """
    length: int
    _pg_type = "VARCHAR"


@dataclass
class TextField(Column[str], str):
    """Reference: https://www.postgresql.org/docs/15/datatype-character.html"""
    _pg_type = "TEXT"


@dataclass
class DateField(Column[datetime.date], datetime.date):
    """Reference: https://www.postgresql.org/docs/15/datatype-datetime.html"""


@dataclass
class TimeField(Column[datetime.time], datetime.time):
    """Reference: https://www.postgresql.org/docs/15/datatype-datetime.html

    SpecialArgs:
        p(int): The number of fractional digits retained in the seconds. Range of p is from 0 to 6.
        with_timezone(bool): Whether to include the time zone.
    """
    p: int = 0
    with_timezone: bool = False
    _pg_type = "TIME"

    def __post_init__(self):
        assert 0 <= self.p <= 6, "p must be between 0 and 6"
        if self.p:
            self._pg_type += f"({self.p})"
        if self.with_timezone:
            self._pg_type += " WITH TIME ZONE"


@dataclass
class TimestampField(Column[datetime.datetime], datetime.datetime):
    """Reference: https://www.postgresql.org/docs/15/datatype-datetime.html

    SpecialArgs:
        p(int): The number of fractional digits retained in the seconds. Range of p is from 0 to 6.
        with_timezone(bool): Whether to include the time zone.
    """
    p: int = 0
    with_timezone: bool = False
    _pg_type = "TIMESTAMP"
    __post_init__ = TimeField.__post_init__


@dataclass
class BooleanField(Column[bool]):
    """Reference: https://www.postgresql.org/docs/15/datatype-boolean.html"""
    _pg_type = "BOOLEAN"


"""
Here defines some special date need to be declared in advance for creating new type.
Include: EnumField, RangeField
"""


@dataclass
class EnumField(Column[Enum]):
    """Reference: https://www.postgresql.org/docs/15/datatype-enum.html

    SpecialArgs:
        enum(Type[Enum]): The enum type.
        name(str): The name of the enum type.
    """
    name: str = ""
    enum: Type[Enum] = Enum
    _pg_type = ""

    def __post_init__(self):
        if self.pg_default:
            self.pg_default = self.pg_default.value
        self.set_enum(self.enum)

    def __sql__(self) -> str:
        return super().__sql__()

    def _create_type(self):
        """Return the SQL statement to create the enum type."""
        assert self.enum != Enum, "Enum must be init or declare with annotations"
        return f"CREATE TYPE {self.name} AS ENUM ({','.join(str(e.value) for e in self.enum)})"

    def set_enum(self, enum: Type[Enum]):
        """Set the enum type."""
        self.enum = enum
        if not self.name:
            self.name = enum.__name__
        self._pg_type = self.name


@dataclass
class RangeField(Column[range]):
    """Reference: https://www.postgresql.org/docs/15/rangetypes.html
    built-in range include: int4range, int8range, numrange, tsrange, tstzrange, daterange

    SpecialArgs:
        _pg_type(str): The name of the range type, can be built-in or custom.
    """
    _pg_type: str


"""
Here defines some advanced data type.
Include: UUIDField, JsonField, ArrayField, NetWorkField
"""


@dataclass
class UUIDField(Column[UUID], UUID):
    """Reference: https://www.postgresql.org/docs/15/datatype-uuid.html"""
    _pg_type = "UUID"
    default: UUID = uuid4()


Json = dict


@dataclass
class JsonField(Column[Json], Json): # TODO
    """Reference: https://www.postgresql.org/docs/15/datatype-json.html"""
    _pg_type = "JSON"

    def __post_init__(self):
        if self.pg_default:
            self.pg_default = f"'{json.dumps(self.pg_default)}'::json" # type: ignore


T = TypeVar("T")


@dataclass
class ArrayField(Column[list[T]], list[T]): # TODO
    """Reference: https://www.postgresql.org/docs/15/arrays.html

    SpecialArgs:
        unit_type(Type[Column]): The type of the array element.
        size(int | list[int]): The size of the array. If the size is a list,
            it means the size of each dimension, 0 means not limit.
    """
    unit: Column[T] | Type[Column[T]] | str
    size: int | list[int] = 0

    def __post_init__(self):
        if isinstance(self.unit, str):
            self._pg_type = self.unit
        else:
            assert self.unit._pg_type, "unit must be able to determine _pg_type"
            self._pg_type = self.unit._pg_type

        if not isinstance(self.size, list):
            self.size = [self.size]
        for s in self.size:
            self._pg_type += f"[{s or ''}]"


@dataclass
class NetWorkField(Column[str], str):
    """Reference: https://www.postgresql.org/docs/15/datatype-net-types.html"""
    _pg_type: Literal["cidr", "inet", "macaddr", "macaddr8"] = "inet"


"""
Here defines some geometric data type.
Include: PointField, LineField, LineSegField, BoxField, PathField, PolygonField, CircleField.
"""
Number = int | float | complex
Point = tuple[Number, Number]


@dataclass
class PointField(Column[Point], Point):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#id-1.5.7.16.5"""
    _pg_type = "POINT"


Line = LineSeg = Box = tuple[Point, Point]


@dataclass
class LineField(Column[Line], Line):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-LINE"""
    _pg_type = "LINE"


@dataclass
class LineSegField(Column[LineSeg], LineSeg):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-LSEG"""
    _pg_type = "LSEG"


@dataclass
class BoxField(Column[Box], Box):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-BOX"""
    _pg_type = "BOX"


Polygon = list[Point]


@dataclass
class PolygonField(Column[Polygon], Polygon):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-POLYGON"""
    _pg_type = "POLYGON"


Circle = tuple[Point, Number]


@dataclass
class CircleField(Column[Circle], Circle):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-CIRCLE"""
    _pg_type = "CIRCLE"


OpenPath = list[Point]
ClosePath = tuple[Point, ...]


@dataclass
class OpenPathField(Column[OpenPath], OpenPath):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-PATH"""
    _pg_type = "PATH"


@dataclass
class ClosePathField(Column[ClosePath], ClosePath):
    """Reference: https://www.postgresql.org/docs/15/datatype-geometric.html#DATATYPE-PATH"""
    _pg_type = "PATH"
