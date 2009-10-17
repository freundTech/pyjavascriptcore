cdef extern from "Python.h":
    ctypedef unsigned short Py_UNICODE

    void Py_INCREF(object o)
    void Py_DECREF(object o)

    char* PyCObject_GetDesc(object self)
    void* PyCObject_AsVoidPtr(object self)
    char* PyString_AsString(object o)
    object PyUnicode_DecodeUTF16(Py_UNICODE *u, Py_ssize_t size,
                                 char *errors, int byteorder)
