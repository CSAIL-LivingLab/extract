import hmm
from itertools import chain

class FieldExtractor:

  def __init__(self):
    self.hmm = None

  def ingest(fX,fY):
    pass

  def train(self, X, Y=None):
    hidden_states = list(set(chain.from_iterable(Y)))
    outputs = list(set(chain.from_iterable(X)))
    self.hmm = hmm.HMM(hidden_states, outputs)
    self.hmm.train(X,Y)

  def extract(self, x):
    return self.hmm.viterbi(x)

  def extract_all(self, X):
    csv = []
    for x in X:
      self.extract(x)
      
