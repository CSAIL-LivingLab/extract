import csv

# load
######

def load_txt(filename):
  raw_data = []
  with open(filename, 'r') as f:
    for line in f:
      raw_data.append(line)
  return raw_data

def load_csv(filename):
  with open(filename, 'rb') as f:
    table = list(csv.reader(f, skipinitialspace=True, delimiter=',', quotechar='"'))
    header = table[0]
    return header, table[1:]
