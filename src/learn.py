import itertools
import numpy as np

def featurize(TX, phi):
  X = []
  for tx in TX:
    x = [phi(token) for token in tx]
    X.append(x)
  return X

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
    return self.num2val[num]

  def get_num(self, val):
    return self.val2num[val]

def numerical(TX, translator=None):
  X = []
  vals = set()
  if not translator:
    translator = Translator()
    vals = set(itertools.chain.from_iterable(TX))
    for val in vals:
      translator.add(val)
  for tx in TX:
    X.append([translator.get_num(tx_i) for tx_i in tx])
  return np.array(X), len(vals), translator
