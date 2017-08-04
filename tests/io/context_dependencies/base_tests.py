import unittest

from ml_utils.io.context_dependencies.base import ContextDependencyBase


class ExampleCtxDep(ContextDependencyBase):

    @classmethod
    def dependency_type(cls):
        return 'example-ctx'


class CtxDepBaseTestCase(unittest.TestCase):

    def test_empty_ctor(self):

        ctx_dep = ContextDependencyBase()
        self.assertDictEqual(ctx_dep.get_params(), {})

        with self.assertRaises(AttributeError):
            print(ctx_dep.unknown)

    def test_ctor_params(self):

        ctx_dep = ContextDependencyBase(parameter=1, hik="hok")
        self.assertDictEqual(ctx_dep.get_params(), {
            "parameter": 1,
            "hik": "hok"
        })

        self.assertEqual(ctx_dep.parameter, 1)
        self.assertEqual(ctx_dep.hik, "hok")

    def test_to_dict(self):

        # Empty context
        ctx_dep = ExampleCtxDep()
        self.assertDictEqual(ctx_dep.to_dict(), {
            'type': 'example-ctx'
        })

        # Context with parameters
        ctx_dep = ExampleCtxDep(something="foo", bar=1)
        self.assertDictEqual(ctx_dep.to_dict(), {
            'type': 'example-ctx',
            'something': 'foo',
            'bar': 1
        })

    def test_from_dict(self):

        # Dict without type
        with self.assertRaises(ValueError):
            ExampleCtxDep.from_dict({})

        # Empty dict without type
        dep_data_empty = {
            'type': 'example-ctx'
        }
        ctx_dep = ExampleCtxDep.from_dict(dep_data_empty)
        self.assertEqual(ctx_dep.get_params(), {})

        # Dict with parameters
        dep_data = {
            'type': 'example-ctx',
            'another': 'value',
            'foo': 1.0,
            'bar': 4
        }
        ctx_dep = ExampleCtxDep.from_dict(dep_data)
        self.assertEqual(ctx_dep.get_params(), {
            'another': 'value',
            'foo': 1.0,
            'bar': 4
        })


if __name__ == '__main__':
    unittest.main()
