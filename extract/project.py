from collections import defaultdict
import csv
import pickle
import shutil
from os import mkdir, path, walk
from .db import MapDB
from .extract import FieldExtractor

# TODO vet for docstrings
# TODO vet for unicode

# Constants
###########

# filenames
_PROJECT_DB = 'project.db'
_INFO_PKL = 'info.pkl'

# table names
_TXT = 'txt'
_LABELS = 'labels'
_RAW_EXTRACTIONS = 'raw_extractions'
_REFINED_EXTRACTIONS = 'refined_extractions'

# column names
_RECORD_ID, _RECORD_ID_TYPE = 'record_id', 'INT'
_TXT_RECORD, _TXT_RECORD_TYPE = 'txt_record', 'TEXT'
_CONFIDENCE, _CONFIDENCE_TYPE = 'confidence', 'FLOAT'
# TODO deal with user clobbering these internal names

# TODO why not just use literal strings in the sql queries?
_DB_NAMESPACE = {
  _TXT: _TXT,
  _LABELS: _LABELS,
  _RAW_EXTRACTIONS: _RAW_EXTRACTIONS,
  _REFINED_EXTRACTIONS: _REFINED_EXTRACTIONS,
  _RECORD_ID: _RECORD_ID,
  _TXT_RECORD: _TXT_RECORD,
  _CONFIDENCE: _CONFIDENCE
}

class ProjectInfo:
  '''
  Holds meta-data that needs to be persisted for each project
  '''
  def __init__(self):
    self.fields = set([])
    self.aux_fields = set([])
    self.connections = defaultdict(set)
    self.custom_tokens = {}

