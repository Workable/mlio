import unittest
import packaging.version
import packaging.specifiers
import mock

from ml_utils.io.context_dependencies.module_version import (
    ModuleVersionContextDependency, get_installed_module_version)


class InstalledModuleVersionTestCase(unittest.TestCase):

    def test_unknown_module(self):

        with self.assertRaises(ImportError):
            get_installed_module_version('unknown_big_package_wrong_name_for_sure_')

    def test_known_module(self):

        joblib_version = get_installed_module_version('joblib')
        self.assertIsInstance(joblib_version, packaging.version.Version)
        self.assertTrue(joblib_version in packaging.specifiers.SpecifierSet('~=0.11'))
        self.assertFalse(joblib_version in packaging.specifiers.SpecifierSet('~=0.21'))


class ModuleVersionTestCase(unittest.TestCase):

    def test_ctor_empty_parameters(self):

        with self.assertRaises(ValueError):
            ModuleVersionContextDependency('', '')

    def test_ctor_empty_version(self):

        ctx_dep = ModuleVersionContextDependency(
            module_name='themodule', version_specs='')

        self.assertEqual(ctx_dep.get_params(), {
            "module_name": "themodule",
            "version_specs": ""
        })
        self.assertIsInstance(ctx_dep.version_specs, packaging.specifiers.SpecifierSet)
        self.assertEqual(str(ctx_dep.version_specs), '')

        # Check version compatibility with every version
        self.assertTrue(packaging.version.Version('0.0.0') in ctx_dep.version_specs)

    def test_ctor_invalid_version(self):

        with self.assertRaises(packaging.specifiers.InvalidSpecifier):
            ModuleVersionContextDependency("a module", "1.0.0")

        with self.assertRaises(packaging.specifiers.InvalidSpecifier):
            ModuleVersionContextDependency("a module", "wrong")

    @mock. patch("ml_utils.io.context_dependencies.module_version.get_installed_module_version")
    def test_is_satisfied_empty_version_spec(self, mocked_f):

        # Empty context
        ctx_dep = ModuleVersionContextDependency("the module", "")

        mocked_f.return_value = packaging.version.Version('0.1.0')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('1.1.0')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.1.0')
        self.assertTrue(ctx_dep.is_satisfied())

    @mock.patch("ml_utils.io.context_dependencies.module_version.get_installed_module_version")
    def test_is_satisfied_simple(self, mocked_f):
        # Empty context
        ctx_dep = ModuleVersionContextDependency("the module", "~=2.2.1")

        mocked_f.return_value = packaging.version.Version('0.1.0')
        self.assertFalse(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.0')
        self.assertFalse(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.1')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.2')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('3.2.2')
        self.assertFalse(ctx_dep.is_satisfied())

    @mock.patch("ml_utils.io.context_dependencies.module_version.get_installed_module_version")
    def test_is_satisfied_complex(self, mocked_f):
        # Empty context
        ctx_dep = ModuleVersionContextDependency("the module", ">=2.2,<4")

        mocked_f.return_value = packaging.version.Version('0.1.0')
        self.assertFalse(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.0')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.1')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('2.2.2')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('3.2.2')
        self.assertTrue(ctx_dep.is_satisfied())

        mocked_f.return_value = packaging.version.Version('4.0.1')
        self.assertFalse(ctx_dep.is_satisfied())

    def test_to_dict(self):

        # Empty context
        ctx_dep = ModuleVersionContextDependency("the module", "")
        self.assertDictEqual(ctx_dep.to_dict(), {
            "type": "module-version",
            "module_name": "the module",
            "version_specs": ""
        })

        # With single version
        ctx_dep = ModuleVersionContextDependency("the module", "==2.2.1")
        self.assertDictEqual(ctx_dep.to_dict(), {
            "type": "module-version",
            "module_name": "the module",
            "version_specs": "==2.2.1"
        })

        # With multi set
        ctx_dep = ModuleVersionContextDependency("the module", "==2.2.1,<=3.0.0")
        self.assertDictEqual(ctx_dep.to_dict(), {
            "type": "module-version",
            "module_name": "the module",
            "version_specs": "==2.2.1,<=3.0.0"
        })

    def test_from_dict_wrong_types(self):

        # Dict without type
        with self.assertRaises(ValueError):
            ModuleVersionContextDependency.from_dict({})

        # Dict with wrong type
        with self.assertRaises(ValueError):
            ModuleVersionContextDependency.from_dict({
                'type': 'another-dep'
            })

        # Dict with missing module
        with self.assertRaises(TypeError):
            ModuleVersionContextDependency.from_dict({
                'type': 'module-version'
            })

        # Dict with missing spec
        with self.assertRaises(TypeError):
            ModuleVersionContextDependency.from_dict({
                'type': 'module-version',
                'module_name': 'themodule'
            })

    def test_from_dict_empty_version(self):

        # dict with empty version

        dep = ModuleVersionContextDependency.from_dict({
            'type': 'module-version',
            'module_name': 'the module',
            'version_specs': ''
        })
        self.assertEqual(dep.get_params(), {
            'module_name': 'the module',
            'version_specs': ''
        })
        self.assertEqual(dep.module_name, 'the module')
        self.assertEqual(dep.version_specs, '')

    def test_from_dict_full(self):

        # dict with empty version

        dep = ModuleVersionContextDependency.from_dict({
            "type": "module-version",
            "module_name": "the module",
            "version_specs": "==2.2.1"
        })
        self.assertEqual(dep.get_params(), {
            "module_name": "the module",
            "version_specs": "==2.2.1"
        })
        self.assertEqual(dep.module_name, 'the module')
        self.assertEqual(dep.version_specs, '==2.2.1')


if __name__ == '__main__':
    unittest.main()
