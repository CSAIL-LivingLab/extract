import sys
from src.parse import read_data, tokenize, parse_data, featurize

if __name__ == '__main__':
  filename = sys.argv[1]
  raw_data = read_data(filename)
  tokens = tokenize(raw_data)
  logical_data = parse_data(tokens)
  oo = featurize(logical_data)
  print oo
