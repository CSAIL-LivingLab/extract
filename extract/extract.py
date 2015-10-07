from itertools import chain
from .hmm import HMM
from .learn import featurize, numerical
from .lex import Lexer
from .ingest import labels

def phi(t):
  return t.typ

# model
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
  'src': 'src: /', # for prefix testing
  'dst': 'dest: /' # for prefix testing
}

class FieldExtractor:

  # TODO set lexer with hierarchy
  def __init__(self, fields, lexer=None):
    self.fields = fields

    if lexer:
      self.lexer = lexer
    else:
      self.lexer = Lexer(default_types)

    self.phi = phi
    self.hmm = None
    self.x_translator = None
    self.y_translator = None

  def train(self, txt_records, txt_labels=None):
    Ti = Lexer.pad(self.lexer.tokenize_all(txt_records))
    X_obj = featurize(Ti, self.phi)
    X, v, self.x_translator = numerical(X_obj)

    if txt_labels:
      To = self.lexer.tokenize_all(txt_labels)
      Y_obj = labels(Ti, To, self.fields)
      Y, k, self.y_translator = numerical(Y_obj)
      self.hmm = HMM(k, v)
      self.hmm.train(X,Y)
      #print self.hmm.start_p
      #print self.hmm.trans_p
      #print self.hmm.emit_p
    else:
      raise NotImplementedError()

  def extract(self, txt_records):
    # ingest test data
    unpadded = self.lexer.tokenize_all(txt_records)
    T_test = Lexer.pad(unpadded)
    X_obj_test = featurize(T_test, self.phi)
    X_test, _, _ = numerical(X_obj_test, self.x_translator)

    # viterbi
    Z = []
    for x_test in X_test:
      Z.append(self.hmm.viterbi(x_test))

    # chunk fields
    extraction = extract_from_labels(Z, T_test)

    # filter
    return self._field_filter(extraction)

  # subroutines
  #############

  def _field_filter(self, csv):
    filtered_csv = []
    indices = [self.y_translator.get_num(attr) for attr in self.fields]
    for row in csv:
      filtered_csv.append([row[j] for j in indices])
    return filtered_csv

# chunk
#######

def group_fields(z, x):
  fields = {}
  field = []
  field_num = None
  for t in range(len(x)):
    x_t = x[t]
    if len(field) == 0:
      field.append(x_t)
      field_num = z[t]
    elif z[t] == field_num:
      field.append(x_t)
    else:
      fields[field_num] = ''.join([token.string for token in field])
      field = [x_t]
      field_num = z[t]
  return fields

def extract_from_labels(Z, Tx):
  extraction = []
  for i in range(len(Z)):
    z_i = Z[i]
    tx_i = Tx[i]
    row = []
    fields = group_fields(z_i, tx_i)
    for j in range(max(chain.from_iterable(Z))+1):
      row.append(fields.get(j,''))
    extraction.append(row)
  return extraction

