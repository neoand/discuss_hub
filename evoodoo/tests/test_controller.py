from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("standard", "at_install")
class TestSomething(TransactionCase):
    def test_basic(self):
        self.assertEqual(1 + 1, 2)
