#pragma once
#include "Initializer/Initializer.h"
#include "TaintTracking/TaintRange.h"
#include "TaintTracking/TaintedObject.h"
#include "Utils/StringUtils.h"
#include <Python.h>
#include <pybind11/pybind11.h>

using namespace std;
using namespace pybind11::literals;
namespace py = pybind11;

PyObject*
api_new_pyobject_id(PyObject* self, PyObject* const* args, Py_ssize_t nargs);

bool
is_tainted(PyObject* tainted_object, TaintRangeMapType* tx_taint_map);

bool
api_is_tainted(py::object tainted_object);

void
pyexport_tainted_ops(py::module& m);