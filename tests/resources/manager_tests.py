import unittest
from pathlib import Path

from mlio.resources.exceptions import ResourceNotFoundError
from mlio.resources.manager import ResourceManager
from mlio.resources.repositories import RepositoriesContainer, LocalDirectoryRepository
from mlio.resources.resource_types import MLIOResource, VocabularyResource


class ManagerBaseTestCase(unittest.TestCase):

    def setUp(self):
        self.populated_man = ResourceManager()
        self.populated_man.repositories.add_first(
            LocalDirectoryRepository('resources_data', Path(__file__).resolve().parent / 'fixtures' / 'data'))
        self.populated_man.add_resource(MLIOResource('the-list', 'default.mlpack'))
        self.populated_man.add_resource(MLIOResource('the-text', 'multi.mlpack', slot_key='the-text'))
        self.populated_man.add_resource(VocabularyResource('the-voc', 'something.voc'))

    def test_empty_manager(self):

        # Different attributes
        man = ResourceManager()
        self.assertIsInstance(man.repositories, RepositoriesContainer)
        self.assertEqual(0, len(man.resources))

        self.assertEqual(str(man), "<ResourceManager: #0 resources in #0 repositories>")
        self.assertEqual(repr(man), "<ResourceManager: #0 resources in #0 repositories>")

    def test_add_resource(self):
        man = ResourceManager()
        r1 = MLIOResource('an id', 'broken file')
        r2 = MLIOResource('another', 'broken file')

        man.add_resource(r1)
        man.add_resource(r2)
        self.assertIs(r1.manager, man)
        self.assertIs(r2.manager, man)

        self.assertEqual(str(man), "<ResourceManager: #2 resources in #0 repositories>")
        self.assertEqual(repr(man), "<ResourceManager: #2 resources in #0 repositories>")

    def test_has_resource(self):

        # Empty manager
        man = ResourceManager()
        self.assertFalse(man.has_resource('unknown'))
        self.assertFalse(man.has_resource(False))

        # Populated
        man = ResourceManager()
        man.add_resource(MLIOResource('an id', 'broken file'))
        self.assertFalse(man.has_resource('unknown'))
        self.assertFalse(man.has_resource(False))
        self.assertTrue(man.has_resource('an id'))

        man.add_resource(MLIOResource('another', 'broken file 2'))
        self.assertFalse(man.has_resource('unknown'))
        self.assertFalse(man.has_resource(False))
        self.assertTrue(man.has_resource('an id'))
        self.assertTrue(man.has_resource('another'))

    def test_access_nonexisting_resources(self):
        man = ResourceManager()

        with self.assertRaises(ResourceNotFoundError):
            man['unknown']

        with self.assertRaises(KeyError):
            man.resources['unknown']

    def test_access_resources(self):
        man = ResourceManager()
        man.repositories.add_first(
            LocalDirectoryRepository('resources_data', Path(__file__).resolve().parent / 'fixtures' / 'data'))
        rlist = MLIOResource('the-list', 'default.mlpack')
        rtext = MLIOResource('the-text', 'multi.mlpack', slot_key='the-text')
        man.add_resource(rlist)
        man.add_resource(rtext)

        self.assertIs(man.resources['the-list'], rlist)
        self.assertIs(man.resources['the-text'], rtext)

        self.assertListEqual(
            man['the-list'],
            ['a', 'list', 'of', 'elements']
        )

        self.assertEqual(
            man['the-text'],
            "Νιαις œ•³≥≠÷’…ß÷≠ γιουνικοτ"
        )

        self.assertEqual(str(man), "<ResourceManager: #2 resources in #1 repositories>")
        self.assertEqual(repr(man), "<ResourceManager: #2 resources in #1 repositories>")

    def test_load_all_resources(self):

        # Check that are not loaded
        self.assertFalse(self.populated_man.resources['the-list'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-text'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-voc'].is_loaded())

        # Force load once
        self.populated_man.load_resources()

        # Check that are now loaded
        self.assertTrue(self.populated_man.resources['the-list'].is_loaded())
        self.assertTrue(self.populated_man.resources['the-text'].is_loaded())
        self.assertTrue(self.populated_man.resources['the-voc'].is_loaded())

    def test_load_partial_resources(self):

        # Check that are not loaded
        self.assertFalse(self.populated_man.resources['the-list'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-text'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-voc'].is_loaded())

        # Load one resource
        self.populated_man.load_resources(['the-list'])

        # Check what is loaded
        self.assertTrue(self.populated_man.resources['the-list'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-text'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-voc'].is_loaded())

        # Load another resource
        self.populated_man.load_resources(['the-text'])

        # Check what is loaded
        self.assertTrue(self.populated_man.resources['the-list'].is_loaded())
        self.assertTrue(self.populated_man.resources['the-text'].is_loaded())
        self.assertFalse(self.populated_man.resources['the-voc'].is_loaded())

    def test_load_unknown_resources(self):

        with self.assertRaises(ResourceNotFoundError):
            self.populated_man.load_resources(['only-unknown'])

        with self.assertRaises(ResourceNotFoundError):
            self.populated_man.load_resources(['only-unknown', 'but', 'many'])

    def test_load_partially_unknown_resources(self):

        # In this case it should load any resource
        with self.assertRaises(ResourceNotFoundError):
            self.populated_man.load_resources(['mixed-unknown', 'the-list'])

        with self.assertRaises(ResourceNotFoundError):
            self.populated_man.load_resources(['the-list', 'mixed-unknown'])

        self.assertFalse(self.populated_man.resources['the-list'].is_loaded())
