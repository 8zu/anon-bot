import json
import os
import os.path as osp


class Option(object):
    def __init__(self, val=None):
        self.val = val

    def is_none(self):
        return self.val is None

    def get(self):
        ret = self.get_or(None)
        if ret is None:
            raise ValueError("unwrapping a None")
        return ret

    def get_or(self, default):
        if self.val:
            return self.val
        else:
            return default


class Cache(object):
    def __init__(self, cache_root):
        self.cache_root = cache_root
        if not osp.exists(cache_root):
            os.mkdir(cache_root)

    def save(self, key, obj):
        path = osp.join(self.cache_root, key)
        with open(path, "w", encoding="UTF-8") as cache:
            json.dump(obj, cache)

    def load(self, key) -> Option:
        path = osp.join(self.cache_root, key)
        if not osp.exists(path):
            return Option(None)
        with open(path, "r", encoding="UTF-8") as cache:
            return Option(json.load(cache))
