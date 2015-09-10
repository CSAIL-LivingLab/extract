import hmm
from itertools import chain
from src.learn import featurize, numerical
from src.parse import load_txt, load_csv, labels

def phi(t):
  return t.typ

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

class FieldExtractor:

  def __init__(self, observation_types):
    self.phi = phi
    self.ots = observation_types
    self.hmm = None
    self.x_translator = None
    self.y_translator = None

  def train(self, in_f, out_f=None):
    Ti = load_txt(in_f, self.ots)
    X_obj = featurize(Ti, self.phi)
    X, v, self.x_translator = numerical(X_obj)

    if out_f:
      To = load_csv(out_f, self.ots)
      Y_obj = labels(Ti,To)
      Y, k, self.y_translator = numerical(Y_obj)

    self.hmm = hmm.HMM(k, v)
    self.hmm.train(X,Y)

  def extract(self, test_f):
    # ingest test data
    T_test = load_txt(test_f, self.ots)
    X_obj_test = featurize(T_test, self.phi)
    X_test, _, _ = numerical(X_obj_test, self.x_translator)

    # viterbi
    Z = []
    for x_test in X_test:
      Z.append(self.hmm.viterbi(x_test))

    # chunk fields
    csv = []
    for i in range(len(Z)):
      z_i = Z[i]
      x_i = T_test[i]
      row = []
      fields = group_fields(z_i, x_i)
      for i in range(self.hmm.k):
        row.append(fields.get(i,''))
      csv.append(row[:4])

    return csv

  def extract2csv(self, test_f):
    pass
