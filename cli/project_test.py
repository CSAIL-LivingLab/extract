from extract.project import Project, ProjectInfo, _RECORD_ID, _TXT_RECORD
from os import mkdir, path
import shutil
import sys

Project.PROJECTS = path.join(path.dirname(path.dirname(path.realpath(__file__))), 'projects')

if __name__ == '__main__':
  if path.exists(Project.PROJECTS):
    shutil.rmtree(Project.PROJECTS)
    mkdir(Project.PROJECTS)
  project = None
  project_name = sys.argv[1]
  project_filepath = sys.argv[2]
  with open(project_filepath) as f:
    project = Project.new_project(project_name, f)

  fields = ['date', 'time', 'src', 'dest']
  project.add_fields(fields)

  aux_fields = ['src_prefix', 'dest_prefix']
  project.add_aux_fields(aux_fields)

  connections = {'src_prefix': set(['src']), 'dest_prefix': set(['dest'])}
  project.add_connections(connections)

  custom_tokens = {'src': 'src:', 'dst': 'dest:'}
  project.add_custom_tokens(custom_tokens)

  line_no = 0

  line = '2012-01-04 00:01:23,180 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block blk_-2281137920769708011_1116 src: /127.0.0.1:32981 dest: /127.0.0.1:50010'

  #extraction_example = {
  #  'date':'2012-01-04',
  #  'time':'00:01:23',
  #  'src':'127.0.0.1:32981',
  #  'dest':'127.0.0.1:50010'
  #}

  extraction_example = {
      'date':'2012-01-04',
      'time':'00:01:23',
      'src_prefix':'src:',
      'src':'127.0.0.1:32981',
      'dest_prefix':'dest:',
      'dest':'127.0.0.1:50010'
  }
  training_example = {_RECORD_ID: line_no}
  training_example.update(extraction_example)

  project.add_training_examples([training_example])
  #print list(project.get_unlabeled_sample(5))

  ambiguity = False
  for ambiguous_field_pairs in project.structure_ambiguity(0.3):
    ambiguity = True
    print 'ambiguous structure:', ambiguous_field_pairs


  smoothing = 0
  if len(sys.argv) > 3:
    smoothing = float(sys.argv[3])

  project.extract(smoothing=smoothing)

  if not ambiguity:
    for ambiguous_extract in project.match_ambiguity():
      ambiguity = True
      print 'ambiguous match:', ambiguous_extract

  if not ambiguity:
    for extraction in project.raw_extractions():
      print extraction
