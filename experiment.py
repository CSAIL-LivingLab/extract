import csv
import sys

if __name__ == '__main__':
  filename = sys.argv[1]
  with open(filename, 'rb') as f:
    return list(csv.reader(f, skipinitialspace=True, delimiter=',', quotechar='"'))
