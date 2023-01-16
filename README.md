# Pg-Orm

A simple orm for postgresql

## TODO

- field类型适配asyncpg
- field禁用某些参数
- Model需要保存哪些字段，column_name, column_var_name, primary_key, partition_key
- Model create_table, add_partition
- Model兼容pydantic
- Query类，支持链式调用，join、filter、order_by、limit、offset、group_by、distinct、update、delete...
- Database，继承asyncpg connect，create(Model), update(instance), delete(instance), select(args, **kwargs), save(instance)
