# This file is part of PyJavaScriptCore, a binding between CPython and
# WebKit's JavaScriptCore.
#
# Copyright (C) 2009, Martin Soto <soto@freedesktop.org>
# Copyright (C) 2009, john paul janecek (see README file)
#
# PyJavaScriptCore is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA. 

cdef extern from "Python.h":
    ctypedef unsigned short Py_UNICODE

    void Py_INCREF(object o)
    void Py_DECREF(object o)

    char* PyString_AsString(object o)

    object PyUnicode_DecodeUTF16(Py_UNICODE *u, Py_ssize_t size,
                                 char *errors, int byteorder)

    ctypedef void * PyCapsule_Destructor
    object PyCapsule_New(void *pointer, const char *name, PyCapsule_Destructor destructor)
    void * PyCapsule_GetPointer(object capsule, const char *name)
