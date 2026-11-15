"""Explicit opt-in: two real emails, synthetic local accounts, real browser links.

Never run against a production database. Credentials are read from the process
environment only; do not enable traces, screenshots or response-body logging.
"""

import os
import time
import unittest
from urllib.parse import urlsplit

import test_advanced_real_api as advanced


@unittest.skipUnless(os.environ.get('RUN_RESEND_E2E') == '1',
                     'Real mail disabled; explicitly authorize two test emails')
class ResendRealApiTests(advanced.AdvancedRealApiTests):
    test_metadata_custom_role_guided_item_board_and_history = None

    def additional_auth_settings(self):
        for key in ('RESEND_API_KEY', 'RESEND_FROM', 'RESEND_TEST_TO'):
            self.assertTrue(os.environ.get(key), 'Missing private real-mail configuration')
        return dict(super().additional_auth_settings(), MAIL_PROVIDER='resend',
                    LOCAL_MAILBOX_ENABLED='false')

    def security_email(self):
        return os.environ['RESEND_TEST_TO']

    def provider_get(self, path):
        # Provider credentials belong only to this isolated APIRequestContext.
        # Never assert response bodies or URLs containing links/credentials.
        time.sleep(0.6)
        response = self.provider.get('https://api.resend.com' + path, timeout=15000)
        self.assertEqual(response.status, 200, 'Resend readback unavailable')
        return response.json()

    def mail_link(self, headers, fragment):
        del headers
        subject = 'Verify email' if fragment == 'verify-email' else 'Set your password'
        prefix = self.base_url + '/#' + fragment + '='
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            entries = self.provider_get('/emails?limit=20')['data']
            matching = [entry for entry in entries if entry.get('subject') == subject
                        and self.security_email().lower() in
                        [address.lower() for address in entry.get('to', [])]]
            for entry in matching[:5]:
                mail = self.provider_get('/emails/' + entry['id'])
                link = (mail.get('text') or '').strip()
                if not link.startswith(prefix):
                    continue
                self.assertEqual(urlsplit(link).netloc, urlsplit(self.base_url).netloc,
                                 'Email must target this isolated frontend')
                event = mail.get('last_event')
                self.assertNotIn(event, ('bounced', 'failed', 'suppressed', 'canceled'),
                                 'Provider reported a delivery failure')
                if event not in ('delivered', 'opened', 'clicked'):
                    break
                self.mail_events.append(event)
                return link
            time.sleep(1)
        self.fail('Provider did not confirm delivery of this run; no automatic resend')

    def test_mfa_recovery_email_confirmation_and_reset_preserve_second_factor(self):
        self.provider = self.playwright.request.new_context(extra_http_headers={
            'Authorization': 'Bearer ' + os.environ['RESEND_API_KEY']})
        self.addCleanup(self.provider.dispose)
        self.mail_events = []
        # Read permission is checked before any external send.
        self.assertIsInstance(self.provider_get('/emails?limit=1').get('data'), list)
        super().test_mfa_recovery_email_confirmation_and_reset_preserve_second_factor()
        self.assertEqual(len(self.mail_events), 2)
        self.assertTrue(all(event in ('delivered', 'opened', 'clicked')
                            for event in self.mail_events))


if __name__ == '__main__':
    unittest.main()
