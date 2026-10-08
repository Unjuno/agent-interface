#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>

static inline uint64_t read_counter(void) {
    uint64_t value;
    __asm__ volatile("mrs %0, cntvct_el0" : "=r"(value));
    return value;
}

static PyObject *read_counter_py(PyObject *self, PyObject *unused) {
    return PyLong_FromUnsignedLongLong((unsigned long long)read_counter());
}

static PyObject *read_frequency_py(PyObject *self, PyObject *unused) {
    uint64_t value;
    __asm__ volatile("mrs %0, cntfrq_el0" : "=r"(value));
    return PyLong_FromUnsignedLongLong((unsigned long long)value);
}

static PyObject *call_timed(PyObject *self, PyObject *args) {
    PyObject *callable, *positional, *keywords = Py_None;
    if (!PyArg_ParseTuple(args, "OO|O", &callable, &positional, &keywords)) return NULL;
    uint64_t before = read_counter();
    PyObject *result = PyObject_Call(callable, positional, keywords == Py_None ? NULL : keywords);
    uint64_t after = read_counter();
    if (result == NULL) return NULL;
    PyObject *out = Py_BuildValue("OKK", result, (unsigned long long)before, (unsigned long long)after);
    Py_DECREF(result);
    return out;
}

static PyMethodDef methods[] = {
    {"read_counter", read_counter_py, METH_NOARGS, "Read CNTVCT_EL0."},
    {"read_frequency", read_frequency_py, METH_NOARGS, "Read CNTFRQ_EL0."},
    {"call_timed", call_timed, METH_VARARGS, "Call a getter between two CNTVCT_EL0 reads."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {PyModuleDef_HEAD_INIT, "counter_call", NULL, -1, methods};
PyMODINIT_FUNC PyInit_counter_call(void) { return PyModule_Create(&module); }
