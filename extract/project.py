import csv
import pickle
import sqlite3 as lite
import shutil
import sys
from os import mkdir, path, walk
from .extract import FieldExtractor

# TODO should this module be outside the extract package?

# TODO keep info in db table instead of python obj?
class ProjectInfo:

  def __init__(self):
    # TODO include additive smoothing param alpha?
    self.fields = set([])
    self.aux_fields = set([])
    self.connections = {}
    self.custom_tokens = {}

class Project:
  # filenames
  _PROJECT_DB = 'project.db'
  _INFO_PKL = 'info.pkl'

  # table names
  _TXT = 'txt'
  _LABELS = 'labels'
  _EXTRACTIONS = 'extractions'

  # column names
  _RECORD_ID, _RECORD_ID_TYPE = 'record_id', 'INT'
  _TXT_RECORD, _TXT_RECORD_TYPE = 'txt_record', 'TEXT'
  _CONFIDENCE, _CONFIDENCE_TYPE = 'confidence', 'FLOAT'

  # projects directory
  PROJECTS = 'projects'

  def __init__(self, name, info=None):
    self.name = name

    if info:
      self.info = info
      self._save_info()
    else:
      self.info = self._load_info()

    self._db = SqlDatabase(path.join(self._path(), Project._PROJECT_DB))

  @staticmethod
  def new_project(name, f):
    # check for name collisions
    project_path = path.join(Project.PROJECTS, name)
    if path.exists(project_path):
      raise ValueError("Project with name '{}' already exists".format(name))

    mkdir(path.join(Project.PROJECTS, name))
    project = Project(name, ProjectInfo())

    project._create_tables()

    for line_no, line in enumerate(f):
      record = {Project._RECORD_ID: line_no, Project._TXT_RECORD: line}
      project._db.insert_into(Project._TXT, record)

    return project

  @staticmethod
  def load_projects(projects_dir=None):
    if not projects_dir:
      projects_dir = Project.PROJECTS
    projects = []
    for project_name in next(walk(projects_dir))[1]:
      projects.append(Project(project_name))
    return projects

  @staticmethod
  def load_project(name, projects_dir=None):
    if not projects_dir:
      projects_dir = Project.PROJECTS
    for project_name in next(walk(projects_dir))[1]:
      if name == project_name:
        return Project(project_name)
    raise ValueError("No project with name '{}' found in {}".format(name, projects_dir))

  @staticmethod
  def delete_project(name, projects_dir=None):
    if not projects_dir:
      projects_dir = Project.PROJECTS
    project_path = path.join(projects_dir, name)
    shutil.rmtree(project_path)

  # API
  #####

  # TODO keep fields unique, warn user if removing non-existent field

  def add_fields(self, fields):
    for field in fields:
      self.info.fields.add(field)
      self._db.add_column(Project._LABELS, field, 'TEXT')
      self._db.add_column(Project._EXTRACTIONS, field, 'TEXT')
    self._save_info()

  def remove_fields(self, fields):
    for field in set(fields):
      self.info.fields.remove(field)
      self._db.drop_column(Project._LABELS, field)
      self._db.drop_column(Project._EXTRACTIONS, field)
    self._save_info()

  def add_aux_fields(self, aux_fields):
    for aux_field in set(aux_fields):
      self.info.aux_fields.add(aux_field)
      self._db.add_column(Project._LABELS, aux_field, 'TEXT')
      self._db.add_column(Project._EXTRACTIONS, aux_field, 'TEXT')
    self._save_info()

  def remove_aux_fields(self, aux_fields):
    for aux_field in set(aux_fields):
      self.info.aux_fields.remove(aux_field)
      self._db.drop_column(Project._LABELS, aux_field)
      self._db.drop_column(Project._EXTRACTIONS, aux_field)
    self._save_info()

  def add_connections(self, connections):
    for from_state, to_states in connections.iteritems():
      self.info.connections[from_state] = self.info.connections.get(from_state, set()) | to_states
    self._save_info()

  def remove_connections(self, connections):
    for from_state, to_states in connections.iteritems():
      self.info.connections[from_state] = self.info.connections.get(from_state, set()) - to_states
    self._save_info()

  def add_custom_tokens(self, custom_tokens):
    self.info.custom_tokens.update(custom_tokens)
    self._save_info()

  def remove_custom_tokens(self, custom_tokens):
    for token in custom_tokens:
      if token in self.info.custom_tokens:
        del self.info.custom_tokens[token]
    self._save_info()

  def add_training_pair(self, record_id, extraction_example):
    record = {Project._RECORD_ID: record_id}
    record.update(extraction_example)
    self._db.insert_into(Project._LABELS, record)

  def get_unlabeled_sample(self, n):
    label_ids = '(SELECT {record_id} FROM {labels})'.format(
        record_id=Project._RECORD_ID, labels=Project._LABELS)

    query = 'SELECT {record_id},{txt_record}'.format(
        record_id=Project._RECORD_ID,
        txt_record=Project._TXT_RECORD)
    query += ' FROM {txt}'.format(
        txt=Project._TXT)
    query += ' WHERE {record_id} NOT IN {label_ids}'.format(
        record_id=Project._RECORD_ID,
        label_ids=label_ids)
    query += ' LIMIT {limit}'.format(
        limit=n)

    result = None
    conn = lite.connect(self._db._path)
    with conn:
      cur = conn.cursor()
      cur.execute(query)
      result = cur.fetchall()
    conn.close()
    return result

  def extract(self):
    fe = FieldExtractor(
        fields=self.info.fields,
        aux_fields=self.info.aux_fields,
        connections=self.info.connections
        custom_tokens=self.info.custom_tokens)

    for txt_record, extraction_example in self._training_pairs():
      fe.train(txt_record, extraction_example)

    for record_id, txt_record in self._txt():
      extraction = fe.extract(txt_record)
      record = {Project._RECORD_ID: record_id}
      record.update(extraction)
      self.insert_into(Project._EXTRACTIONS, record)

  # convenience
  #############

  def _path(self):
    return path.join(Project.PROJECTS, self.name)

  def _save_info(self):
    with open(path.join(self._path(), Project._INFO_PKL), 'wb') as f:
      pickle.dump(self.info, f)

  def _load_info(self):
    with open(path.join(self._path(), Project._INFO_PKL), 'rb') as f:
      return pickle.load(f)

  def _create_tables(self):
    self._db.create_table(Project._TXT, [
        (Project._RECORD_ID, Project._RECORD_ID_TYPE),
        (Project._TXT_RECORD, Project._TXT_RECORD_TYPE)
    ])
    self._db.create_table(Project._LABELS, [
        (Project._RECORD_ID, Project._RECORD_ID_TYPE)
    ])
    self._db.create_table(Project._EXTRACTIONS, [
        (Project._RECORD_ID, Project._RECORD_ID_TYPE),
        (Project._CONFIDENCE, Project._CONFIDENCE_TYPE)
    ])

  def _training_pairs(self):
    # TODO return iterable of (txt_record, extraction_example)
    pass

  def _txt(self):
    # TODO return an iterable of (record_id, txt_record)
    pass

  def _learn(self, field_extractor):
    batch_size = 1e3 # tunable
    batch = cur.fetchmany(batch_size)
    while batch:
      for row in batch:
        # TODO convert row into training pair
        field_extractor.train(x,e)
      batch = cur.fetchmany(batch_size)
    return sum

