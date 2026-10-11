import os
import tempfile
import threading
import unittest
from pathlib import Path

import test_real_api as real_api


class RealApiCleanupTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows file-handle release regression')
    def test_temporary_database_cleanup_waits_for_handle_release(self):
        fixture = real_api.RealApiTests('test_real_login_identity_update_and_logout')
        fixture.temp = tempfile.TemporaryDirectory(prefix='mod1-cleanup-regression-')
        root = Path(fixture.temp.name)
        database = root / 'users.db'
        database.write_bytes(b'synthetic database')
        handle = database.open('rb')
        # Reproduce the OS delay after the owned interpreter has stopped.
        release = threading.Timer(0.2, handle.close)
        release.start()
        try:
            fixture.cleanup_temp()
            self.assertFalse(root.exists())
        finally:
            release.cancel()
            release.join()
            handle.close()
            fixture.temp.cleanup()
