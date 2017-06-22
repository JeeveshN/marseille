import tempfile
import pickle

import pytest

import numpy as np
from numpy.testing import assert_array_equal

from sklearn.utils import check_random_state

from marseille.argdoc import _BaseArgumentationDoc
from marseille.argrnn import ArgumentLSTM


class ArgDocStub(_BaseArgumentationDoc):

    VOCAB = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
    eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
    esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
    cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
    est laborum.""".lower().split()

    TYPES = ["fact", "value", "policy"]

    def __init__(self, n_words=20, n_props=3, random_state=None):
        self.random_state = random_state

        rng = check_random_state(self.random_state)
        self._tokens = rng.choice(self.VOCAB, size=n_words)

        self.prop_offsets = rng.choice(np.arange(n_words), size=2 * n_props,
                                  replace=False)
        self.prop_offsets.sort()
        self.prop_offsets = self.prop_offsets.reshape(-1, 2)

        self._prop_features = [{'label_': lbl}
            for lbl in rng.choice(self.TYPES, size=n_props)]

        self._features = [
            {
                'src__prop_id_': src,
                'trg__prop_id_': trg,
                'label_': rng.uniform() > 0.5
            }
            for src in range(n_props)
            for trg in range(n_props)
            if src != trg]

        self._link_to_prop = None
        self._second_order = None

    def tokens(self, key=None, lower=True):

        # this works because we made self.prop_offsets index tokens
        # and not characters. Bit of a hack but OK
        if key == 'characterOffsetBegin':
            return range(len(self._tokens))

        elif key:
            print(key)
            exit()

        return self._tokens


rng = np.random.RandomState(0)
n_docs = 3
docs = [ArgDocStub(random_state=rng) for _ in range(n_docs)]
Y = [doc.label for doc in docs]


def test_learn_training_set():

    rnn = ArgumentLSTM()
    rnn.fit(docs, Y)
    Y_pred = rnn.predict(docs)

    for y_true, y_pred in zip(Y, Y_pred):
        assert_array_equal(y_true.nodes, y_pred.nodes)
        assert_array_equal(y_true.links, y_pred.links)


def test_serialize():
    rnn = ArgumentLSTM()
    rnn.fit(docs, Y)
    Y_pred = rnn.predict(docs)

    pickled_rnn = pickle.dumps(rnn)

    with tempfile.NamedTemporaryFile() as f:
        rnn.save(f.name)

        unpickled_rnn = pickle.loads(pickled_rnn)

        # classifier cannot predict until loading the parameters
        with pytest.raises(Exception):
            unpickled_rnn.predict(docs)

        unpickled_rnn.load(f.name)

    Y_pkl_pred = unpickled_rnn.predict(docs)

    for y_pred, y_pkl_pred in zip(Y_pred, Y_pkl_pred):
        assert_array_equal(y_pkl_pred.nodes, y_pred.nodes)
        assert_array_equal(y_pkl_pred.links, y_pred.links)