# Database operations
#####################

class SqlDatabase:

  def __init__(self, path):
    self._path = path

  # API
  #####

  def create_table(self, tablename, columns):
    column_defs = ['{} {}'.format(col_name, col_type) for col_name, col_type in columns]
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      cur.execute('CREATE TABLE {tablename} ({columns})'.format(tablename=tablename,
          columns=','.join(column_defs)))
    conn.close()

  def drop_table(self, tablename):
    conn = lite.connect(self._path)
    with con:
      cur = conn.cursor()
      cur.execute('DROP TABLE IF EXISTS {tablename}'.format(tablename=tablename))
    conn.close()

  def add_column(self, tablename, column_name, column_type):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      cur.execute('ALTER TABLE {tablename} ADD {column_name} {column_type}'.format(
          tablename=tablename, column_name=column_name, column_type=column_type))
    conn.close()

  def drop_column(self, tablename, column_name):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      cur.execute('ALTER TABLE {tablename} DROP COLUMN {column_name}'.format(
          tablename=tablename, column_name=column_name))
    conn.close()

  # TODO more efficient insert? batch insert?
  def insert_into(self, tablename, record):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      value_placeholders = ['?'] * len(record)
      insert = "INSERT INTO {tablename} ({column_names}) VALUES ({values})".format(
          tablename=tablename,
          column_names=','.join(record.keys()),
          values=','.join(value_placeholders))
      cur.execute(insert, record.values())
    conn.close()

  # convenience
  #############

  def _do(self, func):
    conn = lite.connect(self._path)
    with conn:
      cur = conn.cursor()
      func(cur)
    conn.close()
