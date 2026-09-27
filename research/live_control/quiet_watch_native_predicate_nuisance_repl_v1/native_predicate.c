#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>

#define ROI_BYTES 4096

static PyObject *count_target(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *obj = NULL;
    if (!PyArg_ParseTuple(args, "O!:count_target", &PyBytes_Type, &obj)) {
        return NULL;
    }
    char *buf = NULL;
    Py_ssize_t n = 0;
    if (PyBytes_AsStringAndSize(obj, &buf, &n) < 0) {
        return NULL;
    }
    if (n != ROI_BYTES) {
        PyErr_Format(PyExc_ValueError, "expected %d bytes, got %zd", ROI_BYTES, n);
        return NULL;
    }
    const uint8_t *p = (const uint8_t *)buf;
    Py_ssize_t count = 0;
    for (Py_ssize_t i = 0; i < ROI_BYTES; i += 4) {
        count += (p[i] == 50u && p[i + 1] == 50u && p[i + 2] == 220u);
    }
    return PyLong_FromSsize_t(count);
}

static PyMethodDef methods[] = {
    {"count_target", count_target, METH_VARARGS, "Count exact BGR target pixels in one 32x32 BGRX ROI."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "native_predicate",
    "Exact BGRX ROI predicate candidate.",
    -1,
    methods
};

PyMODINIT_FUNC PyInit_native_predicate(void) {
    return PyModule_Create(&module);
}
