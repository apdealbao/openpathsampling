from openpathsampling.netcdfplus import StorableNamedObject


class BiasFunction(StorableNamedObject):
    """Generic bias functions. Everything inherits from here. Abstract."""
    def probability_old_to_new(self, sampleset, change):
        raise NotImplementedError

    def probability_new_to_old(self, sampleset, change):
        raise NotImplementedError

    def probability_ratio_new_old(self, sampleset, change):
        old2new = self.probability_old_to_new(sampleset, change)
        new2old = self.probability_new_to_old(sampleset, change)
        return old2new / new2old

    def get_new_old(self, sampleset, change):
        """Associates changed and original samples.

        Returns tuple (replica, new_sample, old_sample)
        """
        # TODO: this should move to sample.py (or pmc.py?) as a free function
        return [(s.replica, s, sampleset[s.replica]) for s in change.samples]


class BiasLookupFunction(BiasFunction):
    """Abstract class for lookup function based bias functions.
    """
    def __init__(self, bias_lookup, sample_reducer):
        super(BiasLookupFunction, self).__init__()
        self.bias_lookup = bias_lookup
        self.sample_reducer = sample_reducer


class BiasEnsembleTable(BiasFunction):
    def __init__(self, bias_table):
        super(BiasEnsembleTable, self).__init__()
        self.bias_table = bias_table

    def probability_old_to_new(self, sampleset, change):
        new_old = self.get_new_old(sampleset, change)
        prob = 1.0
        for diff in new_old:
            new = diff[1]
            old = diff[2]
            new_w = self.bias_table[new.ensemble]
            old_w = self.bias_table[old.ensemble]
            prob *= min(1.0, new_w/old_w) # TODO check direction
        return prob

    def probability_new_to_old(self, sampleset, change):
        new_old = self.get_new_old(sampleset, change)
        prob = 1.0
        for diff in new_old:
            new = diff[1]
            old = diff[2]
            new_w = self.bias_table[new.ensemble]
            old_w = self.bias_table[old.ensemble]
            prob *= min(1.0, old_w/new_w) # TODO check direction
        return prob

