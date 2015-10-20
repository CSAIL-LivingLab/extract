import csv
import pickle
import shutil
from os import mkdir, path, walk
from .db import SqlDatabase
from .extract import FieldExtractor

# TODO should this module be outside the extract package?

# Constants
###########

# filenames
_PROJECT_DB = 'project.db'
_INFO_PKL = 'info.pkl'

# table names
_TXT = 'txt'
_LABELS = 'labels'
# TODO workspace? or final table?
_EXTRACTIONS = 'extractions'

# column names
_RECORD_ID, _RECORD_ID_TYPE = 'record_id', 'INT'
_TXT_RECORD, _TXT_RECORD_TYPE = 'txt_record', 'TEXT'
_CONFIDENCE, _CONFIDENCE_TYPE = 'confidence', 'FLOAT'

# TODO keep info in db table instead of python obj?
class ProjectInfo:
  '''
  Holds meta-data that needs to be persisted for each project
  '''
  def __init__(self):
    self.fields = set([])
    self.aux_fields = set([])
    self.connections = {}
    self.custom_tokens = {}

    self.alpha = 1e3 # default for additive smoothin param

class Project:

  # projects directory
  PROJECTS = 'projects'

  def __init__(self, name, info=None):
    self.name = name

    if info:
      self.info = info
      self._save_info()
    else:
      self.info = self._load_info()

    self._db = SqlDatabase(path.join(self._path(), _PROJECT_DB))

  @staticmethod
  def new_project(name, f):
    # check for name collisions
    project_path = path.join(Project.PROJECTS, name)
    if path.exists(project_path):
      raise ValueError("Project with name '{}' already exists".format(name))

    mkdir(path.join(Project.PROJECTS, name))
    project = Project(name, ProjectInfo())

    project._create_tables()

    txt_records = ({_RECORD_ID: line_no, _TXT_RECORD: line} for line_no, line in enumerate(f))
    project._db.insert_into(_TXT, txt_records)

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

  # Meta-data API
  ###############

  # TODO keep fields unique, warn user if removing non-existent field

  def add_fields(self, fields):
    for field in fields:
      self.info.fields.add(field)
      self._db.add_column(_LABELS, field, 'TEXT')
      self._db.add_column(_EXTRACTIONS, field, 'TEXT')
    self._save_info()

  def remove_fields(self, fields):
    for field in set(fields):
      self.info.fields.remove(field)
      self._db.drop_column(_LABELS, field)
      self._db.drop_column(_EXTRACTIONS, field)
    self._save_info()

  def add_aux_fields(self, aux_fields):
    for aux_field in set(aux_fields):
      self.info.aux_fields.add(aux_field)
      self._db.add_column(_LABELS, aux_field, 'TEXT')
      self._db.add_column(_EXTRACTIONS, aux_field, 'TEXT')
    self._save_info()

  def remove_aux_fields(self, aux_fields):
    for aux_field in set(aux_fields):
      self.info.aux_fields.remove(aux_field)
      self._db.drop_column(_LABELS, aux_field)
      self._db.drop_column(_EXTRACTIONS, aux_field)
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

  # Data API
  ##########

  def add_training_pairs(self, training_pairs):
    training_records = (Project._training_record(rid, e) for rid, e in training_pairs)
    self._db.insert_into(_LABELS, training_records)

  def get_unlabeled_sample(self, n):
    subquery = '(SELECT {record_id} FROM {labels})'.format(record_id=_RECORD_ID, labels=_LABELS)

    query = 'SELECT {record_id},{txt_record}'.format(record_id=_RECORD_ID, txt_record=_TXT_RECORD)
    query += ' FROM {txt}'.format(txt=_TXT)
    query += ' WHERE {record_id} NOT IN {subquery}'.format(record_id=_RECORD_ID,subquery=subquery)
    query += ' LIMIT {limit}'.format(limit=n)

    return self._db.sql([(query, ())])

  def extract(self):
    fe = FieldExtractor(
        fields=self.info.fields,
        aux_fields=self.info.aux_fields,
        connections=self.info.connections,
        custom_tokens=self.info.custom_tokens)

    fe.alpha = self.info.alpha

    for training_pair in self._training_pairs():
      txt_record, extraction_example = training_pair
      fe.train(txt_record, extraction_example)

    extraction_records = (Project._extract_record(fe, rid, txt_r) for rid, txt_r in self._txt())
    self._db.insert_into(_EXTRACTIONS, extraction_records)

  def extractions(self):
    all_fields = list(self.info.fields | self.info.aux_fields)
    query = 'SELECT {record_id},{confidence},{all_fields}'.format(
        record_id=_RECORD_ID,
        confidence=_CONFIDENCE,
        all_fields=','.join(all_fields))
    query += ' FROM {extractions}'.format(extractions=_EXTRACTIONS)
    extract_records = self._db.sql([(query, ())])
    attrs = [_RECORD_ID, _CONFIDENCE] + all_fields
    return (Project._load_record(ext_r, attrs, unpkl=all_fields) for ext_r in extract_records)

  # TODO implement this feature (can we assume decent input since this runs on the users computer)
  def sql(self, query):
    template = 'SELECT {user_input} FROM {} '

  # convenience
  #############

  def _path(self):
    return path.join(Project.PROJECTS, self.name)

  def _save_info(self):
    with open(path.join(self._path(), _INFO_PKL), 'wb') as f:
      pickle.dump(self.info, f)

  def _load_info(self):
    with open(path.join(self._path(), _INFO_PKL), 'rb') as f:
      return pickle.load(f)

  def _create_tables(self):
    # TODO primary key? foreign key?
    self._db.create_table(_TXT, [
        (_RECORD_ID, _RECORD_ID_TYPE),
        (_TXT_RECORD, _TXT_RECORD_TYPE)
    ])
    self._db.create_table(_LABELS, [
        (_RECORD_ID, _RECORD_ID_TYPE)
    ])
    self._db.create_table(_EXTRACTIONS, [
        (_RECORD_ID, _RECORD_ID_TYPE),
        (_CONFIDENCE, _CONFIDENCE_TYPE)
    ])

  def _training_pairs(self):
    all_fields = list(self.info.fields | self.info.aux_fields)
    query = 'SELECT {txt_record},{all_fields}'.format(
        txt_record=_TXT_RECORD,
        all_fields=','.join(all_fields))
    query += ' FROM {txt},{labels}'.format(
        txt=_TXT, labels=_LABELS)
    query += ' WHERE {txt}.{record_id}={labels}.{record_id}'.format(
        txt=_TXT, record_id=_RECORD_ID, labels=_LABELS)
    training_records = self._db.sql([(query, ())])

    split_records = ((tr[0], tr[1:]) for tr in training_records)
    return ((txt_r, dict(zip(all_fields, e))) for txt_r, e in split_records)

  def _txt(self):
    all_txt = 'SELECT {record_id},{txt_record} FROM {txt}'.format(
        record_id=_RECORD_ID, txt_record=_TXT_RECORD, txt=_TXT)
    return self._db.sql([(all_txt, ())])

  # TODO warn if we see any records that have more than 1 match
  def _multiple_match(self, extract_map):
    all_fields = self.info.fields | self.info.aux_fields
    mm = {}
    for attr, extract in extract_map:
      if attr in all_fields and len(extract) > 1:
        mm[attr] = extract
    return mm

  # TODO reconsider record transformations more generally
  @staticmethod
  def _training_record(record_id, extraction_example):
    record = {_RECORD_ID: record_id}
    record.update(extraction_example)
    return record

  @staticmethod
  def _extract_record(field_extractor, record_id, txt_record):
    raw_extract, confidence = field_extractor.extract(txt_record)
    record = {_RECORD_ID: record_id, _CONFIDENCE: confidence}
    extracted = {field: pickle.dumps(extract) for field, extract in raw_extract.iteritems()}
    record.update(field_extractor._all_field_filter(extracted))
    return record

  @staticmethod
  def _load_record(record, attrs, unpkl=[]):
    d = dict(zip(attrs, record))
    for key, val in d.iteritems():
      if key in unpkl and val is not None:
        d[key] = pickle.loads(val)
    return d

