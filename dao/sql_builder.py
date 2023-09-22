#!-*- coding:utf-8 -*-
# python3.7
# Create time: 2022/10/12 11:00
# Filename:

from typing import Tuple, List

from pypika import MySQLQuery, Table, Order
from pypika import functions as fn
from pypika.queries import QueryBuilder
from pypika.terms import Values


def gen_wheres_part(table_name: str, conditions: dict, args: list = None):
    where_value_list = []
    if args is not None:
        where_value_list.extend(args)
    where_strs = []
    table_str = ''
    if table_name:
        table_str = f'`{table_name}`.'
    for field in conditions:
        condition_value = conditions[field]
        for op in condition_value:
            condition_op_value = condition_value[op]
            op = op.upper()
            match = False

            if op == '=':
                where_strs.append(f"{table_str}{field} = %s")
                match = True
            elif op == '>':
                where_strs.append(f"{table_str}{field} > %s")
                match = True
            elif op == '>=':
                where_strs.append(f"{table_str}{field} >= %s")
                match = True
            elif op == '<':
                where_strs.append(f"{table_str}{field} < %s")
                match = True
            elif op == '<=':
                where_strs.append(f"{table_str}{field} <= %s")
                match = True
            elif op == '!=' or op == '<>':
                where_strs.append(f"{table_str}{field} != %s")
                match = True
            elif op == 'LIKE':
                where_strs.append(f"{table_str}{field} like %s")
                condition_op_value = f'%{condition_op_value}%'
                match = True
            elif op == 'IN':
                condition_value_len = len(condition_op_value)
                if condition_value_len == 0:
                    condition_op_value = ['']
                    condition_value_len = len(condition_op_value)
                where_strs.append(f"{table_str}{field} IN ({','.join(['%s'] * condition_value_len)})")
                match = True
            elif op == 'NOT IN':
                condition_value_len = len(condition_op_value)
                if condition_value_len == 0:
                    condition_op_value = ['']
                    condition_value_len = len(condition_op_value)
                where_strs.append(f"{table_str}{field} NOT IN ({','.join(['%s'] * condition_value_len)})")
                match = True
            elif op == 'BETWEEN':
                condition_value_len = len(condition_op_value)
                where_strs.append(f"{table_str}`{field}` BETWEEN %s AND %s")
                match = True
            else:
                raise Exception(f'{op} 模式暂不支持')

            if match:
                if isinstance(condition_op_value, list) or isinstance(condition_op_value, set):
                    where_value_list.extend(condition_op_value)
                else:
                    where_value_list.append(condition_op_value)
            pass

    return ' AND '.join(where_strs), where_value_list


def gen_wheres(table: Table, q: QueryBuilder, conditions: dict, args: list = None):
    """
    :param table:
    :param q:
    :param conditions: {'date': {'>=': 'value1', '<=': 'value2'}, 'test1': {'=': 'value3'}, 'test2': {'in': []}}
    :param args:
    :return:
    """
    where_value_list = []
    if args is not None:
        where_value_list.extend(args)
    if not conditions:
        return q, where_value_list

    for field in conditions:
        condition_value = conditions[field]
        for op in condition_value:
            condition_op_value = condition_value[op]
            op = op.upper()
            match = False

            if op == '=':
                q = q.where(table[field] == '%s')
                match = True
            elif op == '>':
                q = q.where(table[field] > '%s')
                match = True
            elif op == '>=':
                q = q.where(table[field] >= '%s')
                match = True
            elif op == '<':
                q = q.where(table[field] < '%s')
                match = True
            elif op == '<=':
                q = q.where(table[field] <= '%s')
                match = True
            elif op == '!=' or op == '<>':
                q = q.where(table[field] != '%s')
                match = True
            elif op == 'IS NULL':
                q = q.where(table[field].isnull())
                match = False
            elif op == 'IS NOT NULL':
                q = q.where(table[field].isnotnull())
                match = False
            elif op == 'LIKE':
                q = q.where(table[field].like('%s'))
                condition_op_value = f'%{condition_op_value}%'
                match = True
            elif op == 'IN':
                condition_value_len = len(condition_op_value)
                q = q.where(table[field].isin(['%s'] * condition_value_len))
                match = True
            elif op == 'NOT IN':
                condition_value_len = len(condition_op_value)
                q = q.where(table[field].notin(['%s'] * condition_value_len))
                match = True
            elif op == 'BETWEEN':
                condition_value_len = len(condition_op_value)
                q = q.where(table[field]['%s': '%s'])
                match = True
            else:
                raise Exception(f'{op} 模式暂不支持')

            if match:
                if isinstance(condition_op_value, list) or isinstance(condition_op_value, set):
                    where_value_list.extend(condition_op_value)
                else:
                    where_value_list.append(condition_op_value)
    return q, where_value_list


