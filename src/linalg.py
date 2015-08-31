import numpy as np

# linear algebra utility functions

def normalize_cols(M):
  sums = M.sum(axis=0)
  sums[sums == 0] = 1
  return M.astype(float) / sums

def normalize_rows(M):
  return normalize_cols(M.T).T

def is_col_stochastic(M, threshold=1e-8):
  return np.all(np.absolute(M.sum(axis=0) - np.ones(M.shape[1])) <= threshold)

def is_row_stochastic(M, threshold=1e-8):
  return is_col_stochastic(M.T, threshold)
