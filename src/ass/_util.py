from collections import abc, OrderedDict


class CaseInsensitiveOrderedDict(abc.MutableMapping):
    """A case insensitive ordered dictionary that preserves the original casing."""

    def __init__(self, *args, **kwargs):
        self._dict = OrderedDict(*args, **kwargs)
        self._case_mapping = {key.lower(): key for key in self._dict}

        if len(self._case_mapping) != len(self._dict):
            raise ValueError("Duplicate keys provided for case insensitive dict")

    def __contains__(self, key):
        if key.lower() in self._case_mapping:
            return self._case_mapping[key.lower()] in self._dict
        else:
            return False

    def __getitem__(self, key):
        return self._dict[self._case_mapping[key.lower()]]

    def __setitem__(self, key, value):
        if key.lower() not in self._case_mapping:
            self._case_mapping[key.lower()] = key
        self._dict[self._case_mapping[key.lower()]] = value

    def __delitem__(self, key):
        del self._dict[self._case_mapping[key.lower()]]
        del self._case_mapping[key.lower()]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def __repr__(self):
        return repr(self._dict)

    def __str__(self):
        return str(self._dict)
