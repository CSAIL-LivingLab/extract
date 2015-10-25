# -*- coding: utf-8 -*-
from collections import namedtuple, defaultdict
from .hmm import HiddenMarkovModel as HMM
from .learn import featurize
from .lex import Lexer, find, DEFAULT_TOKEN_DEFS, Token

# TODO field namespace? other namespaces? uniqueness

# Use-case: 1 FE / extraction
class FieldExtractor:
  '''Extracts fields from text via the Viterbi algorithm.
  Learns a model via the HMM supervised learning algorithm.
  '''

  _GARBAGE_STATE = None
  # TODO different smoothing parameters for differents states/observations

  def __init__(self, fields, aux_fields=[], connections={}, custom_tokens={}):
    '''Initializes a FieldExtractor with a Lexer and an HMM.
    fields -- sequence with the names of the target fields for extraction
    aux_fields -- sequence of auxiliary fields that may help to model the target fields
    connections -- describes important state transitions (ignoring garbage sequences)
    custom_tokens -- a mapping between names and regex's to help model the language
    '''
    self._fields = set(fields)
    self._aux_fields = set(aux_fields)
    self._connections = connections
    self._custom_tokens = custom_tokens

    self._lexer = Lexer(DEFAULT_TOKEN_DEFS, custom_types=custom_tokens)

    self._hmm = HMM(self._states(), self._outputs())

  def learn(self, training_examples, smoothing=0):
    '''Trains the underlying HMM via machine learning techniques.
    training_examples -- sequence of (txt,extraction) examples
    '''
    training_pairs = (self._training_pair(example) for example in training_examples)
    self._hmm.supervised_learn(training_pairs, smoothing=smoothing)
    #print self._hmm.start_p
    #print self._hmm.trans_p
    #print self._hmm.emit_p

  def _training_pair(self, training_example):

    txt_example, extraction_example = training_example

    # txt_record -> x
    x_tokens = self._lexer.tokenize(txt_example)
    x = featurize(x_tokens)

    # extraction_example -> y
    y_tokens = {
        field: self._lexer.tokenize(extract, stop=False)
        for field, extract in extraction_example.iteritems()
    }
    y = _label(x_tokens, y_tokens, connections=self._connections)

    return x, y

  def extract(self, txt_record):
    '''Extracts pieces of text corresponding to fields.
    Returns an extraction map {field: extract} and the probability of the extraction
    '''
    # digest input
    t_test = self._lexer.tokenize(txt_record)
    x_test = featurize(t_test)

    # ML guess
    z, probability = self._hmm.viterbi(x_test)

    # group by field
    raw_extraction = _group_fields(z, t_test)

    # TODO normalize probabilities to come up with confidences
    return raw_extraction, probability

  def all_field_filter(self, raw_extraction):
    '''Filters out any mappings whose state is not a field or auxiliary field.
    Eg. Filters out the garbage state and states derived from connections
    raw_extraction -- a mapping from state names to extracts
    '''
    filtered = {
        field: extract
        for field,extract in raw_extraction.iteritems()
        if field in self._fields | self._aux_fields
    }
    return filtered

  # subroutines
  #############

  def _states(self):
    states = [FieldExtractor._GARBAGE_STATE]
    states.extend(self._fields)
    states.extend(self._aux_fields)
    for from_state, to_states in self._connections.iteritems():
      states.extend([_connection(from_state, to_state) for to_state in to_states])
    return states

  def _outputs(self):
    outputs = [Token.STOP]
    outputs.extend(self._lexer.types.keys())
    return outputs

# utils
#######

def _connection(from_state, to_state):
  return u'{} ➞ {}'.format(from_state, to_state)

def _label(x_tokens, y_tokens, connections={}):
  '''Produces a sequence of field names acting as a label for the observation sequence.
  x_tokens -- the tokenized observation sequence
  y_tokens -- a mapping from field names to individually-tokenized extracts
  connections -- state transitions that ignore garbage gaps between the states
  '''

  labels = [None] * len(x_tokens)

  # label fields and aux fields
  for state, extract in y_tokens.iteritems():
    i = find(x_tokens, extract)
    labels[i : i + len(extract)] = [state] * len(extract)

  # fill in gaps with corresponding connections
  for gap in _gaps(labels):
    start, stop = gap.start, gap.end
    from_state = labels[start - 1]
    to_state = labels[stop]
    if to_state in connections.get(from_state, set()):
      labels[start:stop] = [_connection(from_state, to_state)] * (stop - start)
  return labels

def _gaps(labels):
  '''Find start/stop indices for all unbroken sequences of None.
  labels -- a sequence of field names
  '''
  Gap = namedtuple('Gap', ['start', 'end'])
  gaps = []

  field_indices = []
  for index, label in enumerate(labels):
    if label is not None:
      field_indices.append(index)

  for i in range(0, len(field_indices) - 1):
    field_index = field_indices[i]
    next_field_index = field_indices[i + 1]
    if field_index + 1 != next_field_index:
      # gap detected
      start = field_index + 1
      end = next_field_index
      gaps.append(Gap(start=start, end=end))

  return gaps

def _group_fields(z, x_tokens):
  '''Maps field names to their extracts'''
  fields = defaultdict(list)
  extract = [x_tokens[0]]
  for t in range(1,len(x_tokens)):
    field = z[t - 1]
    if z[t] == field:
      extract.append(x_tokens[t])
    else:
      fields[field].append(Lexer.detokenize(extract))
      extract = [x_tokens[t]]
  # handle dangling extract
  fields[z[-1]].append(Lexer.detokenize(extract))
  return fields
