import sys
from extract import FieldExtractor
from extract.ingest import load_txt, load_csv
from os import path

if __name__ == '__main__':
  folder = sys.argv[1]

  if not path.exists(folder):
    raise ValueError("Folder '{}' does not exist".format(folder))

  training_txt_records = load_txt(path.join(folder, 'input.txt'))
  fields, training_txt_labels = load_csv(path.join(folder, 'output.csv'))
  test_txt_records = load_txt(path.join(folder, 'test.txt'))

  fe = FieldExtractor(fields)

  fe.train(training_txt_records, training_txt_labels)

  ## uncomment below to display matrices for hmm
  #print fe.hmm.start_p
  #print fe.hmm.trans_p
  #print fe.hmm.emit_p

  print fe.extract(test_txt_records)

