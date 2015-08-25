import learn
import numpy as np
from scipy.stats import rv_discrete

def is_col_stochastic(M, threshold=1e-8):
  return np.all(np.absolute(M.sum(axis=0) - np.ones(M.shape[1])) <= threshold)

def is_row_stochastic(M, threshold=1e-8):
  return is_col_stochastic(M.T, threshold)

def sample_pmf(vals, probs):
    rv = rv_discrete(values=(vals, probs))
    return rv.rvs(size=1)

class HiddenMarkovModel:

  def __init__(self, hidden_states, outputs):
    self.hidden_states = hidden_states
    self.outputs = outputs

    self.start_p = None
    self.trans_p = None
    self.emit_p = None

  def set_params(self, start_p, trans_p, emit_p):
    k, v = len(self.hidden_states), len(self.outputs)

    if np.all(start_p.shape == (k,1)):
      if is_col_stochastic(start_p):
        self.start_p = start_p
      else:
        raise ValueError('start_p not column stochastic')
    else:
      raise ValueError('start_p shape not k,1')

    if np.all(trans_p.shape == (k,k)):
      if is_row_stochastic(trans_p):
        self.trans_p = trans_p
      else:
        raise ValueError('trans_p not row stochastic')
    else:
      raise ValueError('trans_p shape not k,k')

    if np.all(emit_p.shape == (k,v)):
      if is_row_stochastic(emit_p):
        self.emit_p = emit_p
      else:
        raise ValueError('emit_p not row stochastic')
    else:
      raise ValueError('emit_p shape not k,v')


  def step(self, state):
    states = np.arange(len(self.hidden_states))
    if state is None:
      # pick a starting state
      p_states = self.start_p.T
    else:
      p_states = self.trans_p[state, :]
    new_state = sample_pmf(states, p_states)

    outputs = np.arange(len(self.outputs))
    p_outputs = self.emit_p[new_state, :]
    return new_state, sample_pmf(outputs, p_outputs)

  def generate(self, count):
    x = []
    z = []
    state = None
    for _ in xrange(count):
      state, output = self.step(state)
      z.append(state)
      x.append(output)
    return z, x

  def train(self, X,Y=None):
    if Y is None:
      # TODO unsupervised learning
      pass
    else:
      start_p, trans_p, emit_p = learn.supervised_learn(self, X, Y)
      self.set_params(start_p, trans_p, emit_p)

  def viterbi(self, obs):
    V = [{}]
    path = {}

    # Initialize base cases (t == 0)
    for y in range(len(self.hidden_states)):
      V[0][y] = self.start_p[y] * self.emit_p[y][obs[0]]
      path[y] = [y]

    # Run Viterbi for t > 0
    for t in range(1, len(obs)):
      V.append({})
      newpath = {}

      for y in range(len(self.hidden_states)):
        (prob, state) = max((V[t-1][y0] * self.trans_p[y0][y] * self.emit_p[y][obs[t]], y0) for y0 in range(len(self.hidden_states)))
        V[t][y] = prob
        newpath[y] = path[state] + [y]

      # Don't need to remember the old paths
      path = newpath
    n = 0           # if only one element is observed max is sought in the initialization values
    if len(obs) != 1:
      n = t
    (prob, state) = max((V[n][y], y) for y in range(len(self.hidden_states)))
    return (prob, path[state])
