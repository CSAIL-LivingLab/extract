import sys
from . import FieldExtractor
from os import mkdir, path
import sqlite3 as lite

# database name
PROJECT_DB = 'project.db'

# table names
TXT_TABLE = 'txt'
LABEL_TABLE = 'label'
EXTRACTION_TABLE = 'extraction'

# column names
RECORD_ID = 'record_id'
TXT_RECORD = 'txt_record'

class Project:

  PROJECTS = 'projects'

  @staticmethod
  def new_project(name, f):
    # check for name collisions
    project_path = path.join(Project.PROJECTS, name)
    if path.exists(project_path):
      raise ValueError("Project with name '{}' already exists".format(name))

    project = Project(name)
    mkdir(project.path)

    # txt table
    txt_header = [
        '{record_id} int'.format(record_id=RECORD_ID),
        '{txt_record} TEXT'.format(txt_record=TXT_RECORD),
        'PRIMARY KEY ({record_id})'.format(record_id=RECORD_ID)
    ]
    create_table(project.db(), TXT_TABLE, txt_header)
    insert_into(project.db(), TXT_TABLE, enumerate(f))

    return project

  @staticmethod
  def load_projects():
    projects = []
    for project_name in next(walk(Project.PROJECTS))[1]:
      projects.append(Project(project_name))
    return projects

  def __init__(self, name):
    self.name = name
    self.path = path.join(Project.PROJECTS, self.name)

  def db(self):
    return path.join(self.path, PROJECT_DB)

  def get_fields(self):
    cols = column_names(self.db(), LABEL_TABLE)
    # skip id column
    return cols[1:]

  def set_fields(self, fields):
    # TODO don't just drop table without asking
    drop_table(self.db(), LABEL_TABLE)

    label_header = ['{record_id} int'.format(record_id=RECORD_ID)]
    for field in fields:
      label_header.append('{field} TEXT'.format(field=field))
    # TODO use FOREIGN KEY instead of PRIMARY KEY
    label_header.append('PRIMARY KEY ({record_id})'.format(record_id=RECORD_ID))

    create_table(self.db(), LABEL_TABLE, label_header)

  def unlabeled_sample(self, n):
    def sql(cur):
      # SELECT txt.record_id, txt.txt_record
      # FROM txt, labels
      # WHERE txt.record_id NOT IN (SELECT record_id FROM labels)
      # LIMIT n
      query = 'SELECT {txt}.{record_id},{txt}.{txt_record}'.format(
          txt=TXT_TABLE, record_id=RECORD_ID, txt_record=TXT_RECORD)
      query += ' FROM {txt}'.format(
          txt=TXT_TABLE)
      label_ids = '(SELECT {record_id} FROM {labels})'.format(
          record_id=RECORD_ID, labels=LABEL_TABLE)
      query += ' WHERE {txt}.{record_id} NOT IN {label_ids}'.format(
          txt=TXT_TABLE, record_id=RECORD_ID, label_ids=label_ids)
      query += ' LIMIT {limit}'.format(
          limit=n)
      cur.execute(query)
      return cur.fetchall()
    sample = safe_sql(self.db(), sql)
    return sample

  def set_labels(self, labels):
    # labels is a list of tuples : (txt_id, csv_list)
    # eg. (8, ['2012-04-02', '00:01:56', '127.0.0.1:54321', '127.2.2.67890'])
    label_records = [[label[0]] + label[1] for label in labels]
    insert_into(self.db(), LABEL_TABLE, label_records)

  def training_set(self):
    def sql(cur):
      query = 'SELECT {txt_record},{fields}'.format(
          txt_record=TXT_RECORD, fields=','.join(self.get_fields()))
      query += ' FROM {txt},{labels}'.format(
          txt=TXT_TABLE, labels=LABEL_TABLE)
      query += ' WHERE {txt}.{record_id}={labels}.{record_id}'.format(
          txt=TXT_TABLE, record_id=RECORD_ID, labels=LABEL_TABLE)
      cur.execute(query)
      return cur.fetchall()
    training_txt_records, training_txt_labels = [], []
    for training_example in safe_sql(self.db(), sql):
      training_txt_records.append(training_example[0])
      training_txt_labels.append(training_example[1:])
    return training_txt_records, training_txt_labels

  def extract(self):
    drop_table(self.db(), EXTRACTION_TABLE)

    # extraction header
    fields = self.get_fields()
    extraction_header = ['{record_id} int'.format(record_id=RECORD_ID)]
    for field in fields:
      extraction_header.append('{field} TEXT'.format(field=field))
    # TODO use FOREIGN KEY instead of PRIMARY KEY
    extraction_header.append('PRIMARY KEY ({record_id})'.format(record_id=RECORD_ID))

    create_table(self.db(), EXTRACTION_TABLE, extraction_header)

    fe = FieldExtractor(fields)
    fe.train(*self.training_set())

    # TODO keep track of record_id so that we can insert results into extraction table
    def sql(cur):
      cur.execute('SELECT {txt_record} FROM {txt}'.format(txt_record=TXT_RECORD, txt=TXT_TABLE))
      return cur.fetchall()
    txt_records = [txt_record[0] for txt_record in safe_sql(self.db(), sql)]
    extraction_records = fe.extract(txt_records)
    print 'EXTRACTION:'
    for extraction_record in extraction_records:
      print '\t',extraction_record
    #insert_into(self.db(), EXTRACTION_TABLE, extraction_records)