class Project:
  '''Persistenly encapsulates a field extraction project'''

  PROJECTS = 'projects' # projects directory

  def __init__(self, name, info=None):
    '''Initializes a project
    name -- The name of the project
    info -- Empty ProjectInfo should be passed in when creating a new project
    '''
    self.name = name

    if info:
      self.info = info
      self._save_info()
    else:
      self.info = self._load_info()

    self._db = MapDB(path.join(self._path(), _PROJECT_DB))

  @staticmethod
  def new_project(name, f):
    '''Creates a new project.
    name -- The name of the project
    f -- File descriptor for the text file that should be extracted
    '''
    project_path = path.join(Project.PROJECTS, name)
    if path.exists(project_path): # check for name collisions
      raise ValueError("Project with name '{}' already exists".format(name))

    mkdir(path.join(Project.PROJECTS, name))
    project = Project(name, ProjectInfo())

    project._create_tables()
    project._ingest(f)

    return project

  @staticmethod
  def load_projects(projects_dir=None):
    '''Loads all projects from the project directory
    Returns a list of projects
    '''
    if not projects_dir:
      projects_dir = Project.PROJECTS
    projects = []
    for project_name in next(walk(projects_dir))[1]:
      projects.append(Project(project_name))
    return projects

  @staticmethod
  def load_project(name, projects_dir=None):
    '''Load a specific project by name'''
    if not projects_dir:
      projects_dir = Project.PROJECTS
    for project_name in next(walk(projects_dir))[1]:
      if name == project_name:
        return Project(project_name)
    raise ValueError("No project with name '{}' found in {}".format(name, projects_dir))

  @staticmethod
  def delete_project(name, projects_dir=None):
    '''Irreversibly deletes a project by name'''
    if not projects_dir:
      projects_dir = Project.PROJECTS
    project_path = path.join(projects_dir, name)
    shutil.rmtree(project_path)

  # Meta-data API
  ###############

  # TODO keep fields unique, warn user if removing non-existent field
  # TODO refactor DRY

  def add_fields(self, fields):
    with self._db.cursor() as cur:
      for field in set(fields):
        self.info.fields.add(field)
        cur.execute(*self._db.add_column(_LABELS, field, 'TEXT'))
        cur.execute(*self._db.add_column(_RAW_EXTRACTIONS, field, 'TEXT'))
        cur.execute(*self._db.add_column(_REFINED_EXTRACTIONS, field, 'TEXT'))
    self._save_info()

  def remove_fields(self, fields):
    with self._db.cursor() as cur:
      for field in set(fields):
        self.info.fields.remove(field)
        cur.execute(*self._db.drop_column(_LABELS, field))
        cur.execute(*self._db.drop_column(_RAW_EXTRACTIONS, field))
        cur.execute(*self._db.drop_column(_REFINED_EXTRACTIONS, field))
    self._save_info()

  def add_aux_fields(self, aux_fields):
    with self._db.cursor() as cur:
      for aux_field in set(aux_fields):
        self.info.aux_fields.add(aux_field)
        cur.execute(*self._db.add_column(_LABELS, aux_field, 'TEXT'))
        cur.execute(*self._db.add_column(_RAW_EXTRACTIONS, aux_field, 'TEXT'))
        cur.execute(*self._db.add_column(_REFINED_EXTRACTIONS, aux_field, 'TEXT'))
    self._save_info()

  def remove_aux_fields(self, aux_fields):
    with self._db.cursor() as cur:
      for aux_field in set(aux_fields):
        self.info.aux_fields.remove(aux_field)
        cur.execute(*self._db.drop_column(_LABELS, aux_field))
        cur.execute(*self._db.drop_column(__RAW_EXTRACTIONS, aux_field))
        cur.execute(*self._db.drop_column(__REFINED_EXTRACTIONS, aux_field))
    self._save_info()

  def add_connections(self, connections):
    for from_state, to_states in connections.iteritems():
      self.info.connections[from_state] = self.info.connections[from_state] | to_states
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

  # @output := {record_id: rid, txt_record: txt_r}
  def txt(self):
    '''''' # TODO
    query = ('SELECT {record_id},{txt_record}'
            ' FROM {txt}')

    query = query.format(**_DB_NAMESPACE)

    attrs = [_RECORD_ID, _TXT_RECORD]
    return (dict(zip(attrs, record)) for record in self._sql(query))

  # @output := {record_id: rid, txt_record: txt_r}
  def unlabeled_sample(self, n):
    '''''' # TODO
    query = ('SELECT {record_id},{txt_record}'
            ' FROM {txt}'
            ' WHERE {record_id} NOT IN (SELECT {record_id} FROM {labels})'
            ' LIMIT {limit}')

    query = query.format(limit=n, **_DB_NAMESPACE)

    attrs = [_RECORD_ID, _TXT_RECORD]
    return (dict(zip(attrs, record)) for record in self._sql(query))

  # @output := {record_id: rid, txt_record: txt_r, *fields: *artificial_extract}
  def training_examples(self):
    '''''' # TODO
    query = ('SELECT {txt}.{record_id},{txt_record},{all_fields}'
            ' FROM {txt},{labels}'
            ' WHERE {txt}.{record_id}={labels}.{record_id}')

    all_fields = self._all_fields()
    query = query.format(all_fields=','.join(all_fields), **_DB_NAMESPACE)

    attrs = [_RECORD_ID, _TXT_RECORD] + all_fields
    return (dict(zip(attrs, record)) for record in self._sql(query))

  # @output := {record_id: rid, txt_record: txt_r, confidence: c, *fields: *impure_extract}
  def raw_extractions(self):
    '''''' # TODO
    query = ('SELECT {txt}.{record_id} AS {record_id},{txt_record},{confidence},{all_fields}'
            ' FROM {txt},{raw_extractions}'
            ' WHERE {txt}.{record_id}={raw_extractions}.{record_id}')

    all_fields = self._all_fields()
    query = query.format(all_fields=','.join(all_fields), **_DB_NAMESPACE)

    attrs = [_RECORD_ID, _TXT_RECORD, _CONFIDENCE] + all_fields
    pkl_maps = (dict(zip(attrs, pkl_record)) for pkl_record in self._sql(query))

    record_maps = (self._unpkl(pkl_map) for pkl_map in pkl_maps)
    return record_maps

  # @output := {record_id: rid, txt_record: txt_r, confidence: c, *fields: *pure_extract}
  def refined_extractions(self, sql):
    '''''' # TODO
    query = ('SELECT {txt}.{record_id} AS {record_id},{txt_record},{confidence},{all_fields}'
            ' FROM {txt},{refined_extractions}'
            ' WHERE {txt}.{record_id}={refined_extractions}.{record_id}')

    all_fields = self._all_fields
    query = query.format(all_fields=','.join(all_fields), **_DB_NAMESPACE)

    attrs = [_RECORD_ID, _TXT_RECORD, _CONFIDENCE] + all_fields
    return (dict(zip(attrs, record)) for record in self._sql(query))

