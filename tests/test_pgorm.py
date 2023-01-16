# cSpell:word SMALLSERIAL
import unittest
from enum import Enum

from pydantic import BaseModel

from pgorm import (ArrayField, CharField, DecimalField, EnumField, ForeignKey,
                   IntegerField, JsonField, LineField, Model, OnAction,
                   TextField, TimeField, VarCharField)



class DemoModel(Model):
    id: int = IntegerField()

class DemoModel2(Model):
    id: int = IntegerField()
    id2: ForeignKey = ForeignKey(to=DemoModel, on_delete=OnAction.CASCADE, on_update=OnAction.CASCADE, check="id > 0", generated=lambda x:x+1, group=0)


class TestFields(unittest.TestCase):
    def test_foreign_key(self):
        self.assertEqual(
            ForeignKey(
                column_name="foreign_key", to=Model, column="_id", on_delete=OnAction.CASCADE
            ).__sql__(), "foreign_key REFERENCE model (_id) ON DELETE CASCADE"
        )

    def test_integer(self):
        self.assertEqual(
            IntegerField(2, pg_default=0, column_name="integer").__sql__(), "integer SMALLINT DEFAULT 0"
        )
        self.assertEqual(
            IntegerField(
                2, auto_increment=True, pg_default=0, check="integer != 0", column_name="integer"
            ).__sql__(), "integer SMALLSERIAL"
        )

    def test_decimal(self):
        decimal = DecimalField(5, 3, column_name="decimal", nullable=False, null_not_distinct=True)
        self.assertEqual(decimal.__sql__(), "decimal DECIMAL(5,3) NOT NULL")
        decimal.unique = True
        self.assertEqual(
            decimal.__sql__(), "decimal DECIMAL(5,3) NOT NULL UNIQUE NULLS NOT DISTINCT"
        )

    def test_char(self):
        self.assertEqual(CharField(10, column_name="char").__sql__(), "char CHAR(10)")
        self.assertEqual(VarCharField(10, column_name="varchar").__sql__(), "varchar VARCHAR(10)")
        self.assertEqual(TextField(column_name="text").__sql__(), "text TEXT")

    def test_enum(self):
        class Num(Enum):
            a = 1
            b = 2

        a = EnumField(enum=Num, column_name="enum", pg_default=Num.a)
        self.assertEqual(a._create_type(), "CREATE TYPE Num AS ENUM (1,2)")
        self.assertEqual(a.__sql__(), "enum Num DEFAULT 1")

    def test_geometric(self):
        self.assertEqual(
            LineField(column_name="line", pg_default=((1, 2), (3, 4))).__sql__(),
            "line LINE DEFAULT ((1, 2), (3, 4))"
        )

    def test_json(self):
        self.assertEqual(
            JsonField(column_name="json", pg_default={"a": 1}).__sql__(),
            "json JSON DEFAULT '{\"a\": 1}'::json"
        )

    def test_array(self):
        self.assertEqual(
            ArrayField(IntegerField(4), size=[0, 5], column_name="numbers").__sql__(),
            "numbers INTEGER[][5]"
        )

class TestModel(BaseModel):
    # id: int = fields.IntegerField(col_name="id", primary_key=True)
    id: int = IntegerField()


class TestOrm(unittest.TestCase):
    pass
