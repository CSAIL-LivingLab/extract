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

  # 
  # print len(training_txt_records)
  # print len(training_txt_labels)
  # print zip(training_txt_records, training_txt_labels)[:5]

  # smoothing allows some guessing. lookup additive smoothing
  fe.learn(zip(training_txt_records, training_txt_labels), smoothing=1e-3)

  ## uncomment below to display matrices for hmm
  ## should not be even (obvi?)
  # print fe._hmm.start_p
  # print fe._hmm.trans_p
  # print fe._hmm.emit_p


  for test_txt_record in test_txt_records:
    print fe.extract(test_txt_record)

