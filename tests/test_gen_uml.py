"""
Test case that checks the working of the utils/command/gen_uml.py module.
"""

import os
import pkg_resources
import unittest

from utils.command.gen_uml import generate


class PseudoFile(object):
    def __init__(self):
        self.data = ""

    def write(self, data):
        self.data += data

    def close(self):
        pass


class GenUmlTestCase(unittest.TestCase):
    def test_loading(self):

        dist = pkg_resources.get_distribution("gaphor")
        model_file = os.path.join(dist.location, "tests/test-model.gaphor")
        outfile = PseudoFile()

        generate(model_file, outfile)

        assert outfile.data == GENERATED, '"""%s"""' % outfile.data


GENERATED = """# This file is generated by build_uml.py. DO NOT EDIT!

from gaphor.UML.properties import association, attribute, enumeration, derived, derivedunion, redefine
# class 'ValSpec' has been stereotyped as 'SimpleAttribute'
# class 'ShouldNotShowUp' has been stereotyped as 'SimpleAttribute' too
class Element(object): pass
class SubClass(Element): pass
class C(object): pass
class D(C): pass
C.attr = attribute('attr', str)
C.name1 = association('name1', SubClass, opposite='name2')
SubClass.name2 = association('name2', C, opposite='name1')
C.base = association('base', SubClass, opposite='abstract')
D.subbase = association('subbase', SubClass, opposite='concrete')
SubClass.concrete = association('concrete', D, opposite='subbase')
D.name3 = association('name3', SubClass, opposite='name4')
# 'SubClass.value' is a simple attribute
SubClass.value = attribute('value', str)
SubClass.abstract = derivedunion('abstract', C, 0, '*', SubClass.concrete)
SubClass.name4 = redefine(SubClass, 'name4', D, name2)
"""

# # 'SubClass.value' is a simple attribute
# SubClass.value = attribute('value', str, lower=f9124094-3f14-11de-9595-00224128e79d)
