# cSpell:word SMALLSERIAL
import unittest

from pydantic import BaseModel

from pgorm import ForeignKey, Model, OnAction
from pgorm.fields import CharField, Decimal, ForeignKey, Integer, VarCharField, TextField


class DemoModel(Model):
    id: int = Integer()

class DemoModel2(Model):
    id: int = Integer()
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
            Integer(2, pg_default=0, column_name="integer").__sql__(), "integer SMALLINT DEFAULT 0"
        )
        self.assertEqual(
            Integer(
                2, auto_increment=True, pg_default=0, check="integer != 0", column_name="integer"
            ).__sql__(), "integer SMALLSERIAL"
        )

    def test_decimal(self):
        decimal = Decimal(5, 3, column_name="decimal", nullable=False, null_not_distinct=True)
        self.assertEqual(decimal.__sql__(), "decimal DECIMAL(5,3) NOT NULL")
        decimal.unique = True
        self.assertEqual(
            decimal.__sql__(), "decimal DECIMAL(5,3) NOT NULL UNIQUE NULLS NOT DISTINCT"
        )

    def test_char(self):
        self.assertEqual(CharField(10, column_name="char").__sql__(), "char CHAR(10)")
        self.assertEqual(VarCharField(10, column_name="varchar").__sql__(), "varchar VARCHAR(10)")
        self.assertEqual(TextField(column_name="text").__sql__(), "text TEXT")


class TestModel(BaseModel):
    # id: int = fields.IntegerField(col_name="id", primary_key=True)
    id: int = Integer()


class TestOrm(unittest.TestCase):
    pass
