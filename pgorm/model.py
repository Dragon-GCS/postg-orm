# Author: Dragon
# Python: 3.10
# Created at 2022/12/23 20:31
# Edit with VS Code
# Filename: pg_orm.py
# Description: A simple ORM for PostgreSQL


from collections import defaultdict
from typing import Any, ClassVar, Sequence, TypeVar
from itertools import filterfalse

from pydantic.main import BaseModel, ModelMetaclass
from typing_extensions import dataclass_transform

from ._base import Column
from .fields import ForeignKey, OnAction


T = TypeVar("T")

def _create_init(attrs: dict[str, Any]):
    """Create __init__ method in class attrs"""
    args, locals = ["self", "*"], {"__builtins__": None}
    for name, value in attrs["__fields__"].items():
        arg_name = name
        if typ := attrs["__annotations__"].get(name):
            locals[f"_typ_{name}"] = typ
            arg_name = f"{name}:_typ_{name}"
        locals[f"_dft_{name}"] = value.default
        args.append(f"{arg_name}=_dft_{name}")

    attrs["_init_txt"] = f"def __init__({','.join(args)}):\n" + \
        '\n'.join(f'  self.{key} = {key}' for key in attrs["__fields__"].keys()) or '  pass'
    exec(attrs["_init_txt"], locals, attrs)


def _covert_underline(name: str) -> str:
    """Convert camel case to underline case"""
    return "".join(
        (name[0].lower(), *[f"_{char.lower()}" if char.isupper() else char for char in name[1:]])
    )


def _valid_same_item(_iter: Sequence[T], name: str) -> T:
    """Valid all the items in iter are same"""
    assert len(set(_iter)) == 1, f"All value for {name} must be same"
    return _iter[0]


@dataclass_transform(kw_only_default=True, field_specifiers=(Column, ))
class MetaModel(ModelMetaclass):
    """Meta class for base model, this class will create __init__ method for model,
    and filter the columns to __fields__ attribute.
    """
    def __new__(cls, name: str, bases: tuple, attrs: dict[str, Any], **kwargs):
        """
        Args:
            name(str): The name of the class being created.
            bases(tuple): A tuple of the base classes, in the order of their occurrence in the base class list.
            attrs(dict): A dictionary containing the class attributes.
            kwargs(dict): The keyword arguments passed to the class statement.
        """
        fields = {}
        annotations = {}
        for base in reversed(bases):
            if base.__module__.startswith(("pgorm.", "pydantic.")):
                continue
            fields.update(base.__fields__)
            annotations.update(base.__annotations__)
        annotations.update(attrs.get('__annotations__', {}))

        for key, value in attrs.items():
            if isinstance(value, Column):
                value._set_column_name(key)
                fields[key] = value
                annotations[key] = attrs.get('__annotations__', {}).get(key, Any)

        attrs["__fields__"] = fields
        attrs["__fields_set__"] = set(fields.keys())
        attrs["__annotations__"] = annotations
        attrs["__table_name__"] = attrs.get("__table_name__", _covert_underline(name))
        attrs["__schema__"] = attrs.get("__schema__", "public")
        if name != "Model":
            _create_init(attrs)
        cls = type.__new__(cls, name, bases, attrs)
        return cls


# TODO: create database class and query class, use model like: db.query(MyModel).filter(id=1).all()


class Model(metaclass=MetaModel):   # TODO: inherit from pydantic.BaseModel
    __table_name__: ClassVar[str]           # The table name of the model
    __schema__: ClassVar[str]               # The schema of the model
    pk: ClassVar[list[str]]                 # The primary keys of the model
    foreign: ClassVar[set["Model"]]       # The foreign model of the model
    _init_txt: ClassVar[str]                # The __init__ method text
    __fields__: ClassVar[dict[str, Column]] # The columns of the model
    __fields_set__: ClassVar[set[str]]      # The columns' name set of the model

    # TODO: use Columns.check to check the columns value, create setattr and getattr method.
    # TODO: create_table sql -> owner change
    # TODO: to_dict method
    # TODO: foreign key and many to many
    @classmethod
    def create_table(cls):
        foreign_model = set()
        field_txt, pk, partition, unique, foreign = [], [], [], defaultdict(list), defaultdict(list)
        for field in cls.__fields__.values():
            field_txt.append(field.__sql__())
            # group primary key
            if field.primary_key:
                pk.append(field.column_name)
            # group unique constraint
            if field.unique_group is not None:
                unique[field.unique_group].append(field.column_name)
            # group foreign constraint
            if isinstance(field, ForeignKey):
                foreign_model.add(field.to)
                if field.group:
                    foreign[field.group].append(field)
            # add partition key
            if field.partition is not None:
                partition.append(field)
        if pk:
            field_txt.append(f"PRIMARY KEY ({','.join(pk)})")
        for names in unique.values():
            field_txt.append(f"UNIQUE ({','.join(names)})")
        for fields in foreign.values():
            ref_table = _valid_same_item([field.to for field in fields], "foreign table")
            _txt = f"FOREIGN KEY ({','.join(field.column_name for field in fields)}) " \
                f"REFERENCES {ref_table} ({','.join(field.column for field in fields)})"
            if (on_delete := _valid_same_item([field.on_delete for field in fields],
                                              "on delete")) != OnAction.NO_ACTION:
                _txt += f" ON DELETE {on_delete}"
            if (on_update := _valid_same_item([field.on_update for field in fields],
                                              "on update")) != OnAction.NO_ACTION:
                _txt += f" ON UPDATE {on_update}"
            field_txt.append(_txt)
        table = f"{cls.__schema__}.{cls.__table_name__}" if cls.__schema__ != "public" else cls.__table_name__
        sql = "\n".join((f"CREATE TABLE IF NOT EXISTS {table} (", ',\n'.join(field_txt), ")"))
        if partition: # TODO: partition key's check
            columns = [field.column_name for field in partition]
            # assert set(columns) <= set(pk), "partition key must be primary key"
            # assert set(columns) <= set(unique) , "partition key must be same"
            method = _valid_same_item([field.partition for field in partition], "partition method")
            sql += f" PARTITION BY {method.value} ({','.join(columns)})"
        return sql


    def to_dict(self):
        for name, field in self.__fields__.items():
            print(field.__sql__())
