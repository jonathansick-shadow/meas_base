#!/usr/bin/env python
#
# LSST Data Management System
# Copyright 2008-2015 AURA/LSST.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#

import unittest

import numpy

import lsst.afw.geom
import lsst.meas.base.tests
import lsst.utils.tests
import lsst.pex.exceptions


class InputUtilitiesTestCase(lsst.meas.base.tests.AlgorithmTestCase):

    def testFlagAliases(self):
        """Test that we get flag aliases to the slot centroid and shape algorithms when we
        initialize GaussianFlux (which uses both SafeCentroidExtractor and SafeShapeExtractor).
        """
        config = self.makeSingleFrameMeasurementConfig("base_GaussianFlux",
                                                       ["base_SdssCentroid", "base_SdssShape"])
        config.slots.centroid = "base_SdssCentroid"
        config.slots.shape = "base_SdssShape"
        task = self.makeSingleFrameMeasurementTask(config=config)
        # Test that the aliases resolve to the correct field.
        self.assertEqual(task.schema.find("base_GaussianFlux_flag_badCentroid").key,
                         task.schema.find("base_SdssCentroid_flag").key)
        self.assertEqual(task.schema.find("base_GaussianFlux_flag_badShape").key,
                         task.schema.find("base_SdssShape_flag").key)
        # Test that the aliases are direct links (i.e. they do not require recursive expansion).
        self.assertEqual(task.schema.getAliasMap().get("base_GaussianFlux_flag_badCentroid"),
                         "base_SdssCentroid_flag")
        self.assertEqual(task.schema.getAliasMap().get("base_GaussianFlux_flag_badShape"),
                         "base_SdssShape_flag")

    def testCentroidFlagAliases(self):
        """Test that we setup the right aliases when using centroid algorithms to feed each other.
        """
        config = self.makeSingleFrameMeasurementConfig("base_NaiveCentroid", ["base_SdssCentroid"])
        config.slots.centroid = "base_SdssCentroid"
        config.slots.shape = None
        task = self.makeSingleFrameMeasurementTask(config=config)
        # Test that the alias resolves to the correct field.
        self.assertEqual(task.schema.find("base_NaiveCentroid_flag_badInitialCentroid").key,
                         task.schema.find("base_SdssCentroid_flag").key)
        # Test that the alias is a direct links (i.e. it do not require recursive expansion).
        self.assertEqual(task.schema.getAliasMap().get("base_NaiveCentroid_flag_badInitialCentroid"),
                         "base_SdssCentroid_flag")
        # Test that there is no circular alias for the slot centroider itself.
        self.assertRaises(KeyError, task.schema.find, "base_SdssCentroid_flag_badInitialCentroid")

    def testUnmetCentroidDependency(self):
        """Test that we throw an exception (LogicError) when initializing an algorithm
        that requires a centroid without the centroid slot set.
        """
        config = self.makeSingleFrameMeasurementConfig("base_GaussianFlux",
                                                       ["base_SdssCentroid", "base_SdssShape"])
        config.slots.centroid = None
        config.slots.shape = "base_SdssShape"
        self.assertRaises(lsst.pex.exceptions.LogicError, self.makeSingleFrameMeasurementTask, config=config)

    def testUnmetShapeDependency(self):
        """Test that we throw an exception (LogicError) when initializing an algorithm
        that requires a shape without the shape slot set.
        """
        config = self.makeSingleFrameMeasurementConfig("base_GaussianFlux",
                                                       ["base_SdssCentroid", "base_SdssShape"])
        config.slots.centroid = "base_SdssCentroid"
        config.slots.shape = None
        self.assertRaises(lsst.pex.exceptions.LogicError, self.makeSingleFrameMeasurementTask, config=config)


def suite():
    """Returns a suite containing all the test cases in this module."""
    lsst.utils.tests.init()

    suites = []
    suites += unittest.makeSuite(InputUtilitiesTestCase)
    suites += unittest.makeSuite(lsst.utils.tests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(exit = False):
    """Run the tests"""
    lsst.utils.tests.run(suite(), exit)

if __name__ == "__main__":
    run(True)
