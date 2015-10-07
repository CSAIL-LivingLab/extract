from .extract import FieldExtractor
from os import mkdir, path, walk
import sqlite3 as lite
import sys

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
  def load_projects(projects_dir=PROJECTS):
    projects = []
    for project_name in next(walk(projects_dir))[1]:
      projects.append(Project(project_name))
    return projects

  @staticmethod
  def load_project(name, projects_dir=PROJECTS):
    for project_name in next(walk(projects_dir))[1]:
      if name == project_name:
        return Project(project_name)
    raise ValueError("No project with name '{}' found in {}".format(name, projects_dir))

  def __init__(self, name):
    self.name = name
    self.path = path.join(Project.PROJECTS, self.name)

  def db(self):
    return path.join(self.path, PROJECT_DB)

  def get_fields(self):
    cols = column_names(self.db(), LABEL_TABLE)
    return cols[1:] # skip id column

  def set_fields(self, fields):
    drop_table(self.db(), LABEL_TABLE)
    create_table(self.db(), LABEL_TABLE, self.standard_header(fields))

  def standard_header(self, fields=None):
    if not fields:
      fields = self.get_fields()

    header = ['{record_id} int'.format(record_id=RECORD_ID)]
    for field in fields:
      header.append('{field} TEXT'.format(field=field))
    # TODO use FOREIGN KEY instead of PRIMARY KEY
    header.append('PRIMARY KEY ({record_id})'.format(record_id=RECORD_ID))
    return header

  def get_labels(self):
    return select_all(self.db(), LABEL_TABLE)

  def unlabeled_sample(self, n):
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
    return self.safe_query(query)

  def set_labels(self, labels):
    # labels is a list of tuples : (txt_id, csv_list)
    # eg. (8, ['2012-04-02', '00:01:56', '127.0.0.1:54321', '127.2.2.67890'])
    label_records = [[label[0]] + label[1] for label in labels]
    insert_into(self.db(), LABEL_TABLE, label_records)

  def training_set(self):
    query = 'SELECT {txt_record},{fields}'.format(txt_record=TXT_RECORD,
        fields=','.join(self.get_fields()))
    query += ' FROM {txt},{labels}'.format(
        txt=TXT_TABLE, labels=LABEL_TABLE)
    query += ' WHERE {txt}.{record_id}={labels}.{record_id}'.format(
        txt=TXT_TABLE, record_id=RECORD_ID, labels=LABEL_TABLE)

    X_txt, Y_csv = [], []
    for training_example in self.safe_query(query):
      X_txt.append(training_example[0])
      Y_csv.append(training_example[1:])
    return X_txt, Y_csv

  def extract(self):
    # create fresh extraction table
    drop_table(self.db(), EXTRACTION_TABLE)
    create_table(self.db(), EXTRACTION_TABLE, self.standard_header())

    # TODO consider FieldExtractor API
    fe = FieldExtractor(self.get_fields())
    fe.train(*self.training_set())

    txt = select_all(self.db(), TXT_TABLE)
    extractions = fe.extract([txt_record for _,txt_record in txt])

    # TODO stream this??
    extraction_records = []
    for i in range(len(txt)):
      record_id = txt[i][0]
      extraction_record = [record_id] + extractions[i]
      extraction_records.append(extraction_record)

    insert_into(self.db(), EXTRACTION_TABLE, extraction_records)

  def get_extraction(self):
    # TODO join with txt_table to view txt and extraction side by side?
    return select_all(self.db(), EXTRACTION_TABLE)

  def safe_query(self, query):
    def sql(cur):
      cur.execute(query)
      return cur.fetchall()
    return safe_sql(self.db(), sql)

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

def select_all(db, tablename):
  def sql(cur):
    cur.execute('SELECT * FROM {tablename}'.format(tablename=tablename))
    return cur.fetchall()
  return safe_sql(db, sql)

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
    sys.exit(1)

  finally:
    if con:
      con.close()

  return result

