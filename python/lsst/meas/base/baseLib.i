// -*- lsst-c++ -*-
/*
 * LSST Data Management System
 * Copyright 2008-2013 LSST Corporation.
 *
 * This product includes software developed by the
 * LSST Project (http://www.lsst.org/).
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the LSST License Statement and
 * the GNU General Public License along with this program.  If not,
 * see <http://www.lsstcorp.org/LegalNotices/>.
 */

%define baseLib_DOCSTRING
"
Basic routines to talk to lsst::meas::base classes
"
%enddef

%feature("autodoc", "1");
%module(package="lsst.meas.base", docstring=baseLib_DOCSTRING) baseLib

%{
#include "lsst/pex/logging.h"
#include "lsst/afw/geom.h"
#include "lsst/afw/math.h"
#include "lsst/afw/table.h"
#include "lsst/afw/cameraGeom.h"
#include "lsst/afw/image.h"
#include "lsst/afw/detection.h"
#include "lsst/meas/base.h"
#define PY_ARRAY_UNIQUE_SYMBOL LSST_MEAS_BASE_NUMPY_ARRAY_API
#include "numpy/arrayobject.h"
#include "ndarray/swig.h"
#include "ndarray/swig/eigen.h"
%}

%init %{
    import_array();
%}

%include "lsst/p_lsstSwig.i"
%include "lsst/base.h"
%include "std_complex.i"

%include "ndarray.i"

%declareNumPyConverters(lsst::meas::base::CentroidCov);

%lsst_exceptions();

%include "std_vector.i"
%import "lsst/afw/geom/geomLib.i"
%import "lsst/afw/table/tableLib.i"
%import "lsst/afw/image/imageLib.i"
%import "lsst/afw/detection/detectionLib.i"
%import "lsst/pex/config.h"
%import "lsst/afw/image/Exposure.h"

%include "lsst/meas/base/Results.h"
%include "lsst/meas/base/ResultMappers.h"
%include "lsst/meas/base/Inputs.h"

%define %instantiateInput(T)
%ignore std::vector<lsst::meas::base::T>::vector(size_type);
%ignore std::vector<lsst::meas::base::T>::resize(size_type);
%template(T ## Vector) std::vector<lsst::meas::base::T>;
%pythoncode %{
T.Vector = T ## Vector
%}
%enddef

%instantiateInput(AlgorithmInput1)
%instantiateInput(AlgorithmInput2)
%instantiateInput(AlgorithmInput3)

%pythoncode %{
    FlagsResult = {}
    FlagsResultMapper = {}
%}

%define %instantiateFlags(N)
%template(FlagsResult ## N) lsst::meas::base::FlagsResult<N>;
%template(FlagsResultMapper ## N) lsst::meas::base::FlagsResultMapper<N>;
%pythoncode %{
    FlagsResult[N] = FlagsResult ## N
    FlagsResultMapper[N] = FlagsResultMapper ## N
%}
%enddef

%instantiateFlags(0)
%instantiateFlags(1)
%instantiateFlags(2)
%instantiateFlags(3)
%instantiateFlags(4)
%instantiateFlags(5)
%instantiateFlags(6)
%instantiateFlags(7)
%instantiateFlags(8)

%define %instantiateSimpleResult1(NAMESPACE, ALGORITHM, T1)
%template(ALGORITHM##SimpleResult1) lsst::meas::base::SimpleResult1< NAMESPACE::ALGORITHM, T1 >;
%template(ALGORITHM##SimpleResultMapper1) lsst::meas::base::SimpleResult1< NAMESPACE::ALGORITHM, T1##Mapper>;
%enddef

%define %instantiateSimpleResult2(NAMESPACE, ALGORITHM, T1, T2)
%template(ALGORITHM##SimpleResult2) lsst::meas::base::SimpleResult2< NAMESPACE::ALGORITHM, T1, T2 >;
%template(ALGORITHM##SimpleResultMapper2) lsst::meas::base::SimpleResult2< NAMESPACE::ALGORITHM, T1##Mapper, T2##Mapper >;
%enddef

%define %instantiateSimpleResult3(NAMESPACE, ALGORITHM, T1, T2, T3)
%template(ALGORITHM##SimpleResult3) lsst::meas::base::SimpleResult3< NAMESPACE::ALGORITHM, T1, T2, T3 >;
%template(ALGORITHM##SimpleResultMapper3) lsst::meas::base::SimpleResult3< NAMESPACE::ALGORITHM, T1##Mapper, T2##Mapper, T3##Mapper>;
%enddef

%include "lsst/meas/base/PsfFlux.h"
%include "lsst/meas/base/SdssShape.h"

%template(apply) lsst::meas::base::PsfFluxAlgorithm::apply<float>;
%template(apply) lsst::meas::base::PsfFluxAlgorithm::apply<double>;
%template(apply) lsst::meas::base::SdssShapeAlgorithm::apply<float>;
%template(apply) lsst::meas::base::SdssShapeAlgorithm::apply<double>;

%instantiateSimpleResult1(lsst::meas::base, PsfFluxAlgorithm, lsst::meas::base::FluxResult)
%instantiateSimpleResult3(lsst::meas::base, SdssShapeAlgorithm, lsst::meas::base::ShapeResult, lsst::meas::base::CentroidResult, lsst::meas::base::FluxResult)

// Turn C++ typedefs into equivalent Python attributes - it's a shame Swig doesn't do this for us.
%pythoncode %{

PsfFluxAlgorithm.Control = NullControl
PsfFluxAlgorithm.Result = PsfFluxAlgorithmSimpleResult1
PsfFluxAlgorithm.ResultMapper = PsfFluxAlgorithmSimpleResultMapper1
PsfFluxAlgorithm.Input = AlgorithmInput2

SdssShapeAlgorithm.Control = SdssShapeControl
SdssShapeAlgorithm.Result = SdssShapeAlgorithmSimpleResult3
SdssShapeAlgorithm.ResultMapper = SdssShapeAlgorithmSimpleResultMapper3
SdssShapeAlgorithm.Input = AlgorithmInput2

%}
