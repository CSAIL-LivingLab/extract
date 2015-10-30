import logging
import re
from extract.project import Project
from flask import Flask, render_template, request, redirect, session, url_for
from logging.handlers import RotatingFileHandler
from os import mkdir, path
from werkzeug import secure_filename

PROJECTS = path.join(path.dirname(path.realpath(__file__)), 'projects')
if not path.exists(PROJECTS):
  mkdir(PROJECTS)

Project.PROJECTS = PROJECTS

app = Flask(__name__)
app.secret_key = 'no-secret' # enables use of app.session

# Routes
########

@app.route('/')
def index():
  return redirect(url_for('home'))

@app.route('/home')
def home():
  return render_template('home.html')

@app.route('/projects')
def projects():
  return render_template('projects.html', projects=Project.load_projects())

@app.route('/fields')
def fields():
  project = get_working_project()
  info = project.info
  txt_sample = list(project.txt()) # TODO random sample
  header = project.txt_header()
  return render_template('fields.html', info=info, header=header, txt_sample=txt_sample)

@app.route('/label')
def label():
  project = get_working_project()
  info = project.info
  labels_so_far = project.labels_so_far()
  header = project.training_header()
  all_fields = project._all_fields()
  return render_template('label.html', info=info, header=header, labels_so_far=labels_so_far, all_fields=all_fields)

@app.route('/connect')
def connect():
  project = get_working_project()
  info = project.info
  ambiguities = project.structure_ambiguity(0.3)
  return render_template('connect.html', info=info, ambiguities=ambiguities)

@app.route('/review')
def review():
  project = get_working_project()
  extractions = project.raw_extractions()
  header = project.raw_header()
  return render_template('review.html', header=header, extractions=extractions)

@app.route('/query')
def query():
  project = get_working_project()
  return render_template('query.html')

# HTTP API
##########

@app.route('/api/new_project', methods=['POST'])
def new_project():
  project_name = secure_filename(request.form['project_name'])
  test_txt = request.files['txt']
  project = Project.new_project(project_name, test_txt)
  if not get_working_project():
    set_working_project(project)
  return redirect(url_for('projects'))

@app.route('/api/delete_project', methods=['POST'])
def delete_project():
  project_name = request.form['project-name']
  Project.delete_project(project_name)
  set_working_project(None)
  return redirect(url_for('projects'))

@app.route('/api/switch_project', methods=['POST'])
def switch_project():
  project_name = request.form['project-name']
  project = Project.load_project(project_name)
  set_working_project(project)
  return redirect(url_for('projects'))

@app.route('/api/add_fields', methods=['POST'])
def add_fields():
  project = get_working_project()
  fields = request.form['fields'].split(',')
  project.add_fields(fields)
  return redirect(url_for('fields'))

@app.route('/api/add_aux_fields', methods=['POST'])
def add_aux_fields():
  project = get_working_project()
  fields = request.form['fields'].split(',')
  project.add_aux_fields(fields)
  return redirect(url_for('connect'))

@app.route('/api/add_connections', methods=['POST'])
def add_connections():
  project = get_working_project()
  from_state = request.form['from_state']
  to_state = request.form['to_state']
  project.add_connections({from_state: set([to_state])})
  return redirect(url_for('connect'))

# TODO support removal

@app.route('/api/update_training_examples', methods=['POST'])
def update_training_examples():
  project = get_working_project()
  fields = project.info.fields
  # TODO update to new API
  training_pairs = {}
  for field_id, val in request.form.iteritems():
    # TODO robust json
    if re.match('[0-9]+[-]{1}.*', field_id) is not None and val:
      record_id, field = field_id.split('-', 1)
      training_pair = training_pairs.get(record_id, {})
      if not training_pair:
        training_pair['record_id'] = record_id
      training_pair[field] = val
      training_pairs[record_id] = training_pair
  project.update_training_examples(training_pairs.values())

  return redirect(url_for('label'))

@app.route('/api/extract', methods=['POST'])
def extract():
  project = get_working_project()
  project.extract()
  return redirect(url_for('review'))

@app.route('/api/refine', methods=['POST'])
def refine():
  project = get_working_project()
  project.refine()
  return redirect(url_for('query'))

# convenience
#############

def set_working_project(project):
  if project:
    session['working_project'] = project.name
  else:
    del session['working_project']

def get_working_project():
  project_name = session.get('working_project', None)
  if not project_name:
    return None

  return Project.load_project(project_name)

def allowed_filename(filename):
  return '.' in filename and path.splitext(filename)[1] == '.txt'

# Run
#####

if __name__ == '__main__':
  log_path = path.join(path.dirname(path.realpath(__file__)), 'log.log')
  handler = RotatingFileHandler(log_path, maxBytes=10000, backupCount=1)
  handler.setLevel(logging.INFO)
  app.logger.addHandler(handler)
  app.run(debug=True)
