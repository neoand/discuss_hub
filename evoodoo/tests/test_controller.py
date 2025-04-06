from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('standard', 'at_install')
class TestSomething(TransactionCase):
    def test_basic(self):
        self.assertEqual(1 + 1, 2)