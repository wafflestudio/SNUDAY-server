from functools import reduce


def compose(*fs):
    def compose2(f, g):
        return lambda *a, **kw: f(g(*a, **kw))

    return reduce(compose2, fs, lambda x: x)
