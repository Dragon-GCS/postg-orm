import unittest
from pgorm.fields import IntegerField, VarCharField, DateField, OpenPath, OpenPathField

from pgorm.model import Model
from pgorm import PartitionMethod
import datetime


class MyModel(Model):
    __schema__ = "test"
    id: int = IntegerField(8, partition=PartitionMethod.HASH, nullable=False)
    name: str = VarCharField(length=20, default="test")
    level: int = IntegerField(8, default=1, unique=True)
    name_en: str = VarCharField(length=20, default="test", unique=True)
    date: datetime.date = DateField(default=datetime.date.today())
    path: OpenPath = OpenPathField()


model = MyModel(id = 1)


# class TestModel(unittest.TestCase):

#     def test_model(self):
#         model = MyModel(id = 1)
#         print(model)
#         print(MyModel.create_table())

# if __name__ == '__main__':
#     unittest.main()
