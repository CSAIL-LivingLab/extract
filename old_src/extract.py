from hmm import HMM
from learn import featurize
from parse import parse_data, parse_labels, label 

def token_types(x):
  def token_type(t):
    return t.typ()
  return map(token_type, x)

def labels(Tx, Te):
  Y = []
  assert len(Tx) == len(Te)
  for i in range(len(Tx)):
    x_i = Tx[i]
    e_i = Te[i]
    Y.append(label(x_i, e_i))
  return Y

def flatten(l):
  return [item for sublist in l for item in sublist]

class FieldExtractor:

  def __init__(self):
    self.hmm = None

  def learn(self, pre_extraction_file, post_extraction_file):
    Tx = parse_data(pre_extraction_file)
    Te = parse_labels(post_extraction_file)
    X = featurize(Tx, token_types)
    print X
    Y = labels(Tx, Te)

    hidden_states = set(flatten(Y))
    observation_set = set(flatten(X))
    print Y
    self.hmm = HMM(hidden_states, observation_set)
    self.hmm.train(X,Y)

  def run(self, data_file):
    pass
