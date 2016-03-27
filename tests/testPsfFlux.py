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
import lsst.afw.image
import lsst.afw.table
import lsst.utils.tests
import lsst.meas.base.tests

from lsst.meas.base.tests import (AlgorithmTestCase, FluxTransformTestCase,
                                  SingleFramePluginTransformSetupHelper)


class PsfFluxTestCase(AlgorithmTestCase):

    def setUp(self):
        self.center = lsst.afw.geom.Point2D(50.1, 49.8)
        self.bbox = lsst.afw.geom.Box2I(lsst.afw.geom.Point2I(0, 0),
                                        lsst.afw.geom.Extent2I(100, 100))
        self.dataset = lsst.meas.base.tests.TestDataset(self.bbox)
        self.dataset.addSource(100000.0, self.center)

    def tearDown(self):
        del self.center
        del self.bbox
        del self.dataset

    def makeAlgorithm(self, ctrl=None):
        """Construct an algorithm (finishing a schema in the process), and return both.
        """
        if ctrl is None:
            ctrl = lsst.meas.base.PsfFluxControl()
        schema = lsst.meas.base.tests.TestDataset.makeMinimalSchema()
        algorithm = lsst.meas.base.PsfFluxAlgorithm(ctrl, "base_PsfFlux", schema)
        return algorithm, schema

    def testMasking(self):
        algorithm, schema = self.makeAlgorithm()
        exposure, catalog = self.dataset.realize(10.0, schema)
        record = catalog[0]
        badPoint = lsst.afw.geom.Point2I(self.center) + lsst.afw.geom.Extent2I(3, 4)
        imageArray = exposure.getMaskedImage().getImage().getArray()
        maskArray = exposure.getMaskedImage().getMask().getArray()
        badMask = exposure.getMaskedImage().getMask().getPlaneBitMask("BAD")
        imageArray[badPoint.getY() - exposure.getY0(), badPoint.getX() - exposure.getX0()] = numpy.inf
        maskArray[badPoint.getY() - exposure.getY0(), badPoint.getX() - exposure.getX0()] |= badMask
        # Should get an infinite value exception, because we didn't mask that one pixel
        self.assertRaises(lsst.meas.base.PixelValueError, algorithm.measure, record, exposure)
        # If we do mask it, we should get a reasonable result
        ctrl = lsst.meas.base.PsfFluxControl()
        ctrl.badMaskPlanes = ["BAD"]
        algorithm, schema = self.makeAlgorithm(ctrl)
        algorithm.measure(record, exposure)
        # rng dependent
        self.assertClose(record.get("base_PsfFlux_flux"), record.get("truth_flux"),
                         atol=3*record.get("base_PsfFlux_fluxSigma"))
        # If we mask the whole image, we should get a MeasurementError
        maskArray[:, :] |= badMask
        with self.assertRaises(lsst.meas.base.MeasurementError) as context:
            algorithm.measure(record, exposure)
        self.assertEqual(context.exception.getFlagBit(), lsst.meas.base.PsfFluxAlgorithm.NO_GOOD_PIXELS)

    def testSubImage(self):
        """Test that we don't get confused by images with nonzero xy0, and that the EDGE flag is set
        when it should be.
        """
        algorithm, schema = self.makeAlgorithm()
        exposure, catalog = self.dataset.realize(10.0, schema)
        record = catalog[0]
        psfImage = exposure.getPsf().computeImage(record.getCentroid())
        bbox = psfImage.getBBox()
        bbox.grow(-1)
        subExposure = exposure.Factory(exposure, bbox, lsst.afw.image.LOCAL)
        algorithm.measure(record, subExposure)
        self.assertClose(record.get("base_PsfFlux_flux"), record.get("truth_flux"),
                         atol=3*record.get("base_PsfFlux_fluxSigma"))
        self.assertTrue(record.get("base_PsfFlux_flag_edge"))

    def testNoPsf(self):
        """Test that we raise FatalAlgorithmError when there's no PSF.
        """
        algorithm, schema = self.makeAlgorithm()
        exposure, catalog = self.dataset.realize(10.0, schema)
        exposure.setPsf(None)
        self.assertRaises(lsst.meas.base.FatalAlgorithmError, algorithm.measure, catalog[0], exposure)

    def testMonteCarlo(self):
        """Test that we get exactly the right answer on an ideal sim with no noise, and that
        the reported uncertainty agrees with a Monte Carlo test of the noise.
        """
        algorithm, schema = self.makeAlgorithm()
        exposure, catalog = self.dataset.realize(0.0, schema)
        record = catalog[0]
        flux = record.get("truth_flux")
        algorithm.measure(record, exposure)
        self.assertClose(record.get("base_PsfFlux_flux"), flux, rtol=1E-3)
        self.assertClose(record.get("base_PsfFlux_fluxSigma"), 0.0, rtol=1E-3)
        for noise in (0.001, 0.01, 0.1):
            fluxes = []
            fluxSigmas = []
            nSamples = 1000
            for repeat in xrange(nSamples):
                exposure, catalog = self.dataset.realize(noise*flux, schema)
                record = catalog[0]
                algorithm.measure(record, exposure)
                fluxes.append(record.get("base_PsfFlux_flux"))
                fluxSigmas.append(record.get("base_PsfFlux_fluxSigma"))
            fluxMean = numpy.mean(fluxes)
            fluxSigmaMean = numpy.mean(fluxSigmas)
            fluxStandardDeviation = numpy.std(fluxes)
            self.assertClose(fluxSigmaMean, fluxStandardDeviation, rtol=0.10)   # rng dependent
            self.assertLess(fluxMean - flux, 2.0*fluxSigmaMean / nSamples**0.5)   # rng dependent

    def testSingleFramePlugin(self):
        task = self.makeSingleFrameMeasurementTask("base_PsfFlux")
        exposure, catalog = self.dataset.realize(10.0, task.schema)
        task.run(exposure, catalog)
        record = catalog[0]
        self.assertFalse(record.get("base_PsfFlux_flag"))
        self.assertFalse(record.get("base_PsfFlux_flag_noGoodPixels"))
        self.assertFalse(record.get("base_PsfFlux_flag_edge"))
        self.assertClose(record.get("base_PsfFlux_flux"), record.get("truth_flux"),
                         atol=3*record.get("base_PsfFlux_fluxSigma"))

    def testForcedPlugin(self):
        task = self.makeForcedMeasurementTask("base_PsfFlux")
        measWcs = self.dataset.makePerturbedWcs(self.dataset.exposure.getWcs())
        measDataset = self.dataset.transform(measWcs)
        exposure, truthCatalog = measDataset.realize(10.0, measDataset.makeMinimalSchema())
        refCat = self.dataset.catalog
        refWcs = self.dataset.exposure.getWcs()
        measCat = task.generateMeasCat(exposure, refCat, refWcs)
        task.attachTransformedFootprints(measCat, refCat, exposure, refWcs)
        task.run(measCat, exposure, refCat, refWcs)
        measRecord = measCat[0]
        truthRecord = truthCatalog[0]
        # Centroid tolerances set to ~ single precision epsilon
        self.assertClose(measRecord.get("slot_Centroid_x"), truthRecord.get("truth_x"), rtol=1E-7)
        self.assertClose(measRecord.get("slot_Centroid_y"), truthRecord.get("truth_y"), rtol=1E-7)
        self.assertFalse(measRecord.get("base_PsfFlux_flag"))
        self.assertFalse(measRecord.get("base_PsfFlux_flag_noGoodPixels"))
        self.assertFalse(measRecord.get("base_PsfFlux_flag_edge"))
        self.assertClose(measRecord.get("base_PsfFlux_flux"), truthCatalog.get("truth_flux"),
                         rtol=1E-3)
        self.assertLess(measRecord.get("base_PsfFlux_fluxSigma"), 500.0)


class PsfFluxTransformTestCase(FluxTransformTestCase, SingleFramePluginTransformSetupHelper):
    controlClass = lsst.meas.base.PsfFluxControl
    algorithmClass = lsst.meas.base.PsfFluxAlgorithm
    transformClass = lsst.meas.base.PsfFluxTransform
    flagNames = ('flag', 'flag_noGoodPixels', 'flag_edge')
    singleFramePlugins = ('base_PsfFlux',)
    forcedPlugins = ('base_PsfFlux',)


def suite():
    """Returns a suite containing all the test cases in this module."""

    lsst.utils.tests.init()

    suites = []
    suites += unittest.makeSuite(PsfFluxTestCase)
    suites += unittest.makeSuite(PsfFluxTransformTestCase)
    suites += unittest.makeSuite(lsst.utils.tests.MemoryTestCase)
    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    lsst.utils.tests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
