import numpy as np
from .linalg import normalize_cols, normalize_rows

def featurize(tokens, phi=None):
  def typ(t):
    return t.typ
  if not phi:
    phi = typ
  return [phi(token) for token in tokens]

def smooth(v, alpha):
  '''Additive smoothing'''
  return (v + alpha) / (sum(v) + len(v) * alpha)

class NumericalTranslator:

  def __init__(self, words):
    num = 0
    self._num2word = {}
    self._word2num = {}
    for word in words:
      self._num2word[num] = word
      self._word2num[word] = num
      num += 1

  def numerical(self,tokens):
    w = [self.num(token) for token in tokens]
    assert None not in w
    return w

  def num(self, word):
    return self._word2num.get(word, None)

  def word(self, num):
    return self._num2word.get(num, None)

class HiddenMarkovModelStatistics:

  def __init__(self, k, v):
    self.k = k
    self.v = v

    self.s_count = np.zeros(shape=(self.k,1))
    self.t_count = np.zeros(shape=(self.k,self.k))
    self.e_count = np.zeros(shape=(self.k,self.v))

  def include(self, x, y):
    self.s_count += self._start_count(y)
    self.t_count += self._trans_count(y)
    self.e_count += self._emit_count(x,y)

  def normalize(self):
    S = normalize_cols(self.s_count)
    T = normalize_rows(self.t_count)
    E = normalize_rows(self.e_count)
    return S,T,E

  def smoothed_normalize(self, alpha):
    S,T,E = self.normalize()
    S = smooth(S, alpha)
    for i in range(len(T)):
      T[i,:] = smooth(T[i,:], alpha)
    for i in range(len(E)):
      E[i,:] = smooth(E[i,:], alpha)
    return S, T, E

  # convenience
  #############

  def _start_count(self, y):
    s_count = np.zeros(shape=(self.k, 1))
    s_count[y[0]] = 1
    return s_count

  def _trans_count(self, y):
    t_count = np.zeros(shape=(self.k, self.k))
    for t in range(len(y) - 1):
      t_count[y[t], y[t+1]] += 1
    return t_count

  def _emit_count(self, x, y):
    e_count = np.zeros(shape=(self.k, self.v))
    for t in range(len(y)):
      e_count[y[t], x[t]] += 1
    return e_count
