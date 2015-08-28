import numpy as np

# linear algebra utility functions

def normalize_cols(M):
  return M.astype(float) / M.sum(axis=0)

def normalize_rows(M):
  return normalize_cols(M.T).T

def is_col_stochastic(M, threshold=1e-8):
  return np.all(np.absolute(M.sum(axis=0) - np.ones(M.shape[1])) <= threshold)

def is_row_stochastic(M, threshold=1e-8):
  return is_col_stochastic(M.T, threshold)
