from django.test import TestCase

from apps.core.utils import compose


class UtilsTest(TestCase):
    def test_compose(self):
        def f(x):
            return x + 1

        def g(x):
            return x * 50

        self.assertEqual(compose(f, g)(2), 101)
        self.assertEqual(compose(f, g, f)(2), 151)
        self.assertEqual(compose(f, g, f, g)(2), 5051)
