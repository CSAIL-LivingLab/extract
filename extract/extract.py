from .hmm import HMM
from .learn import featurize, numerical
from .learn import featurize_all, numerical_all
from .lex import Lexer

def phi(t):
  return t.typ

# TODO set lexer with hierarchy
default_types = {
  'num': '\d+',
  'abc': '[a-zA-Z]+',
  #'sym': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?\s]'
  'spc': '\s+',
  #'pnc': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?]'
  'hyp': '[-]{1}',
  'cln': '[:]{1}',
  'prd': '[.]{1}',
  'pnc': '[`=[\]\\\\;\',/~!@#$%^&*()_+{}|"<>?]',
  'src': 'src:', # for prefix testing
  'dst': 'dest:' # for prefix testing
}

# TODO use-case for FE: one time use (1 FE / extraction)? or 1 FE / project?
class FieldExtractor:

  def __init__(self, fields, lexer=None):
    self.fields = set(fields)
    self.aux_fields = set()
    self.connections = {}

    self.lexer = Lexer(default_types)
    if lexer:
      self.lexer = lexer

    self.hmm = None
    self.x_translator = None
    self.y_translator = None

    self.phi = phi

  # TODO record-by-record training
  def train(self, training_set):
    '''Trains the underlying Hidden Markov Model
        @param training_set is a list of training pairs tuples: [(txt, extraction),...]
    '''
    # separate into X,Y for HMM training
    txt_records, extraction_examples = [], []
    for txt_record, extraction_example in training_set:
      txt_records.append(txt_record)
      extraction_examples.append(extraction_example)

    # txt_records -> X
    Ti = Lexer.pad_all(self.lexer.tokenize_all(txt_records))
    X_obj = featurize_all(Ti, self.phi)
    X, v, self.x_translator = numerical_all(X_obj)

    # extraction_examples -> Y
    To = [{field_name:self.lexer.tokenize_all(extracted_field, stop=False) for field_name,extracted_field in o.iteritems()} for o in extraction_examples]
    Y_obj = extraction2label_all(Ti, To, self._states(), self.connections)
    Y, k, self.y_translator = numerical_all(Y_obj)

    # HMM
    self.hmm = HMM(k, v)
    # TODO consider stream training in HMM
    self.hmm.train(X,Y)

    #print self.hmm.start_p
    #print self.hmm.trans_p
    #print self.hmm.emit_p

  def extract(self, txt_record):
    '''Runs the Viterbi algorithm on the tokens made from @param txt_record
        @param txt_record is the raw text as a string
        @returns a tuple containing: 1) dictionary mapping field names to a list of the viterbi MLE string(s) corresponding to the field, 2) the confidence of the Field extractor as a probability
    '''
    # digest input
    t_test = self.lexer.tokenize(txt_record)
    x_obj_test = featurize(t_test, self.phi)
    x_test = numerical(x_obj_test, self.x_translator)

    # ML guess
    z, confidence = self.hmm.viterbi(x_test)

    # group by internal field number
    fields = group_fields(z, t_test)

    # translate field numbers to field names
    raw_extraction = {}
    for field_num, field in fields.iteritems():
      raw_extraction[self.y_translator.get_val(field_num)] = field

    # TODO normalize confidences
    return raw_extraction, confidence

  # subroutines
  #############

  # TODO should this be part of the API? when should this be called?
  def _field_filter(self, extraction):
    indices = [self.y_translator.get_num(attr) for attr in self.fields]
    return [extraction[j] for j in indices]

  def _states(self):
    states = []
    states.extend(self.fields)
    states.extend(self.aux_fields)
    return states

# TODO move these into their own file?
# utils

def find(x, pattern):
  i = 0
  while i <= len(x) - len(pattern):
    if x[i:i + len(pattern)] == pattern:
      return i
    i += 1
  return -1

# TODO modularize this function
def extraction2label(x, e, states, connections):
  labels = [None] * len(x)

  # label fields and aux fields
  for state,extraction in e.iteritems():
    i = find(x, extraction)
    labels[i : i + len(extraction)] = [state] * len(extraction)

  # compute start,stop indices for all potential connections
  links = _links(labels)

  # fill in links with corresponding connections
  for (from_state,to_state), (i,j) in links.iteritems():
    if to_state in connections.get(from_state, set()):
      labels[i:j] = ['{}-{}'.format(from_state, to_state)] * (j - i)
  return labels

# helper function for extraction2label
def _links(labels):
  '''Finds all sequences of None within @param labels that are wrapped by non-None values
    @param labels is a list of field names as strings
    @returns a dictionary mapping the 2 states surrounding a None-sequence to the indices for that None-sequence
  '''
  links = {}
  index = 0
  while index < len(labels):
    label = labels[index]
    if label is None and index != 0:
      none_index = index
      while none_index < len(labels):
        if labels[none_index] is not None:
          break
        none_index += 1
      if none_index >= len(labels):
        break
      from_state = labels[index - 1]
      to_state = labels[none_index]
      links[(from_state, to_state)] = (index, none_index)
      index = none_index
    else:
      index += 1
  return links

# TODO OBSOLETE condition: record-by-record architecture
def extraction2label_all(Tx, Te, states, connections):
  Y = []
  assert len(Tx) == len(Te)
  for i in range(len(Tx)):
    x_i = Tx[i]
    e_i = Te[i]
    Y.append(extraction2label(x_i, e_i, states, connections))
  return Y

# chunk
#######

def group_fields(z, x):
  fields = {}
  field = [x[0]]
  for t in range(1,len(x)):
    field_id = z[t - 1]
    if z[t] == field_id:
      field.append(x[t])
    else:
      fields.setdefault(field_id, []).append(Lexer.detokenize(field))
      field = [x[t]]
  # ignore dangling field as it always corresponds to STOP
  #fields.setdefault(z[-1], []).append(Lexer.detokenize(field))
  return fields
