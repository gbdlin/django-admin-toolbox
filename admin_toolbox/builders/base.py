class BaseBuilder(object):

    def __init__(self):
        super(BaseBuilder, self).__init__()

    def build(self, request=None, context=None, menu_name='default'):
        return {}
