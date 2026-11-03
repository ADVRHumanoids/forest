import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from forest.common.dependency import Dependency
from forest.common.package import Package
from forest.common import install
from forest.cmake_tools import CmakeTools
from forest.cmake_tools import _impl


class DependencyTests(unittest.TestCase):
    def test_plain_and_versioned_conditional_dependencies(self):
        recipe = {'depends': ['plain'], 'depends_if': {'enabled': [
            {'name': 'versioned', 'version': '1.2', 'exact': True}]}}
        evaluator = Mock()
        evaluator.parse_conditional_dict.return_value = recipe['depends_if']['enabled']
        with patch('forest.common.package.EvalHandler.instance', return_value=evaluator):
            for _ in range(2):
                pkg = Package.from_yaml('parent', recipe)
                self.assertEqual([str(dep) for dep in pkg.depends],
                                 ['plain', 'versioned 1.2 EXACT'])
        self.assertEqual(recipe['depends'], ['plain'])

    def test_invalid_requirements(self):
        for entry in [None, {}, {'name': 'pkg', 'version': 1.2},
                      {'name': 'pkg', 'version': '>=1.2'},
                      {'name': 'pkg', 'version': '1.2.3.4.5'},
                      {'name': 'pkg', 'exact': True},
                      {'name': 'pkg', 'exact': 'false'},
                      {'name': 'pkg', 'verison': '1.2'}, 'pkg)\nmessage(FATAL_ERROR bad)']:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                Dependency.from_yaml(entry)


class CmakeProbeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        log_patch = patch('forest.common.print_utils.log_file', new_callable=io.StringIO)
        log_patch.start()
        self.addCleanup(log_patch.stop)
        self.prefix = Path(self.tempdir.name)
        self.saved_args = _impl.default_args
        CmakeTools.set_default_args([])
        self.addCleanup(CmakeTools.set_default_args, self.saved_args)
        (self.prefix / 'ForestVersionFixtureConfig.cmake').write_text('')
        script = self.prefix / 'version.cmake'
        script.write_text('include(CMakePackageConfigHelpers)\n'
                          'write_basic_package_version_file("{}" VERSION 2.4.1 '
                          'COMPATIBILITY SameMajorVersion)\n'.format(
                              (self.prefix / 'ForestVersionFixtureConfigVersion.cmake').as_posix()))
        subprocess.run(['cmake', '-P', str(script)], check=True, capture_output=True)

    def probe(self, version=None, exact=False):
        return CmakeTools.find_package('ForestVersionFixture', version, exact,
                                       prefix_path=str(self.prefix))

    def test_real_cmake_version_selection(self):
        for version, exact, expected in [(None, False, True), ('2.3', False, True),
                                         ('2.5', False, False), ('1.0', False, False),
                                         ('2.4.1', True, True), ('2.4.0', True, False)]:
            with self.subTest(version=version, exact=exact):
                self.assertEqual(self.probe(version, exact), expected)

    def test_missing_version_metadata(self):
        (self.prefix / 'ForestVersionFixtureConfigVersion.cmake').unlink()
        self.assertTrue(self.probe())
        self.assertFalse(self.probe('2.0'))

    def test_global_cmake_arguments_reach_probe(self):
        CmakeTools.set_default_args(['-DCMAKE_PREFIX_PATH=' + str(self.prefix)])
        self.assertTrue(CmakeTools.find_package('ForestVersionFixture', '2.0'))


class DependencyInstallTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = self.tempdir.name
        self.parent = Package('parent', [{'name': 'dep', 'version': '2.0'}])
        self.dep = Package('dep', [])
        for pkg in (self.parent, self.dep):
            pkg.fetcher = Mock()
            pkg.fetcher.fetch.return_value = True
        install._build_cache.clear()
        self.addCleanup(install._build_cache.clear)
        self.loader = patch.object(Package, 'from_name', side_effect=lambda name: {
            'parent': self.parent, 'dep': self.dep}[name])
        self.loader.start()
        self.addCleanup(self.loader.stop)
        self.builder_patch = patch.object(install, 'build_package', return_value=True)
        self.builder = self.builder_patch.start()
        self.addCleanup(self.builder_patch.stop)

    def grow(self, **kwargs):
        return install.install_package('parent', self.root, self.root, self.root,
                                       'Release', 1, **kwargs)

    def test_installed_compatible_dependency_skips_build(self):
        with patch.object(CmakeTools, 'find_package', return_value=True) as probe:
            self.assertTrue(self.grow())
        probe.assert_called_once_with('dep', version='2.0', exact=False, prefix_path=self.root)
        self.assertEqual([call.kwargs['pkg'].name for call in self.builder.call_args_list], ['parent'])

    def test_recheck_after_installation(self):
        with patch.object(CmakeTools, 'find_package', side_effect=[False, False]):
            self.assertFalse(self.grow())
        self.assertEqual([call.kwargs['pkg'].name for call in self.builder.call_args_list], ['dep'])

    def test_successful_installation(self):
        with patch.object(CmakeTools, 'find_package', side_effect=[False, True]):
            self.assertTrue(self.grow())
        self.assertEqual([call.kwargs['pkg'].name for call in self.builder.call_args_list], ['dep', 'parent'])

    def test_recheck_workspace_and_cached_dependency(self):
        os.mkdir(os.path.join(self.root, 'dep'))
        install._build_cache['dep'] = True
        with patch.object(CmakeTools, 'find_package', return_value=False) as probe:
            self.assertFalse(self.grow())
        probe.assert_called_once()
        self.builder.assert_not_called()

    def test_recheck_after_workspace_rebuild(self):
        os.mkdir(os.path.join(self.root, 'dep'))
        with patch.object(CmakeTools, 'find_package', return_value=False) as probe:
            self.assertFalse(self.grow())
        probe.assert_called_once()
        self.assertEqual([call.kwargs['pkg'].name for call in self.builder.call_args_list], ['dep'])

    def test_plain_dependency_keeps_existing_install_behavior(self):
        self.parent.depends = [Dependency('dep')]
        with patch.object(CmakeTools, 'find_package', return_value=False) as probe:
            self.assertTrue(self.grow())
        probe.assert_called_once_with('dep', version=None, exact=False, prefix_path=self.root)
        self.assertEqual([call.kwargs['pkg'].name for call in self.builder.call_args_list], ['dep', 'parent'])

    def test_no_deps_skips_probes(self):
        with patch.object(CmakeTools, 'find_package') as probe:
            self.assertTrue(self.grow(no_deps=True))
        probe.assert_not_called()

    def test_src_only_does_not_validate_after_fetch(self):
        with patch.object(CmakeTools, 'find_package', return_value=False) as probe:
            self.assertTrue(self.grow(src_only=True))
        probe.assert_called_once()
        self.dep.fetcher.fetch.assert_called_once()
        self.builder.assert_not_called()


if __name__ == '__main__':
    unittest.main()
