import hmm
from itertools import chain

class FieldExtractor:

  def __init__(self):
    self.hmm = None

  def train(self, X, Y=None):
    hidden_states = list(set(chain.from_iterable(Y)))
    print hidden_states
    outputs = list(set(chain.from_iterable(X)))
    print outputs
    self.hmm = hmm.HMM(hidden_states, outputs)
    self.hmm.train(X,Y)
