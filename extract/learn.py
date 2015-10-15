import itertools
import numpy as np

def featurize(tx, phi):
  return [phi(token) for token in tx]

class Translator:

  def __init__(self):
    self.counter = 0
    self.val2num = {}
    self.num2val = {}

  def add(self, val):
    past_num = self.val2num.get(val, None)
    if past_num:
      del self.val2num[val]
    self.val2num[val] = self.counter
    self.num2val[self.counter] = val
    self.counter += 1

  def remove(self, val):
    num = self.val2num[val]
    del self.val2num[val]
    del self.num2val[num]

  def remove_num(self, num):
    val = self.num2val[num]
    del self.num2val[num]
    del self.val2num[val]

  def get_val(self, num):
    return self.num2val.get(num, None)

  def get_num(self, val):
    # return -1 to signal unseen value
    return self.val2num.get(val, -1)

def numerical(tx, translator):
  return [translator.get_num(tx_i) for tx_i in tx]

# TODO OBSOLETE condition: record-by-record architecture
def featurize_all(TX, phi):
  X = []
  for tx in TX:
    X.append(featurize(tx,phi))
  return X

# TODO OBSOLETE condition: record-by-record architecture
def numerical_all(TX, translator=None):
  X = []
  vals = set()
  if not translator:
    translator = Translator()
    vals = set(itertools.chain.from_iterable(TX))
    for val in vals:
      translator.add(val)
  for tx in TX:
    X.append(numerical(tx, translator))
  return np.array(X), len(vals), translator