# Database operations
#####################

def create_table(db, tablename, columns):
  def sql(cur):
    cur.execute('CREATE TABLE {tablename} ({columns})'.format(tablename=tablename,
        columns=','.join(columns)))
  safe_sql(db, sql)

def drop_table(db, tablename):
  def sql(cur):
    cur.execute('DROP TABLE IF EXISTS {tablename}'.format(tablename=tablename))
  safe_sql(db, sql)

def table_info(db, tablename):
  def sql(cur):
    cur.execute('PRAGMA table_info({tablename})'.format(tablename=tablename))
    return cur.fetchall()
  ti = safe_sql(db, sql)
  return ti

def column_names(db, tablename):
  return [column[1] for column in table_info(db, tablename)]

def insert_into(db, tablename, records):
  cols = column_names(db, tablename)
  value_placeholders = ['?'] * len(cols)
  def sql(cur):
    for record in records:
      insert = "INSERT INTO {tablename} ({column_names}) VALUES ({values})".format(
          tablename=tablename, column_names=','.join(cols), values=','.join(value_placeholders))
      cur.execute(insert, record)
  safe_sql(db, sql)

def safe_sql(db, func):
  con = None
  result = None
  try:
    with lite.connect(db) as con:
      cur = con.cursor()
      result = func(cur)

  except lite.Error, e:
    print "Error %s:" % e.args[0]
    # TODO should we exit on DB error?
    #sys.exit(1)

  finally:
    if con:
      con.close()

  return result

# small test example
####################

FIELDS = ['date', 'time', 'src','dest']
#FIELDS = ['date', 'time', 'src_prefix', 'src', 'dest_prefix', 'dest']
LABELS = [
    (0,['2012-01-04', '00:01:23','127.0.0.1:32981','127.0.0.1:50010']),
    #(0,['2012-01-04', '00:01:23', 'src: /', '127.0.0.1:32981', 'dest: /', '127.0.0.1:50010']),
    (2,['2012-01-04', '00:01:23', '',''])
    #(2,['2012-01-04', '00:01:23', '','', '', ''])
]

if __name__ == '__main__':
  filename = sys.argv[1]
  project_name = sys.argv[2]
  with open(filename) as f:
    project = Project.new_project(project_name, f)
    project.set_fields(FIELDS)
    project.set_labels(LABELS)
    print 'Unlabeled sample:', project.unlabeled_sample(5)
    project.extract()
