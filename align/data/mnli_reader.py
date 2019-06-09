from typing import Dict
import json
import logging

from overrides import overrides

from allennlp.common.file_utils import cached_path
from allennlp.data.dataset_readers.dataset_reader import DatasetReader
from allennlp.data.fields import Field, TextField, LabelField, MetadataField
from allennlp.data.instance import Instance
from allennlp.data.token_indexers import SingleIdTokenIndexer, TokenIndexer
from allennlp.data.tokenizers import Tokenizer, WordTokenizer
from allennlp.data import Token

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

# TODO: unify with XNLI; just hardcore "en" as language tag

@DatasetReader.register("mnli")
class MnliReader(DatasetReader):
    """
    Reads a file from the Multi Natural Language Inference (MNLI) dataset.  This data is
    formatted as jsonl, one json-formatted instance per line.  The keys in the data are
    "gold_label", "sentence1", and "sentence2".  We convert these keys into fields named "label",
    "premise" and "hypothesis", along with a metadata field containing the tokenized strings of the
    premise and hypothesis.

    Parameters
    ----------
    tokenizer : ``Tokenizer``, optional (default=``WordTokenizer()``)
        We use this ``Tokenizer`` for both the premise and the hypothesis.  See :class:`Tokenizer`.
    token_indexers : ``Dict[str, TokenIndexer]``, optional (default=``{"tokens": SingleIdTokenIndexer()}``)
        We similarly use this for both the premise and the hypothesis.  See :class:`TokenIndexer`.
    max_sent_len : ``int``
        Examples where premis or hypothesis are larger then this will be filtered out
    """

    def __init__(self,
                 tokenizer: Tokenizer = None,
                 token_indexers: Dict[str, TokenIndexer] = None,
                 is_bert_pair: bool = False,  
                 max_sent_len: int = None,
                 lazy: bool = False) -> None:
        super().__init__(lazy)
        self._tokenizer = tokenizer or WordTokenizer()
        self._token_indexers = token_indexers or {'tokens': SingleIdTokenIndexer()}
        self._max_sent_len = max_sent_len
        self._is_bert_pair = is_bert_pair 

    @overrides
    def _read(self, file_path: str):
        # if `file_path` is a URL, redirect to the cache
        file_path = cached_path(file_path)

        with open(file_path, 'r') as snli_file:
            logger.info("Reading MultiNLI instances from jsonl dataset at: %s", file_path)
            for line in snli_file:
                example = json.loads(line)

                label = example["gold_label"]
                if label == '-':
                    # These were cases where the annotators disagreed; we'll just skip them.  It's
                    # like 800 out of 400k examples in the training data.
                    continue

                premise = example["sentence1"]
                hypothesis = example["sentence2"]

                # filter out very long sentences
                if self._max_sent_len is not None:
                    # These were sentences are too long for bert; we'll just skip them.  It's
                    # like 1000 out of 400k examples in the training data.
                    if len(premise.split(" ")) > self._max_sent_len or len(hypothesis.split(" ")) > self._max_sent_len:
                        continue

                yield self.sentence_pair_to_bert_instance(premise, hypothesis, label)

    def sentence_pair_to_bert_instance(self,  # type: ignore
                         premise: str,
                         hypothesis: str,
                         label: str = None) -> Instance:
        # pylint: disable=arguments-differ
        if self._is_bert_pair:
            return self.text_to_instance_bert(premise, hypothesis, label)
        
        fields: Dict[str, Field] = {}
        premise_tokens = self._tokenizer.tokenize(premise)
        hypothesis_tokens = self._tokenizer.tokenize(hypothesis)
        fields['premise'] = TextField(premise_tokens, self._token_indexers)
        fields['hypothesis'] = TextField(hypothesis_tokens, self._token_indexers)
        if label:
            fields['label'] = LabelField(label)

        metadata = {"premise_tokens": [x.text for x in premise_tokens],
                    "hypothesis_tokens": [x.text for x in hypothesis_tokens]}
        fields["metadata"] = MetadataField(metadata)
        return Instance(fields)

    def text_to_instance_bert(self, 
                                   premise: str, 
                                   hypothesis: str, 
                                   label: str = None) -> Instance:
        fields: Dict[str, Field] = {}

        premise_tokens = self._tokenizer.tokenize(premise)
        hypothesis_tokens = self._tokenizer.tokenize(hypothesis)

        premise_hypothesis_tokens = premise_tokens
        premise_hypothesis_tokens.append(Token("[SEP]"))
        premise_hypothesis_tokens.extend(hypothesis_tokens)

        fields['premise_hypothesis'] = TextField(premise_hypothesis_tokens, self._token_indexers)

        if label:
            fields['label'] = LabelField(label)

        metadata = {"premise_tokens": [x.text for x in premise_tokens],
                    "hypothesis_tokens": [x.text for x in hypothesis_tokens]}
        fields["metadata"] = MetadataField(metadata)
        return Instance(fields)