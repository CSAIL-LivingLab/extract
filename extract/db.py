import sqlite3 as lite
from contextlib import contextmanager

# Database operations
#####################

# TODO use this to implement a streaming API to handle BIG data
def fetch(cursor, batch_size=1e3):
  '''An iterator that uses fetchmany to keep memory usage down'''
  while True:
    records = cursor.fetchmany(int(batch_size))
    if not records:
      break
    for record in records:
      yield record

class MapDB:

  def __init__(self, path):
    self._path = path

  # API
  #####

  @contextmanager
  def cursor(self):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      yield cur
    conn.close()

  # SQL synthesis

  def create_table(self, tablename, columns, primary_key=None):
    column_defs = ['{} {}'.format(col_name, col_type) for col_name, col_type in columns]
    create_table = 'CREATE TABLE {tablename} ({columns}'.format(tablename=tablename,
        columns=','.join(column_defs))
    if primary_key:
      create_table += ', PRIMARY KEY({})'.format(primary_key)
    create_table += ')'
    return create_table, ()

  def drop_table(self, tablename):
    drop_table = 'DROP TABLE IF EXISTS {tablename}'.format(tablename=tablename)
    return drop_table, ()

  def add_column(self, tablename, column_name, column_type):
    add_column = 'ALTER TABLE {tablename} ADD {column_name} {column_type}'.format(
        tablename=tablename, column_name=column_name, column_type=column_type)
    return add_column, ()

  def drop_column(self, tablename, column_name):
    drop_column = 'ALTER TABLE {tablename} DROP COLUMN {column_name}'.format(
        tablename=tablename, column_name=column_name)
    return drop_column, ()

  def insert(self, tablename, record_map):
    attrs, record = record_map.keys(), record_map.values()
    value_placeholders = ['?'] * len(attrs)
    insert = "INSERT INTO {tablename} ({columns}) VALUES ({values})".format(
        tablename=tablename,
        columns=','.join(attrs),
        values=','.join(value_placeholders))
    return insert, record

  def insert_or_replace(self, tablename, record_map):
    attrs, record = record_map.keys(), record_map.values()
    value_placeholders = ['?'] * len(attrs)
    i_or_r = "INSERT OR REPLACE INTO {tablename} ({columns}) VALUES ({values})".format(
        tablename=tablename,
        columns=','.join(attrs),
        values=','.join(value_placeholders))
    return i_or_r, record