# save data
###########

  # @input training_examples := {record_id: rid, *fields: *artificial_extract}
  def add_training_examples(self, training_examples):
    '''''' # TODO
    with self._db.cursor() as cur:
      for training_example in training_examples:
        cur.execute(*self._db.insert(_LABELS, training_example))

# perform computation
#####################

  def extract(self, smoothing=0):
    '''''' # TODO
    # initialize field extractor
    fe = FieldExtractor(
        fields=self.info.fields,
        aux_fields=self.info.aux_fields,
        connections=self.info.connections,
        custom_tokens=self.info.custom_tokens)

    # train field extractor
    split_training_examples = (
        (training_example[_TXT_RECORD], fe.all_field_filter(training_example))
        for training_example in self.training_examples()
    )
    fe.learn(split_training_examples, smoothing=smoothing)

    # extract
    extraction_maps = (_extraction_map(fe, record) for record in self.txt())

    # store extractions
    with self._db.cursor() as cur:
      for extraction_map in extraction_maps:
        # pickle all fields (may contain multiple matches in a list)
        cur.execute(*self._db.insert(_RAW_EXTRACTIONS, self._pkl(extraction_map)))

  def refine(self):
    '''''' # TODO
    # TODO
    for extraction_map in self.raw_extractions():
      self._sql(*self._db.insert(_REFINED_EXTRACTIONS, _refine(extraction_map)))

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

  def _all_fields(self):
    return list(self.info.fields | self.info.aux_fields)

  def _sql(self, query, params=()):
    with self._db.cursor() as cur:
      cur.execute(query,params)
      return cur.fetchall()

  def _create_tables(self):
    with self._db.cursor() as cur:
      # TODO primary key? foreign key?
      cur.execute(*self._db.create_table(_TXT, [
          (_RECORD_ID, _RECORD_ID_TYPE),
          (_TXT_RECORD, _TXT_RECORD_TYPE)
      ]))
      cur.execute(*self._db.create_table(_LABELS, [
          (_RECORD_ID, _RECORD_ID_TYPE)
      ]))
      cur.execute(*self._db.create_table(_RAW_EXTRACTIONS, [
          (_RECORD_ID, _RECORD_ID_TYPE),
          (_CONFIDENCE, _CONFIDENCE_TYPE)
      ]))
      cur.execute(*self._db.create_table(_REFINED_EXTRACTIONS, [
          (_RECORD_ID, _RECORD_ID_TYPE),
          (_CONFIDENCE, _CONFIDENCE_TYPE)
      ]))

  def _ingest(self, f):
    txt_record_maps = ({_RECORD_ID: line_no, _TXT_RECORD: line} for line_no, line in enumerate(f))
    with self._db.cursor() as cur:
      for txt_record_map in txt_record_maps:
        cur.execute(*self._db.insert(_TXT, txt_record_map))

  def _pkl(self, record_map):
    pkl_record_map = record_map.copy()
    pkl_fields = {
        field: pickle.dumps(extract)
        for field, extract in record_map.iteritems()
        if field in self._all_fields() and extract is not None
    }
    pkl_record_map.update(pkl_fields)
    return pkl_record_map

  def _unpkl(self, pkl_record_map):
    record_map = pkl_record_map.copy()
    unpkl_fields = {
        field: pickle.loads(extract)
        for field, extract in pkl_record_map.iteritems()
        if field in self._all_fields() and extract is not None
    }
    record_map.update(unpkl_fields)
    return record_map

  # TODO warn if we see any records that have more than 1 match
  def _multiple_match(self, extract_map):
    all_fields = self.info.fields | self.info.aux_fields
    mm = {}
    for attr, extract in extract_map:
      if attr in all_fields and len(extract) > 1:
        mm[attr] = extract
    return mm

# utils

def _extraction_map(fe, record):
  extraction, confidence = fe.extract(record[_TXT_RECORD])
  extraction_map = {_RECORD_ID: record[_RECORD_ID], _CONFIDENCE: confidence}
  extraction_map.update(fe.all_field_filter(extraction))
  return extraction_map

