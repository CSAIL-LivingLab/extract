# -*- coding: utf-8 -*-
import numpy as np
from .linalg import normalize_cols, normalize_rows

def typ(t):
  return t.typ

def featurize(tokens, phi=typ):
  return [phi(token) for token in tokens]

def normalize(M, smoothing=0, axis=0):
  u'''Additive smoothing
  M -- the numpy array/matrix to be normalized
  smoothing -- additive smoothing paramater α
  axis -- specifices the axis along which to normalize
  '''
  def smooth(v):
    return (v + smoothing) / (sum(v) + len(v) * smoothing)
  return np.apply_along_axis(smooth, axis, M)
