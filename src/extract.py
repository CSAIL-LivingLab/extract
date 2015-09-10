import hmm
import numpy as np
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

def labels2csv(Z, Tx):
  csv = []
  for i in range(len(Z)):
    z_i = Z[i]
    tx_i = Tx[i]
    row = []
    fields = group_fields(z_i, tx_i)
    for j in range(max(chain.from_iterable(Z))):
      row.append(fields.get(j,''))
    csv.append(row)
  return csv

class FieldExtractor:

  def __init__(self, observation_types):
    self.phi = phi
    self.ots = observation_types
    self.hmm = None
    self.x_translator = None
    self.y_translator = None
    self.header = None

  def train(self, in_f, out_f=None):
    Ti = load_txt(in_f, self.ots)
    X_obj = featurize(Ti, self.phi)
    X, v, self.x_translator = numerical(X_obj)
    print self.x_translator.val2num

    if out_f:
      self.header, To = load_csv(out_f, self.ots)
      Y_obj = labels(Ti,To, self.header)
      Y, k, self.y_translator = numerical(Y_obj)
      self.hmm = hmm.HMM(k, v)
      self.hmm.train(X,Y)
    else:
      raise NotImplementedError()

  def extract(self, test_f):
    # ingest test data
    T_test = load_txt(test_f, self.ots)
    X_obj_test = featurize(T_test, self.phi)
    X_test, _, _ = numerical(X_obj_test, self.x_translator)
    np.set_printoptions(threshold=np.nan)

    # viterbi
    Z = []
    for x_test in X_test:
      Z.append(self.hmm.viterbi(x_test))

    # chunk fields
    csv = labels2csv(Z, T_test)

    # filter
    return self._header_filter(csv)

  # subroutines
  #############

  def _header_filter(self, csv):
    filtered_csv = []
    indices = [self.y_translator.get_num(attr) for attr in self.header]
    for row in csv:
      filtered_csv.append([row[j] for j in indices])
    return filtered_csv
