"""
Test script to be executed before pushing or submitting a PR to master
repository.
"""

import unittest

from .delta_energy_test import test_delta_sub, test_delta_add
from .oal_CuNP import oal_CuNP_energy, oal_CuNP_forces

class TestMethods(unittest.TestCase):
    def test_delta_sub(self):
        test_delta_sub()

    def test_delta_add(self):
        test_delta_add()

    def oal_CuNP_energy(self):
        oal_CuNP_energy()

    def oal_CuNP_forces(self):
        oal_CuNP_forces()

    #def oal_PtNP_energy(self):
    #    oal_PtNP_energy(self):

if __name__ == "__main__":
    unittest.main(warnings="ignore")
