from django.test import TestCase
from dubletten_tool.src.classes import TempRel


class TempRelTest(TestCase):

    def setup(self, *args, **kwargs):
        print("setup test")

    def test_temp_rel_setup_and_reset(self, *args, **kwargs):

        # assert that the newly imported class is not setup yet, i.e. has no _instances attr
        self.assertRaises(AttributeError, getattr, TempRel, "_instances")
        TempRel.setup()
        self.assertEquals(TempRel._instances, [])
