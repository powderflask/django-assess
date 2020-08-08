from django.test import TestCase

from assessment.assess.templatetags import helper_tags

class LinkifyTests(TestCase) :
    def test_linkify(self):
        class Obj:
            def __str__(self):
                return 'Almighty Bob'
            def get_absolute_url(self):
                return 'path/to/almighty/bob/'
        o = Obj()
        link = helper_tags.linkify(o)
        self.assertTrue('<a ' in link)
        self.assertTrue('href' in link)
        self.assertTrue(o.get_absolute_url() in link)
        self.assertTrue(str(o) in link)
