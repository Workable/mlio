
class GenericObject(object):

    def __init__(self, a):
        self.data = {
            i: i ** 2
            for i in range(0, a)
        }


class ObjectFixturesMixIn(object):
    def setUp(self):
        self.obj2k = GenericObject(2000)
        self.obj1k = GenericObject(1000)

        with self.assertRaises(AssertionError):
            # Meta-unit-test that objects are actually different
            self.assertDictEqual(self.obj1k.data, self.obj2k.data)

    def assertEqualObj1k(self, recovered_obj):
        self.assertDictEqual(self.obj1k.data, recovered_obj.data)
        self.assertIsNot(self.obj1k, recovered_obj)

    def assertEqualObj2k(self, recovered_obj):
        self.assertDictEqual(self.obj2k.data, recovered_obj.data)
        self.assertIsNot(self.obj2k, recovered_obj)
