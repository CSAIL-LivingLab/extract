import src.hmm
from src.extract import FieldExtractor
import numpy as np

fe = FieldExtractor()
fe.learn('data/hadoop/input.txt', 'data/hadoop/output.csv')

def hmm_test():
  hidden_states = ['A', 'B', 'C']
  observable_outputs = ['a','b','c']
  model = hmm.HMM(hidden_states, observable_outputs)
  S = np.array([1,0,0]).reshape(3,1)
  print S
  T = np.array([[0.2,0.8,0],[0,0,1],[0.1,0.5,0.4]])
  print T
  E = np.array([[1,0,0],[0,1,0],[0,0,1]])
  print E
  model.set_params(S,T,E)
  while True:
    m = raw_input('run? > ')
    if m.isdigit():
      z,x = model.generate(int(m))
      print 'z:',z
      print 'x:',x
    else:
      break
