import numpy as np
from parse import Token

# convenience
#############

def normalize_cols(M):
  return M.astype(float) / M.sum(axis=0)

def normalize_rows(M):
  return normalize_cols(M.T).T

# supervised parameter estimation
#################################

def supervised_learn(model,X,Y):
  k, v = len(model.hidden_states), len(model.outputs)

  s_count = np.zeros(shape=(k,1))
  for y_i in Y:
    s_count[y_i[0]] += 1
  S = normalize_cols(s_count)

  t_count = np.zeros(shape=(k,k))
  for y_i in Y:
    for t in range(len(y_i) - 1):
     t_count[y_i[t], y_i[t+1]] += 1
  T = normalize_rows(t_count)

  e_count = np.zeros(shape=(k,v))
  for i in range(len(Y)):
    y_i = Y[i,:]
    x_i = X[i,:]
    for t in range(len(y_i)):
      e_count[y_i[t], x_i[t]] += 1
  E = normalize_rows(e_count)

  return S,T,E

# transformation
################

def featurize(T, f):
  X = []
  for t in T:
    x = f(t)
    x.append('end')
    X.append(x)
  return X
