from .hmm import HiddenMarkovModel as HMM
from .learn import featurize, NumericalTranslator, HiddenMarkovModelStatistics as HMM_Statistics
from .lex import Lexer

# TODO set lexer with hierarchy
default_types = {
  'num': '\d+',
  'abc': '[a-zA-Z]+',
  #'sym': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?\s]'
  'spc': '\s+',
  #'pnc': '[-`=[\]\\\\;\',./~!@#$%^&*()_+{}|:"<>?]'
  'hyp': '[-]{1}',
  'cln': '[:]{1}',
  'prd': '[.]{1}',
  'pnc': '[`=[\]\\\\;\',/~!@#$%^&*()_+{}|"<>?]',
}

# Use-case: 1 FE / extraction
class FieldExtractor:

  _GARBAGE_FIELD = None
  _DEFAULT_ALPHA = 1e-3

  # TODO aggressive smoothing for garbage state, differentiate smoothing between HMM matrices
  def __init__(self, fields, aux_fields=[], connections={}, custom_tokens={}):
    self._fields = set(fields)
    self._aux_fields = set(aux_fields)
    self._connections = connections
    self._custom_tokens = custom_tokens

    types = default_types.copy()
    types.update(self._custom_tokens)
    self._lexer = Lexer(types)

    k = len(self._states())
    v = len(self._outputs())
    self._hmm_stats = HMM_Statistics(k,v)
    self._x_translator = NumericalTranslator(self._outputs())
    self._y_translator = NumericalTranslator(self._states())

    # Tunable parameters
    self.alpha = FieldExtractor._DEFAULT_ALPHA

  def train(self, txt_record_example, extraction_example):

    # txt_record -> x
    x_tokens = self._lexer.tokenize(txt_record_example)
    x_obj = featurize(x_tokens)
    x = self._x_translator.numerical(x_obj)

    # extraction_example -> y
    y_tokens = {}
    for field_name, extracted_field in extraction_example.iteritems():
      y_tokens[field_name] = self._lexer.tokenize(extracted_field, stop=False)
    y_obj = extraction2label(x_tokens, y_tokens, self._connections)
    y = self._y_translator.numerical(y_obj)

    # include x,y in statistics
    self._hmm_stats.include(x, y)

  def _hmm(self):
    # HMM
    k = len(self._states())
    v = len(self._outputs())
    hmm = HMM(k,v)
    #self._hmm.set_params(*self._hmm_stats.normalize())
    S,T,E = self._hmm_stats.smoothed_normalize(self.alpha)
    hmm.set_params(S, T, E)
    #print hmm._start_p
    #print hmm._trans_p
    #print hmm._emit_p
    return hmm

  def extract(self, txt_record):
    '''Extracts pieces of text corresponding to fields.
    Returns a tuple with a dictionary mapping field names to a list of matching extraction and a confidence in the extraction as a probability.
    '''
    # digest input
    t_test = self._lexer.tokenize(txt_record)
    x_obj_test = featurize(t_test)
    x_test = self._x_translator.numerical(x_obj_test)

    # ML guess
    z, confidence = self._hmm().viterbi(x_test)

    # group by internal field number
    fields = group_fields(z, t_test)

    # translate field numbers to field names
    raw_extraction = {}
    for field_num, field in fields.iteritems():
      raw_extraction[self._y_translator.word(field_num)] = field

    # TODO normalize confidences
    return raw_extraction, confidence

  # subroutines
  #############

  def _all_field_filter(self, raw_extraction):
    filtered_extraction = {}
    for field_name,field_extraction in raw_extraction.items():
      if field_name in self._fields | self._aux_fields:
        filtered_extraction[field_name] = field_extraction
    return filtered_extraction

  def _states(self):
    states = [FieldExtractor._GARBAGE_FIELD]
    states.extend(self._fields)
    states.extend(self._aux_fields)
    for from_state, to_states in self._connections.iteritems():
      states.extend(['{}2{}'.format(from_state, to_state) for to_state in to_states])
    return states

  def _outputs(self):
    outputs = ['STOP'] # stop tokens
    outputs.extend(self._lexer.types.keys())
    return outputs

# TODO move utils into their own file?
# utils
#######

def find(x, pattern):
  i = 0
  while i <= len(x) - len(pattern):
    if x[i:i + len(pattern)] == pattern:
      return i
    i += 1
  return -1

def extraction2label(x_tokens, y_tokens, connections):
  labels = [None] * len(x_tokens)

  # label fields and aux fields
  for state,extraction in y_tokens.iteritems():
    i = find(x_tokens, extraction)
    labels[i : i + len(extraction)] = [state] * len(extraction)

  # compute start,stop indices for all potential connections
  links = _links(labels)

  # fill in links with corresponding connections
  for (from_state,to_state), (i,j) in links.iteritems():
    if to_state in connections.get(from_state, set()):
      labels[i:j] = ['{}2{}'.format(from_state, to_state)] * (j - i)
  return labels

# helper function for extraction2label
def _links(labels):
  '''Finds all sequences of None within @param labels that are wrapped by non-None values
    @param labels is a list of field names as strings
    @returns a dictionary mapping the 2 states surrounding a None-sequence to the indices for that None-sequence
  '''
  links = {}
  index = 0
  while index < len(labels):
    label = labels[index]
    if label is None and index != 0:
      none_index = index
      while none_index < len(labels):
        if labels[none_index] is not None:
          break
        none_index += 1
      if none_index >= len(labels):
        break
      from_state = labels[index - 1]
      to_state = labels[none_index]
      links[(from_state, to_state)] = (index, none_index)
      index = none_index
    else:
      index += 1
  return links

# chunk
#######

def group_fields(z, x):
  fields = {}
  field = [x[0]]
  for t in range(1,len(x)):
    field_id = z[t - 1]
    if z[t] == field_id:
      field.append(x[t])
    else:
      fields.setdefault(field_id, []).append(Lexer.detokenize(field))
      field = [x[t]]
  # ignore dangling field as it always corresponds to STOP
  #fields.setdefault(z[-1], []).append(Lexer.detokenize(field))
  return fields
