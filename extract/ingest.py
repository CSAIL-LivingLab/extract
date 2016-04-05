import csv

# load
######

def load_txt(filename):
  raw_data = []
  with open(filename, 'r') as f:
    for line in f:
      raw_data.append(line)
  print 'raw_data', raw_data[:5]
  return raw_data

def load_csv(filename):
  with open(filename, 'rb') as f:
    reader = csv.DictReader(f, skipinitialspace=True, delimiter=',', quotechar='"')
    return reader.fieldnames, [row for row in reader]
