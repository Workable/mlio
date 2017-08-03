
class GenericObject(object):

    def __init__(self, a):
        self.data = {
            i: i ** 2
            for i in range(0, a)
        }
