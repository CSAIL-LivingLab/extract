Xtract
======
Extracting fields from semi-structured data

Install
-------
Installation via `pip`
```bash
git clone https://github.com/pcattori/extract.git
cd extract
pip install .
```

API
---

```python
fe = FieldExtractor(fields)
for piece_of_txt, extraction_example in training_pairs:
  fe.train(piece_of_txt, extraction_example)
for piece_of_txt in txt_file:
  extraction = fe.extract(piece_of_txt)
  print extraction # or do something interesting with the extraction
```

Eg.
```python
fields = ['date', 'time', 'src', 'dest']
fe = FieldExtractor(fields)


piece_of_txt = '2012-01-04 00:01:23,180 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block blk_-2281137920769708011_1116 src: /127.0.0.1:32981 dest: /127.0.0.1:50010'

extraction_example = {
  'date':'2012-01-04',
  'time':'00:01:23',
  'src':'127.0.0.1:32981',
  'dest':'127.0.0.1:50010'
}

# in this simple example, train with just 1 training pair
fe.train(piece_of_txt, extraction_example)

hadoop_txt = 'data/hadoop/test.txt' # provide path to some target txt file
for line in open(hadoop_txt):
  print fe.extract(line)
```

TODO
----
- unsupervised learning via baum-welch to learn the token types (this could indirectly fix the 'multiple fields clashing' bug)
- type hierarchy and progressive deepening
- submodels for fields
- detecting field separators via language modeling
  - detecting record separators in the same way

BUGS
----
No known bugs
