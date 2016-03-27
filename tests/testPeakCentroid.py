#!/usr/bin/env python
#
# LSST Data Management System
# Copyright 2008-2016 AURA/LSST.
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

from contextlib import contextmanager
import unittest

import lsst.daf.base
import lsst.meas.base
import lsst.utils.tests

from lsst.meas.base.tests import (AlgorithmTestCase, CentroidTransformTestCase,
                                  SingleFramePluginTransformSetupHelper, ForcedPluginTransformSetupHelper)


@contextmanager
def onlyLogFatal(log):
    """
    For the duration of the context, only log FATAL errors.

    This is convenient when testing algorithms under failure conditions: we
    want to be able to check that they have set appropriate flags without
    spewing alarming & confusing error messages to the console.
    """
    oldLevel = log.getThreshold()
    log.setThreshold(log.FATAL)
    try:
        yield
    finally:
        log.setThreshold(oldLevel)


class SingleFramePeakCentroidTestCase(AlgorithmTestCase):

    def setUp(self):
        self.center = lsst.afw.geom.Point2D(50.1, 49.8)
        self.bbox = lsst.afw.geom.Box2I(lsst.afw.geom.Point2I(-20, -30),
                                        lsst.afw.geom.Extent2I(140, 160))
        self.dataset = lsst.meas.base.tests.TestDataset(self.bbox)
        self.dataset.addSource(1000000.0, self.center)
        self.task = self.makeSingleFrameMeasurementTask("base_PeakCentroid")
        self.exposure, self.catalog = self.dataset.realize(10.0, self.task.schema)

    def tearDown(self):
        del self.center
        del self.bbox
        del self.dataset
        del self.task
        del self.exposure
        del self.catalog

    def testSingleFramePlugin(self):
        """
        Check that we recover the correct location of the centroid.
        """
        self.task.run(self.exposure, self.catalog)
        x = self.catalog[0].get("base_PeakCentroid_x")
        y = self.catalog[0].get("base_PeakCentroid_y")
        self.assertFalse(self.catalog[0].get("base_PeakCentroid_flag"))
        self.assertClose(x, self.center.getX(), atol=None, rtol=.02)
        self.assertClose(y, self.center.getY(), atol=None, rtol=.02)

    def testFlags(self):
        """
        When it is impossible to measure the centroid -- in this case, because
        we have removed the Peaks from the SourceRecord -- the centroider
        should set a failure flag.
        """
        self.catalog[0].getFootprint().getPeaks().clear()
        # The decorator suppresses alarming but expected errors on the console.
        with onlyLogFatal(self.task.log):
            self.task.run(self.exposure, self.catalog)
        self.assertTrue(self.catalog[0].get("base_PeakCentroid_flag"))


class SingleFramePeakCentroidTransformTestCase(CentroidTransformTestCase,
                                               SingleFramePluginTransformSetupHelper):

    class SingleFramePeakCentroidPluginFactory(object):
        """
        Helper class to sub in an empty PropertyList as the final argument to
        lsst.meas.base.SingleFramePeakCentroidPlugin.
        """

        def __call__(self, control, name, inputSchema):
            return lsst.meas.base.SingleFramePeakCentroidPlugin(control, name, inputSchema,
                                                                lsst.daf.base.PropertyList())
    controlClass = lsst.meas.base.SingleFramePeakCentroidConfig
    algorithmClass = SingleFramePeakCentroidPluginFactory()
    transformClass = lsst.meas.base.SimpleCentroidTransform
    flagNames = ()
    singleFramePlugins = ("base_PeakCentroid",)


class ForcedPeakCentroidTransformTestCase(CentroidTransformTestCase,
                                          ForcedPluginTransformSetupHelper):
    controlClass = lsst.meas.base.ForcedPeakCentroidConfig
    algorithmClass = lsst.meas.base.ForcedPeakCentroidPlugin
    transformClass = lsst.meas.base.SimpleCentroidTransform
    flagNames = ()
    forcedPlugins = ("base_PeakCentroid",)


def suite():
    """Returns a suite containing all the test cases in this module."""

    lsst.utils.tests.init()

    suites = []
    suites += unittest.makeSuite(SingleFramePeakCentroidTestCase)
    suites += unittest.makeSuite(SingleFramePeakCentroidTransformTestCase)
    suites += unittest.makeSuite(ForcedPeakCentroidTransformTestCase)
    suites += unittest.makeSuite(lsst.utils.tests.MemoryTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    lsst.utils.tests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
