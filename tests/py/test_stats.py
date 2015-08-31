from __future__ import print_function, unicode_literals

import datetime
from decimal import Decimal
import json

import pytest

from gratipay.testing import Harness


class DateTime(datetime.datetime): pass
datetime.datetime = DateTime


class TestCommaize(Harness):
    # XXX This really ought to be in helper methods test file
    def setUp(self):
        Harness.setUp(self)
        simplate = self.client.load_resource(b'/about/stats.html')
        self.commaize = simplate.pages[0]['commaize']

    def test_commaize_commaizes(self):
        actual = self.commaize(1000.0)
        assert actual == "1,000"

    def test_commaize_commaizes_and_obeys_decimal_places(self):
        actual = self.commaize(1000, 4)
        assert actual == "1,000.0000"


class TestChartOfReceiving(Harness):
    def setUp(self):
        Harness.setUp(self)
        for participant in ['alice', 'bob']:
            p = self.make_participant(participant, claimed_time='now', last_bill_result='')
            setattr(self, participant, p)

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_handles_a_tip(self):
        self.alice.set_tip_to(self.bob, '3.00')
        expected = ([[Decimal('3.00'), 1, Decimal('3.00'), 1.0, Decimal('1')]],
                    1.0, Decimal('3.00'))
        actual = self.bob.get_tip_distribution()
        assert actual == expected

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_handles_no_tips(self):
        expected = ([], 0.0, Decimal('0.00'))
        actual = self.alice.get_tip_distribution()
        assert actual == expected

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_handles_multiple_tips(self):
        carl = self.make_participant('carl', claimed_time='now', last_bill_result='')
        self.alice.set_tip_to(self.bob, '1.00')
        carl.set_tip_to(self.bob, '3.00')
        expected = ([
            [Decimal('1.00'), 1L, Decimal('1.00'), 0.5, Decimal('0.25')],
            [Decimal('3.00'), 1L, Decimal('3.00'), 0.5, Decimal('0.75')]
        ], 2.0, Decimal('4.00'))
        actual = self.bob.get_tip_distribution()
        assert actual == expected

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_handles_big_tips(self):
        self.bob.update_number('plural')
        carl = self.make_participant('carl', claimed_time='now', last_bill_result='')
        self.alice.set_tip_to(self.bob, '200.00')
        carl.set_tip_to(self.bob, '300.00')
        expected = ([
            [Decimal('200.00'), 1L, Decimal('200.00'), 0.5, Decimal('0.4')],
            [Decimal('300.00'), 1L, Decimal('300.00'), 0.5, Decimal('0.6')]
        ], 2.0, Decimal('500.00'))
        actual = self.bob.get_tip_distribution()
        assert actual == expected

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_ignores_bad_cc(self):
        bad_cc = self.make_participant('bad_cc', claimed_time='now', last_bill_result='Failure!')
        self.alice.set_tip_to(self.bob, '1.00')
        bad_cc.set_tip_to(self.bob, '3.00')
        expected = ([[Decimal('1.00'), 1L, Decimal('1.00'), 1, Decimal('1')]],
                    1.0, Decimal('1.00'))
        actual = self.bob.get_tip_distribution()
        assert actual == expected

    @pytest.mark.xfail(reason="#3399")
    def test_get_tip_distribution_ignores_missing_cc(self):
        missing_cc = self.make_participant('missing_cc', claimed_time='now')
        self.alice.set_tip_to(self.bob, '1.00')
        missing_cc.set_tip_to(self.bob, '3.00')
        expected = ([[Decimal('1.00'), 1L, Decimal('1.00'), 1, Decimal('1')]],
                    1.0, Decimal('1.00'))
        actual = self.bob.get_tip_distribution()
        assert actual == expected

class TestJson(Harness):

    def test_200(self):
        response = self.client.GET('/about/stats.json')
        assert response.code == 200
        body = json.loads(response.body)
        assert len(body) > 0
