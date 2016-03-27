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
import lsst.meas.base
import lsst.utils.tests


class shapeTransformMatrixTestCase(lsst.utils.tests.TestCase):

    def testIdentity(self):
        # A no-op coordinate transform translates to a no-op shape transform
        a = lsst.afw.geom.AffineTransform()
        numpy.testing.assert_array_equal(a.getMatrix(), numpy.identity(3))
        m = lsst.meas.base.makeShapeTransformMatrix(a.getLinear())
        numpy.testing.assert_array_equal(m, numpy.identity(3))

    def testVsTransform(self):
        # Transforming an ellipse by multiplying by the matrix should be
        # equivalent to calling its transform() method.
        l = lsst.afw.geom.LinearTransform.makeRotation(lsst.afw.geom.Angle(numpy.random.random()))
        e = lsst.afw.geom.ellipses.Quadrupole(numpy.random.random(), numpy.random.random(),
                                              numpy.random.random())
        numpy.testing.assert_array_almost_equal(numpy.dot(lsst.meas.base.makeShapeTransformMatrix(l),
                                                          e.getParameterVector()), e.transform(l).getParameterVector())

    def testVales(self):
        # Test that the analytically-derived correct values are computed
        l = lsst.afw.geom.LinearTransform(numpy.random.random((2, 2)))
        m = lsst.meas.base.makeShapeTransformMatrix(l)

        self.assertEqual(m[0, 0], l[0, 0]*l[0, 0])
        self.assertEqual(m[0, 1], l[0, 1]*l[0, 1])
        self.assertEqual(m[0, 2], 2*l[0, 0]*l[0, 1])

        self.assertEqual(m[1, 0], l[1, 0]*l[1, 0])
        self.assertEqual(m[1, 1], l[1, 1]*l[1, 1])
        self.assertEqual(m[1, 2], 2*l[1, 0]*l[1, 1])

        self.assertEqual(m[2, 0], l[0, 0]*l[1, 0])
        self.assertEqual(m[2, 1], l[0, 1]*l[1, 1])
        self.assertEqual(m[2, 2], l[0, 0]*l[1, 1] + l[0, 1]*l[1, 0])


def suite():
    """Returns a suite containing all the test cases in this module."""
    lsst.utils.tests.init()

    suites = []
    suites += unittest.makeSuite(shapeTransformMatrixTestCase)
    suites += unittest.makeSuite(lsst.utils.tests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(exit = False):
    """Run the tests"""
    lsst.utils.tests.run(suite(), exit)

if __name__ == "__main__":
    run(True)
