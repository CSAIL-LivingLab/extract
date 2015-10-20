import sqlite3 as lite

# Database operations
#####################

class SqlDatabase:

  def __init__(self, path):
    self._path = path

  # API
  #####

  def create_table(self, tablename, columns):
    column_defs = ['{} {}'.format(col_name, col_type) for col_name, col_type in columns]
    create_table = 'CREATE TABLE {tablename} ({columns})'.format(tablename=tablename,
        columns=','.join(column_defs))
    self.sql([(create_table, ())])

  def drop_table(self, tablename):
    drop_table = 'DROP TABLE IF EXISTS {tablename}'.format(tablename=tablename)
    self.sql([(drop_table, ())])

  def add_column(self, tablename, column_name, column_type):
    add_column = 'ALTER TABLE {tablename} ADD {column_name} {column_type}'.format(
        tablename=tablename, column_name=column_name, column_type=column_type)
    self.sql([(add_column, ())])

  def drop_column(self, tablename, column_name):
    drop_column = 'ALTER TABLE {tablename} DROP COLUMN {column_name}'.format(
        tablename=tablename, column_name=column_name)
    self.sql([(drop_column, ())])

  # Streaming API
  ###############

  def sql(self, queries):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      for query, params in queries:
        cur.execute(query, params)
      return SqlDatabase.fetch(cur)
    conn.close()

  def insert_into(self, tablename, records):
    self.sql(self._insert(tablename, record) for record in records)

  # convenience
  #############

  def _insert(self, tablename, record):
    value_placeholders = ['?'] * len(record)
    insert = "INSERT INTO {tablename} ({column_names}) VALUES ({values})".format(
        tablename=tablename,
        column_names=','.join(record.keys()),
        values=','.join(value_placeholders))
    return insert, record.values()

  @staticmethod
  def fetch(cursor, batch_size=1e3):
    '''An iterator that uses fetchmany to keep memory usage down'''
    while True:
      records = cursor.fetchmany(int(batch_size))
      if not records:
        break
      for record in records:
        yield record
