#!/usr/bin/env python
#
# LSST Data Management System
# Copyright 2008-2014 AURA/LSST.
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

import math
import unittest

import lsst.afw.image as afwImage
import lsst.afw.geom as afwGeom
import lsst.afw.table as afwTable
import lsst.daf.base as dafBase
import lsst.meas.base as measBase
import lsst.utils.tests as utilsTests
import lsst.afw.detection as afwDetection

import lsst.afw.display.ds9 as ds9

try:
    type(verbose)
except NameError:
    verbose = 0
    display = False


def makePluginAndCat(alg, name, control, metadata=False, centroid=None):
    schema = afwTable.SourceTable.makeMinimalSchema()
    if centroid:
        schema.addField(centroid + "_x", type=float)
        schema.addField(centroid + "_y", type=float)
        schema.addField(centroid + "_flag", type='Flag')
        schema.getAliasMap().set("slot_Centroid", centroid)
    if metadata:
        plugin = alg(control, name, schema, dafBase.PropertySet())
    else:
        plugin = alg(control, name, schema)
    cat = afwTable.SourceCatalog(schema)
    return plugin, cat

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


class ShapeTestCase(unittest.TestCase):
    """A test case for centroiding"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testCleanup(self):
        """Test that tearDown does"""
        pass

    def do_testmeasureShape(self):
        """Test that we can instantiate and play with a measureShape"""

        im = afwImage.ImageF(afwGeom.ExtentI(100))
        msk = afwImage.MaskU(im.getDimensions())
        msk.set(0)
        var = afwImage.ImageF(im.getDimensions())
        var.set(10)
        mi = afwImage.MaskedImageF(im, msk, var)
        del im
        del msk
        del var
        exp = afwImage.makeExposure(mi)

        bkgd = 100.0
        control = measBase.SdssShapeControl()
        control.background = bkgd
        control.maxShift = 2
        plugin, cat = makePluginAndCat(measBase.SdssShapeAlgorithm, "test", control, centroid="centroid")

        # cat.defineCentroid("test")
        cat.defineShape("test")
        #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        #
        # Add a Gaussian to the image
        #
        for a, b, phi, tol in [              # n.b. phi in degrees
            (2.5, 1.5, 90.0, 1e-3),
            (1.5, 2.5, 0.0, 1e-3),
            (1.5, 2.5, 45.0, 1e-3),
            (1.5, 2.5, 90.0, 1e-3),

            (3.0, 2.5, 0.0, 1e-3),

            (3.0, 12.5, 0.0, 1e-3),
            (3.0, 12.5, 0.0, 2e-4),

            (1.0, 1.0, 0.0, 4e-3),
            (1.0, 0.75, 0.0, 2e-2),
            #(0.75, 0.75, 0.0, 1e-1),
        ]:
            if b > a:
                a, b = b, a
                phi -= 90
            a, b, phi = float(a), float(b), math.radians(phi)

            im = mi.getImage()
            x, y = 30, 40               # centre of object
            im[:] = bkgd

            axes = afwGeom.ellipses.Axes(a, b, phi, True)
            quad = afwGeom.ellipses.Quadrupole(axes)
            if False:
                a0, b0 = a, b
                pixellatedAxes = axes.convolve(afwGeom.ellipses.Quadrupole(1/6.0, 1/6.0))
                a, b = pixellatedAxes.getA(), pixellatedAxes.getB()
                print a, b, a0, b0
            sigma_xx, sigma_yy, sigma_xy = quad.getIxx(), quad.getIyy(), quad.getIxy()

            ksize = 2*int(4*max(a, b)) + 1
            c, s = math.cos(phi), math.sin(phi)

            sum, sumxx, sumxy, sumyy = 4*[0.0] if False else 4*[None]
            for dx in range(-ksize/2, ksize/2 + 1):
                for dy in range(-ksize/2, ksize/2 + 1):
                    u, v = c*dx + s*dy, s*dx - c*dy
                    I = 1000*math.exp(-0.5*((u/a)**2 + (v/b)**2))
                    im[x + dx, y + dy] += I

                    if sum is not None:
                        sum += I
                        sumxx += I*dx*dx
                        sumxy += I*dx*dy
                        sumyy += I*dy*dy

            if sum is not None:
                sumxx /= sum
                sumxy /= sum
                sumyy /= sum
                print "RHL %g %g %g" % (sumxx, sumyy, sumxy)

            if display:
                ds9.mtv(im)

            footprint = afwDetection.FootprintSet(im, afwDetection.Threshold(110)).getFootprints()[0]
            source = cat.addNew()
            source.setFootprint(footprint)
            source.set("centroid_x", footprint.getPeaks()[0].getCentroid().getX())
            source.set("centroid_y", footprint.getPeaks()[0].getCentroid().getY())
            plugin.measure(source, exp)

            if False:
                Ixx, Iyy, Ixy = source.getIxx(), source.getIyy(), source.getIxy()
                A2 = 0.5*(Ixx + Iyy) + math.sqrt((0.5*(Ixx - Iyy))**2 + Ixy**2)
                B2 = 0.5*(Ixx + Iyy) - math.sqrt((0.5*(Ixx - Iyy))**2 + Ixy**2)

                print "I_xx:  %.5f %.5f" % (Ixx, sigma_xx)
                print "I_xy:  %.5f %.5f" % (Ixy, sigma_xy)
                print "I_yy:  %.5f %.5f" % (Iyy, sigma_yy)
                print "A2, B2 = %.5f, %.5f" % (A2, B2)

            print source.getX(), source.getY(), x, y
            print source.getIxx(), sigma_xx, source.getIyy(), sigma_yy, source.getIxy(), sigma_xy
            self.assertTrue(abs(x - source.getX()) < 1e-4, "%g v. %g" % (x, source.getX()))
            self.assertTrue(abs(y - source.getY()) < 1e-4, "%g v. %g" % (y, source.getY()))
            self.assertTrue(abs(source.getIxx() - sigma_xx) < tol*(1 + sigma_xx),
                            "%g v. %g" % (sigma_xx, source.getIxx()))
            self.assertTrue(abs(source.getIxy() - sigma_xy) < tol*(1 + abs(sigma_xy)),
                            "%g v. %g" % (sigma_xy, source.getIxy()))
            self.assertTrue(abs(source.getIyy() - sigma_yy) < tol*(1 + sigma_yy),
                            "%g v. %g" % (sigma_yy, source.getIyy()))

    def testSDSSmeasureShape(self):
        """Test that we can instantiate and play with SDSSmeasureShape"""

        self.do_testmeasureShape()

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


def suite():
    """Returns a suite containing all the test cases in this module."""
    utilsTests.init()

    suites = []
    suites += unittest.makeSuite(ShapeTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(exit = False):
    """Run the tests"""
    utilsTests.run(suite(), exit)

if __name__ == "__main__":
    run(True)
