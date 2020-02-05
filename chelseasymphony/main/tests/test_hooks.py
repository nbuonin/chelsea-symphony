"""Tests the PayPal donation form implementation"""
import random
import string
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from paypal.standard.ipn.tests.test_ipn import MockedPostbackMixin
from six import text_type
from six.moves.urllib.parse import urlencode
from chelseasymphony.main.wagtail_hooks import (
    get_adjusted_donation
)


CHARSET = "windows-1252"


@override_settings(PAYPAL_ACCT_EMAIL='email-facilitator@gmail.com')
class DonationEmailTest(MockedPostbackMixin, TestCase):
    """Tests the donation form"""
    def paypal_post(self, params):
        """
        Does an HTTP POST the way that PayPal does, using the params given.
        """
        # Taken from paypal.standard.ipn.tests.test_ipn, POST path modified
        # We build params into a bytestring ourselves, to avoid some encoding
        # processing that is done by the test client.
        def cond_encode(param):
            return param.encode(CHARSET) \
                if isinstance(param, text_type) else param

        byte_params = {
            cond_encode(k): cond_encode(v) for k, v in params.items()}
        post_data = urlencode(byte_params)
        return self.client.post(
            "/paypal/",
            post_data,
            content_type='application/x-www-form-urlencoded'
        )

    @staticmethod
    def generate_params(amount, waive_donor_incentive=False):
        """
        Creates a dict of test params for test requests
        """
        amt = '{}'.format(amount).encode(encoding='UTF-8')
        custom = b'waive-donor-incentive=yes' if waive_donor_incentive \
            else b'waive-donor-incentive=no'

        # Transactions with the same ID won't be processed
        txn_id = ''.join(
            [random.choice(string.ascii_uppercase + string.digits) for i
             in range(17)]).encode(encoding='UTF-8')

        return {
            'btn_id1': b"3453595",
            'business': b"email-facilitator@gmail.com",
            'charset': b"windows-1252",
            'custom': custom,
            "first_name": b"Gustav",
            'ipn_track_id': b"a48170aadb705",
            'item_name1': b"Single donation for The Chelsea Symphony",
            'item_number1': b"",
            'last_name': b"Maher",
            'mc_currency': b"USD",
            'mc_fee': b"0.35",
            'mc_gross': amt,
            'mc_gross_1': b"3.00",
            'mc_handling': b"0.00",
            'mc_handling1': b"0.00",
            'mc_shipping': b"0.00",
            'mc_shipping1': b"0.00",
            'notify_version': b"3.8",
            'num_cart_items': b"1",
            'payer_email': b"email@gmail.com",
            'payer_id': b"6EQ6SKDFMPU36",
            'payer_status': b"verified",
            'payment_date': b"03:06:57 Jun 27, 2014 PDT",
            'payment_fee': b"",
            'payment_gross': b"",
            'payment_status': b"Completed",
            'payment_type': b"instant",
            'protection_eligibility': b"Ineligible",
            'quantity1': b"3",
            'receiver_email': b"email-facilitator@gmail.com",
            'receiver_id': b"UCWM6R2TARF36",
            'residence_country': b"US",
            'tax': b"0.00",
            'tax1': b"0.00",
            'test_ipn': b"0",
            'transaction_subject': b"blahblah",
            'txn_id': txn_id,
            'txn_type': b"web_accept",
            'verify_sign': b"A_SECRET_CODE"}

    def test_calculate_donation(self):
        """ Step through all the breakpoints and check that the
        donation is adjusted the expected amount"""
        # $1 - $50
        self.assertEqual(get_adjusted_donation('1.00'), '1.00')
        self.assertEqual(get_adjusted_donation('50.00'), '50.00')
        # $50 - $100
        self.assertEqual(get_adjusted_donation('50.01'), '50.01')
        self.assertEqual(get_adjusted_donation('99.99'), '99.99')
        # $100 - $250
        self.assertEqual(get_adjusted_donation('100.00'), '50.00')
        self.assertEqual(get_adjusted_donation('100.01'), '50.01')
        self.assertEqual(get_adjusted_donation('249.99'), '199.99')
        # $250 - $500
        self.assertEqual(get_adjusted_donation('250.00'), '200.00')
        self.assertEqual(get_adjusted_donation('250.01'), '200.01')
        self.assertEqual(get_adjusted_donation('499.99'), '449.99')
        # $500 - $1000
        self.assertEqual(get_adjusted_donation('500.00'), '400.00')
        self.assertEqual(get_adjusted_donation('500.01'), '400.01')
        self.assertEqual(get_adjusted_donation('999.99'), '899.99')
        # $1000 - $5000
        self.assertEqual(get_adjusted_donation('1000.00'), '900.00')
        self.assertEqual(get_adjusted_donation('1000.01'), '900.01')
        self.assertEqual(get_adjusted_donation('4999.99'), '4899.99')
        # $5000 - $30000: $700
        self.assertEqual(get_adjusted_donation('5000.00'), '4300.00')
        self.assertEqual(get_adjusted_donation('5000.01'), '4300.01')
        self.assertEqual(get_adjusted_donation('29999.99'), '29299.99')
        # $30000+
        self.assertEqual(get_adjusted_donation('30000.00'), '28600.00')
        self.assertEqual(get_adjusted_donation('30000.01'), '28600.01')

    def test_donation_email(self):
        """
        Tests that a single donation triggers an email to be sent
        """
        params = self.generate_params('3.00')
        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            'Thank you for your donation', mail.outbox[0].subject)
        self.assertIn(
            'Hi Gustav!', mail.outbox[0].body)
        self.assertIn(
            '$3.00 contribution', mail.outbox[0].body)

    def test_single_donation(self):
        """
        Tests single donations where the donor has elected to keep thier
        donar benefit. In otherwords, the donation amount needs to be adjusted
        down.
        """
        # Test donation < $100, there should be no adjustment
        self.paypal_post(self.generate_params('99.99'))
        self.assertIn(
            'You have indicated that you would like your donor incentive',
            mail.outbox[-1].body
        )
        # The line that includes the adjusted donation reads '... was $xx.xx'
        self.assertIn('was $99.99', mail.outbox[-1].body)

        # Test donations $100 ~ $499.99, it should be adjusted down $50
        self.paypal_post(self.generate_params('100.00'))
        self.assertIn('was $50.00', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('100.01'))
        self.assertIn('was $50.01', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('499.99'))
        self.assertIn('was $449.99', mail.outbox[-1].body)

        # Test donations $500 ~ $4999.99, should be adjusted down $100
        self.paypal_post(self.generate_params('500.00'))
        self.assertIn('was $400.00', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('500.01'))
        self.assertIn('was $400.01', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('4999.99'))
        self.assertIn('was $4899.99', mail.outbox[-1].body)

        # Test donations $5000 ~ $29,999.99, should be adjusted down $700
        self.paypal_post(self.generate_params('5000.00'))
        self.assertIn('was $4300.00', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('5000.01'))
        self.assertIn('was $4300.01', mail.outbox[-1].body)

        self.paypal_post(self.generate_params('29999.99'))
        self.assertIn('was $29299.99', mail.outbox[-1].body)

        # Test donations > $30K, should be adjusted down $1400
        self.paypal_post(self.generate_params('30000.00'))
        self.assertIn('was $28600.00', mail.outbox[-1].body)

        # Just in case a billionaire falls in love
        self.paypal_post(self.generate_params('1000000000.00'))
        self.assertIn('was $999998600.00', mail.outbox[-1].body)

    def test_single_donation_waived(self):
        """
        Test that a donation is not adjusted when the donor chooses
        to waive thier donor benefit.
        """
        amts = ['1.00', '100.00', '500.00', '5000.00', '30000.00']
        for amt in amts:
            self.paypal_post(
                self.generate_params(amt, waive_donor_incentive=True))
            msg = mail.outbox[-1]
            self.assertIn('was ${}'.format(amt), msg.body)

    def test_recurring_donation_signup(self):
        """
        Test that the initial recurring donation welcome email is sent
        """
        params = self.generate_params(amount='100.00')
        params['txn_type'] = b'subscr_signup'
        params['item_name'] = b'Recurring donation for The Chelsea Symphony'
        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            'Thank you for your recurring donation', mail.outbox[0].subject)
        self.assertIn(
            'thank you for your recurring $100.00 contribution',
            mail.outbox[0].body)

    def test_recurring_donation_payment(self):
        """
        Recurring donations are processed by PayPal every month. This tests
        that the correct email is sent with each monthyly donation.
        """
        params = self.generate_params(amount='100.00')
        params['txn_type'] = b'subscr_payment'
        params['item_name'] = b'Recurring donation for The Chelsea Symphony'
        response = self.paypal_post(params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            'Thank you for your donation', mail.outbox[0].subject)
        self.assertIn(
            'For your records: Your recurring donation', mail.outbox[0].body)
        self.assertIn('was $100.00', mail.outbox[0].body)