def gen_select_sql(table_name: str, cols: list, condition: dict = None,
                   sum_item: dict = None, count_item: dict = None, group_by: list = None, order_by: list = None,
                   limit: int = None, offset: int = None):
    """

    :param table_name: 表名
    :param cols: 需要查询的字段，不包含统计字段
    :param condition: 查询条件，见gen_wheres()用法
    :param sum_item: 需要求和的字段。{字段: 字段别名}
    :param count_item: 需要统计数量的字段。{字段: 字段别名}
    :param group_by: 需分组的字段
    :param order_by: 排序字段。[(字段, 排序方法（DESC）)]
    :param limit: 查询条数
    :param offset:
    :return: sql与值
    """
    table = Table(table_name)

    # 查询的字段
    selects = []
    for col in cols:
        if col == '%*':
            selects = [table.star]
            break
        else:
            selects.append(table[col])

    q = MySQLQuery.from_(table).select(*selects)

    if sum_item:
        for key in sum_item:
            q = q.select(fn.Sum(table[key]).as_(sum_item[key]))

    if count_item:
        for key in count_item:
            q = q.select(fn.Count(table[key]).as_(count_item[key]))

    # 查询条件
    where_value_list_all = []
    if condition:
        q, where_value_list_item = gen_wheres(table, q, condition)
        where_value_list_all += where_value_list_item

    if group_by:
        for item in group_by:
            q = q.groupby(table[item])

    if order_by is not None:
        for order in order_by:
            o = order[1]
            o = o.upper()
            if o == 'DESC':
                o = Order.desc
            else:
                o = Order.asc
            q = q.orderby(order[0], order=o)

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)  # 分页步长

    sql = q.get_sql().replace('\'%s\'', '%s')
    return sql, where_value_list_all


def gen_insert_sql(table_name: str, row: dict, update_cols: list = None) -> Tuple[str, List]:
    """
    插入语句
    :param table_name: 表名
    :param row: 单行数据
    :param update_cols: 主键相同时，需要更新的字段
    :return: 一条sql语句
    """
    table = Table(table_name)

    cols, values, str_list = [], [], []
    for k, v in row.items():
        cols.append(k)
        values.append(v)
        str_list.append('%s')

    q = MySQLQuery.into(table).columns(cols).insert(str_list)

    if update_cols:
        for item in update_cols:
            q = q.on_duplicate_key_update(
                table[item],
                Values(table[item])
            )

    sql = q.get_sql().replace('\'%s\'', '%s')
    return sql, values


def gen_insert_sqls(table_name: str, rows: list, update_cols: list = None):
    """
    插入语句
    :param table_name: 表名
    :param rows: 需要插入的多行数据
    :param update_cols: 主键相同时，需要更新的字段
    :return: 一条sql语句，及对应的值
    """
    table = Table(table_name)

    all_cols, values, all_args = [], [], []  # 键、所有的值、所有的%s
    for row in rows:
        tmp_values = []
        tmp_args = []
        if all_cols:
            for col in all_cols:
                tmp_values.append(row[col])
                tmp_args.append('%s')
        else:
            for k, v in row.items():
                all_cols.append(k)
                tmp_values.append(v)
                tmp_args.append('%s')
        values.extend(tmp_values)
        all_args.append(tmp_args)

    q = MySQLQuery.into(table).columns(all_cols)

    for one_args in all_args:
        q = q.insert(one_args)

    if update_cols:
        for item in update_cols:
            q = q.on_duplicate_key_update(
                table[item],
                Values(table[item])
            )

    sql = q.get_sql().replace('\'%s\'', '%s')
    return sql, values


def gen_update_sql(table_name, cols: dict, conditions: dict):
    table = Table(table_name)

    q = MySQLQuery.update(table)
    args = []

    for col in cols:
        q = q.set(col, '%s')
        args.append(cols[col])

    q, args = gen_wheres(table, q, conditions, args)
    sql = q.get_sql().replace('\'%s\'', '%s')
    return sql, args


def gen_delete_sql(table_name, conditions: dict):
    table = Table(table_name)

    q = MySQLQuery.from_(table)

    q, args = gen_wheres(table, q, conditions)
    sql = q.delete().get_sql().replace('\'%s\'', '%s')
    return sql, args
