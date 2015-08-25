import hmm
from learn import normalize_cols, normalize_rows
import numpy as np

def test_supervised_learn(hidden_states, outputs):

  real_hmm = hmm.HiddenMarkovModel(hidden_states, outputs)

  k,v = len(hidden_states), len(outputs)

  S_actual = normalize_cols(np.random.randint(10, size=(k,1)))
  T_actual = normalize_rows(np.random.randint(10, size=(k,k)))
  E_actual = normalize_rows(np.random.randint(10, size=(k,v)))
  print 'ACTUAL'
  print S_actual
  print T_actual
  print E_actual
  print 'end actual'

  real_hmm.set_params(S_actual, T_actual, E_actual)

  t, n = 3, 1000
  Y = np.zeros(shape=(n,t))
  X = np.zeros(shape=(n,t))
  for i in range(n):
    y_i,x_i = real_hmm.generate(t)
    Y[i,:] = y_i
    X[i,:] = x_i

  print 'DATA'
  print X
  print Y
  print 'end data'

  model = hmm.HiddenMarkovModel(hidden_states, outputs)
  model.train(X, Y)
  print 'LEARNED'
  print model.start_p
  print model.trans_p
  print model.emit_p
  print 'end learned'

  y_actual, x = real_hmm.generate(t)
  y_predicted = model.viterbi(x)
  print 'PREDICT'
  print y_actual
  print y_predicted
  print 'end predict'

test_supervised_learn(['A', 'B', 'C', 'D', 'E'], ['x', 'y', 'z'])
