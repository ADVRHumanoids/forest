import os
from pathlib import Path
import subprocess
import sys
import textwrap
import time
import unittest

import psutil


def wait_for_parent(parent_pid, pwd):
    """Exercise a real child process without invoking sudo."""
    while psutil.pid_exists(parent_pid):
        time.sleep(0.05)


class SudoRefreshShutdownTests(unittest.TestCase):
    def test_cli_stops_refresher_on_every_exit_path(self):
        # A subprocess timeout detects interpreter-shutdown deadlocks that an
        # in-process mock of Process.join() would miss. Keep a reference to the
        # refresher so cleanup cannot accidentally depend on its destructor.
        script = textwrap.dedent('''\
            import sys
            import tempfile
            from unittest.mock import patch
            from forest import main
            from forest.common.sudo_refresh import SudoRefresher
            from test_sudo_refresh import wait_for_parent

            outcome = sys.argv[1]
            refreshers = []

            class RecordingRefresher(SudoRefresher):
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    refreshers.append(self)

            def install(**kwargs):
                if outcome == 'exception':
                    raise TypeError('dependency regression')
                if outcome == 'interrupt':
                    raise KeyboardInterrupt()
                return outcome == 'success'

            with tempfile.TemporaryDirectory() as workspace, \\
                 patch.object(main, '_forest_dirs') as dirs, \\
                 patch.object(main.Cookbook, 'get_available_recipes', return_value=['example']), \\
                 patch.object(main.Cookbook, 'set_recipe_basedir'), \\
                 patch.object(main, 'check_ws_file', return_value=True), \\
                 patch.object(main, 'write_setup_file'), \\
                 patch.object(main, 'install_package', side_effect=install), \\
                 patch.object(SudoRefresher, '_do_sudo'), \\
                 patch.object(SudoRefresher, '_do_sudo_refresh', wait_for_parent), \\
                 patch.object(main.sudo_refresh, 'SudoRefresher', RecordingRefresher), \\
                 patch.object(sys, 'argv', ['forest', 'grow', 'example', '--pwd', 'test', '--verbose']):
                dirs.rootdir = dirs.buildroot = dirs.installdir = workspace
                dirs.srcroot = dirs.recipesdir = workspace
                try:
                    main.main()
                finally:
                    assert len(refreshers) == 1
                    refresher = refreshers[0]
                    assert refresher.proc.daemon
                    assert not refresher.proc.is_alive(), 'refresher leaked'
                    assert refresher.proc.exitcode is not None
                    refresher.close()
                    refresher.close()
                    print('refresher stopped', flush=True)
            ''')
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join(
            [str(root / 'src'), str(root / 'test'), env.get('PYTHONPATH', '')])
        for outcome in ('success', 'failure', 'exception', 'interrupt'):
            with self.subTest(outcome=outcome):
                result = subprocess.run(
                    [sys.executable, '-c', script, outcome], env=env,
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0 if outcome == 'success' else 1,
                                 result.stdout + result.stderr)
                self.assertIn('refresher stopped', result.stdout)
                self.assertNotIn('Exception ignored in:', result.stderr)
                if outcome == 'exception':
                    self.assertIn('TypeError: dependency regression', result.stderr)


if __name__ == '__main__':
    unittest.main()
