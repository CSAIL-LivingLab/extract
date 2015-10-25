# -*- coding: utf-8 -*-
import numpy as np
from .prob import sample_pmf
from .learn import normalize
from .linalg import is_col_stochastic, is_row_stochastic

# Hidden Markov Model
#####################

class HiddenMarkovModel:
  '''Hidden Markov Model that addresses the 3 Machine Learning questions:
  1. Evaluate the probability of observed data
  2. Find the most likely hidden state sequence (z) given observations (x)
  3. Estimate the parameters of the model from multiple sequences (z,x)
  '''

  def __init__(self, hidden_states, observations):
    self.hidden_states = list(set(hidden_states))
    self.observations = list(set(observations))

    self._start_p = None
    self._trans_p = None
    self._emit_p = None

  # TODO maintain stochastic invariant and check dimensions of M
  @property
  def start_p(self):
    u'''Initial state probability matrix, commonly referred to Π'''
    return self._start_p

  @start_p.setter
  def start_p(self, M):
    self._start_p = M

  @property
  def trans_p(self):
    '''State transition probability matrix, commonly referred to A'''
    return self._trans_p

  @trans_p.setter
  def trans_p(self, M):
    self._trans_p = M

  @property
  def emit_p(self):
    '''Emission probability matrix, commonly referred to as O'''
    return self._emit_p

  @emit_p.setter
  def emit_p(self, M):
    self._emit_p = M

  # convenvience
  ##############

  @property
  def k(self):
    return len(self.hidden_states)

  @property
  def v(self):
    return len(self.observations)

  # numerical translation
  #######################

  def _hidden_state_names(self, *indices):
    return [self.hidden_states[index] for index in indices]

  def _hidden_state_indices(self, *names):
    return [self.hidden_states.index(name) for name in names]

  def _observation_names(self, *indices):
    return [self.observations[index] for index in indices]

  def _observation_indices(self, *names):
    return [self.observations.index(name) for name in names]

  # generation
  ############

  def generate(self, n):
    '''Generates a sequence of n (state,output) pairs via random walk through the HMM.'''
    state = None
    for _ in xrange(n):
      state, output = self._step(state)
      yield state, output

  def _step(self, state):
    trans_p = None
    if state is None:
      # pick a starting state
      trans_p = self._start_p.T
    else:
      state_index, = self._hidden_state_indices(state)
      trans_p = self._trans_p[state_index, :]

    new_state = sample_pmf(self.hidden_states, trans_p)
    new_state_index = self._hidden_state_indices(new_state)
    output = sample_pmf(self.observations, self._emit_p[new_state_index, :])

    return new_state, output

  def probability(self, z, x):
    '''Evaluate the probability of observed data'''
    # TODO
    pass

  # most likely sequence of hidden states
  #######################################

  def viterbi(self, x):
    '''Find the most likely hidden state sequence (z) given observations (x).
    x -- sequence of observations
    Returns the most likely state path and the probability associate with that path
    '''
    # numerically translate x
    x = self._observation_indices(*x)

    V = [{}]
    path = {}

    # Initialize base cases (t == 0)
    for z in range(self.k):
      V[0][z] = self._start_p[z] * self._emit_p[z][x[0]]
      path[z] = [z]

    # Run Viterbi for t > 0
    for t in range(1, len(x)):
      V.append({})
      newpath = {}

      for z in range(self.k):
        prob, state = max((V[t-1][z0] * self._trans_p[z0][z] * self._emit_p[z][x[t]], z0) for z0 in range(self.k))
        V[t][z] = prob
        newpath[z] = path[state] + [z]

      # Don't need to remember the old paths
      path = newpath

    prob, state = max((V[-1][z], z) for z in range(self.k))
    return self._hidden_state_names(*path[state]), prob[0]

  # parameter estimation
  ######################

  def supervised_learn(self, training_pairs, smoothing=0):
    u'''Estimate the parameters of the model from multiple sequences (z,x)
    training_pairs -- sequence of (x,y) pairs for use as training examples
    smoothing -- Additive smoothing parameter α
    '''
    start_count = np.zeros(shape=(self.k, 1))
    trans_count = np.zeros(shape=(self.k, self.k))
    emit_count = np.zeros(shape=(self.k, self.v))

    for x, y in training_pairs:
      # numerical translation
      x = self._observation_indices(*x)
      y = self._hidden_state_indices(*y)

      start_count += self._start_count(y)
      trans_count += self._trans_count(y)
      emit_count += self._emit_count(x, y)

    self._start_p = normalize(start_count, smoothing=smoothing)
    self._trans_p = normalize(trans_count, smoothing=smoothing, axis=1)
    self._emit_p = normalize(emit_count, smoothing=smoothing, axis=1)

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
