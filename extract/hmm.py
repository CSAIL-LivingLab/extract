import numpy as np
from .prob import sample_pmf
from .linalg import is_col_stochastic, is_row_stochastic

# Hidden Markov Model
#####################

class HiddenMarkovModel:

  def __init__(self, k, v):
    self.k = k
    self.v = v

    self._start_p = None
    self._trans_p = None
    self._emit_p = None

  # TODO is this method worth having?
  def set_params(self, start_p, trans_p, emit_p):

    if np.all(start_p.shape == (self.k, 1)):
      if is_col_stochastic(start_p):
        self._start_p = start_p
      else:
        raise ValueError('start_p not column stochastic')
    else:
      raise ValueError('start_p shape not k,1')

    if np.all(trans_p.shape == (self.k, self.k)):
      if is_row_stochastic(trans_p):
        self._trans_p = trans_p
      else:
        raise ValueError('trans_p not row stochastic')
    else:
      raise ValueError('trans_p shape not k,k')

    if np.all(emit_p.shape == (self.k, self.v)):
      if is_row_stochastic(emit_p):
        self._emit_p = emit_p
      else:
        raise ValueError('emit_p not row stochastic')
    else:
      raise ValueError('emit_p shape not k,v')

  # generation
  ############

  def generate(self, count):
    x = []
    z = []
    state = None
    for _ in xrange(count):
      state, output = self._step(state)
      z.append(state)
      x.append(output)
    return z, x

  # parameter estimation
  ######################

  def supervised_learn(self, X, Y):
    hmm_stats = HMM_Statistics(self.k, self.v)
    for i in range(len(X)):
      x_i = X[i,:]
      y_i = Y[i,:]
      hmm_stats.include(x_i, y_i)

    self.set_params(*hmm_stats.normalize())

  # most likely sequence of hidden states
  #######################################

  def viterbi(self, obs):
    V = [{}]
    path = {}

    # Initialize base cases (t == 0)
    for y in range(self.k):
      V[0][y] = self._start_p[y] * self._emit_p[y][obs[0]]
      path[y] = [y]

    # Run Viterbi for t > 0
    for t in range(1, len(obs)):
      V.append({})
      newpath = {}

      for y in range(self.k):
        prob, state = max((V[t-1][y0] * self._trans_p[y0][y] * self._emit_p[y][obs[t]], y0) for y0 in range(self.k))
        V[t][y] = prob
        newpath[y] = path[state] + [y]

      # Don't need to remember the old paths
      path = newpath
    n = 0           # if only one element is observed max is sought in the initialization values
    if len(obs) != 1:
      n = t
    prob, state = max((V[n][y], y) for y in range(self.k))
    return path[state], prob[0]


  # convenience
  #############

  def _step(self, state):
    states = np.arange(self.k)
    if state is None:
      # pick a starting state
      p_states = self._start_p.T
    else:
      p_states = self._trans_p[state, :]
    new_state = sample_pmf(states, p_states)

    outputs = np.arange(self.v)
    p_outputs = self._emit_p[new_state, :]
    return new_state, sample_pmf(outputs, p_outputs)

