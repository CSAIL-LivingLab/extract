import pickle
from extract import FieldExtractor
from extract.ingest import load_txt
import sys

if __name__ == '__main__':
  #x,e,states,connections
  fields = ['date', 'time', 'src', 'dest']
  aux_fields = ['src_prefix', 'dest_prefix']
  connections = {'src_prefix':set(['src']), 'dest_prefix':set(['dest'])}
  custom_tokens = {'src': 'src:', 'dst': 'dest:'}

  test = load_txt(sys.argv[1])

  alpha = 0
  if len(sys.argv) > 2:
    alpha = float(sys.argv[2])

  #fe = FieldExtractor(fields)
  fe = FieldExtractor(
      fields,
      aux_fields=aux_fields,
      connections=connections,
      custom_tokens=custom_tokens
  )

  x = '2012-01-04 00:01:23,180 INFO org.apache.hadoop.hdfs.server.datanode.DataNode: Receiving block blk_-2281137920769708011_1116 src: /127.0.0.1:32981 dest: /127.0.0.1:50010'
  e = {
      'date':'2012-01-04',
      'time':'00:01:23',
      'src_prefix':'src:',
      'src':'127.0.0.1:32981',
      'dest_prefix':'dest:',
      'dest':'127.0.0.1:50010'
  }

  fe.learn([(x,e)], alpha)
  print fe.ambiguity(0.3)


  #for t in test:
    #print fe.extract(t)
