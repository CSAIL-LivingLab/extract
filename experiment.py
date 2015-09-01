import sys
from src.extract import FieldExtractor
from src.parse import load_data, parse_data, featurize, load_extractions, examples2labels

def typ(token):
  return token.typ()

if __name__ == '__main__':
  filename = sys.argv[1]
  tokens = load_data(filename)
  print 'tokens',tokens
  TX = parse_data(tokens)
  for tx in TX:
    print 'tx', tx
  phi = typ
  X = featurize(TX, phi)
  print 'X',X

  TE = load_extractions(sys.argv[2])
  Y = examples2labels(TX, TE)
  print 'Y',Y

  fe = FieldExtractor()
  fe.train(X,Y)

  print fe.hmm.start_p
  print fe.hmm.trans_p
  print fe.hmm.emit_p

  X_test = featurize(parse_data(load_data(sys.argv[3])), phi)
  for x_test in X_test:
    print fe.extract(x_test)
