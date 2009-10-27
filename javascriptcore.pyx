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

"""
Two-way binding between CPython and WebKit's JavaScriptCore.
"""

import sys
import types
cdef:
    ctypedef unsigned short bool

include "stdlib.pyi"
include "python.pyi"
include "jsbase.pyi"
include "jscontextref.pyi"
include "jsstringref.pyi"
include "jsvalueref.pyi"
include "jsobjectref.pyi"


#
# Value Conversion
#

cdef object jsToPython(JSContextRef jsCtx, JSValueRef jsValue):
    """Convert a JavaScript value into a Python value."""

    cdef int jsType = JSValueGetType(jsCtx, jsValue)
    cdef JSStringRef jsStr

    if jsType == kJSTypeUndefined or jsType == kJSTypeNull:
        return None
    elif jsType == kJSTypeBoolean:
        return types.BooleanType(JSValueToBoolean(jsCtx, jsValue))
    elif jsType == kJSTypeNumber:
        return JSValueToNumber(jsCtx, jsValue, NULL)
    elif jsType == kJSTypeString:
        jsStr = JSValueToStringCopy(jsCtx, jsValue, NULL)
        try:
            return PyUnicode_DecodeUTF16(JSStringGetCharactersPtr(jsStr),
                                         JSStringGetLength(jsStr) * 2,
                                         NULL, 0)
        finally:
            JSStringRelease(jsStr)
    elif JSObjectIsFunction(jsCtx, jsValue):
        return makeJSFunction(jsCtx, jsValue)
    else:
        return makeJSObject(jsCtx, jsValue)

    return None


class JSException(Exception):
    """Python exception class to encapsulate JavaScript exceptions."""

    def __init__(self, name, message):
        self.name = name
        self.mess = message

    def __str__(self):
        return "JSException name: %s message: %s" % (self.name, self.mess)

cdef object makeJSException(JSContextRef jsCtx, JSValueRef jsException):
    """Factory function for creating exception objects."""
    e = jsToPython(jsCtx, jsException)
    return JSException(e.name, e.message)


cdef object pyStringFromJS(JSStringRef jsString):
    return PyUnicode_DecodeUTF16(JSStringGetCharactersPtr(jsString),
                                 JSStringGetLength(jsString) * 2,
                                 NULL, 0)

cdef JSStringRef createJSStringFromPython(object pyStr):
    """Create a ``JSString`` from a Python object.

    This is a create function. Ownership of the result is transferred
    to the caller."""
    pyStr = unicode(pyStr).encode('utf-8')
    return JSStringCreateWithUTF8CString(pyStr)

cdef JSValueRef pythonToJS(JSContextRef jsCtx, object pyValue):
    """Convert a Python value into a JavaScript value.

    The returned value belongs to the specified context, and must be
    protected if they are going to be permanently stored (e.g., inside
    an object)."""

    if isinstance(pyValue, types.NoneType):
        return JSValueMakeNull(jsCtx)
    elif isinstance(pyValue, types.BooleanType):
        return JSValueMakeBoolean(jsCtx, pyValue)
    elif isinstance(pyValue, (types.IntType, types.FloatType)):
        return JSValueMakeNumber(jsCtx, pyValue)
    elif isinstance(pyValue, types.StringTypes):
        return JSValueMakeString(jsCtx, createJSStringFromPython(pyValue))
    elif isinstance(pyValue, JSObject):
        return (<JSObject>pyValue).jsObject
    elif callable(pyValue):
        return makePyFunction(jsCtx, pyValue)
    else:
        raise ValueError


#
# Python Wrappers for JavaScript objects
#

cdef class JSObject:
    """Wrapper class to make JavaScript objects accessible from Python.

    Since it is impossible to reliably distinguish between JavaScript
    arrays and other types of objects, JObjects have the ability of
    behaving like Python sequences. Some of the operations depend on
    the presence of a 'length' property, and will fail with a
    ``TypeError`` if it isn't present."""

    cdef JSContextRef jsCtx
    cdef JSObjectRef jsObject

    def __init__(self):
        self.jsCtx = NULL
        self.jsObject = NULL

    cdef setup(self, JSContextRef jsCtx, JSObjectRef jsObject):
        # We claim ownership of objects here and release them in
        # __dealloc__. Notice that we also need to own a reference to
        # the context, because it may otherwise disappear while this
        # object still exists.
        self.jsCtx = jsCtx
        JSGlobalContextRetain(self.jsCtx)
        self.jsObject = jsObject
        JSValueProtect(self.jsCtx, self.jsObject)

    def __dealloc__(self):
        JSValueUnprotect(self.jsCtx, self.jsObject)
        JSGlobalContextRelease(self.jsCtx)

    def getPropertyNames(self):
        cdef JSPropertyNameArrayRef nameArray = \
            JSObjectCopyPropertyNames(self.jsCtx, self.jsObject)

        names = []
        for i in range(JSPropertyNameArrayGetCount(nameArray)):
            names.append(pyStringFromJS(
                    JSPropertyNameArrayGetNameAtIndex(nameArray, i)))
        JSPropertyNameArrayRelease(nameArray)
        return names

    def __getattr__(self, name):
        cdef JSStringRef jsName
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsResult

        jsName = createJSStringFromPython(name)
        try:
            if not JSObjectHasProperty(self.jsCtx, self.jsObject, jsName):
                raise AttributeError, \
                    "JavaScript object has no attribute '%s'" % name

            jsResult = JSObjectGetProperty(self.jsCtx, self.jsObject,
                                           jsName, &jsException)
            if jsException != NULL:
                # TODO: Use the exception as an error message.
                raise AttributeError, name
                
            if JSObjectIsFunction(self.jsCtx, jsResult):
                # If this is a function, we mimic Python's behavior
                # and return it bound to this object.
                return makeJSBoundMethod(self.jsCtx, jsResult,
                                         self.jsObject)
            else:
                return jsToPython(self.jsCtx, jsResult)
        finally:
            JSStringRelease(jsName)

    def __setattr__(self, name, value):
        cdef JSStringRef jsName
        cdef JSValueRef jsException = NULL

        jsName = createJSStringFromPython(name)
        try:
            JSObjectSetProperty(self.jsCtx, self.jsObject, jsName,
                                pythonToJS(self.jsCtx, value),
                                kJSPropertyAttributeNone, &jsException)
            if jsException != NULL:
                # TODO: Use the exception as an error message.
                raise AttributeError, name
        finally:
            JSStringRelease(jsName)

    def __contains__(self, item):
        pass

    def __len__(self):
        try:
            return int(self.length)
        except AttributeError:
            raise TypeError, "Not an array or array-like JavaScript object"

    def __iter__(self):
        return _JSObjectIterator(self)

    def __getitem__(self, key):
        cdef JSValueRef jsValueRef
        cdef JSValueRef jsException = NULL

        jsValueRef = JSObjectGetPropertyAtIndex(self.jsCtx, self.jsObject,
                                                key, &jsException)
        if jsException != NULL:
            raise makeJSException(self.jsCtx, jsException)
        return jsToPython(self.jsCtx, jsValueRef)

    def __setitem__(self, key, value):
        cdef JSValueRef jsValue = pythonToJS(self.jsCtx, value)
        cdef JSValueRef jsException = NULL

        JSObjectSetPropertyAtIndex(self.jsCtx, self.jsObject, key, jsValue,
                                   &jsException)
        if jsException != NULL:
            raise makeJSException(self.jsCtx, jsException)

    def __delitem__(self, key):
        pass

    def insert(self, pos, item):
        pass

cdef makeJSObject(JSContextRef jsCtx, JSObjectRef jsObject):
    """Factory function for 'JSObject' instances."""
    cdef JSObject obj = JSObject()
    obj.setup(jsCtx, jsObject)
    return obj


cdef class _JSObjectIterator:
    """Iterator class for JavaScript array-like objects."""

    cdef JSObject pyObj
    cdef int index

    def __init__(self, pyObj):
        self.pyObj = pyObj
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < self.pyObj.__len__():
            value = self.pyObj[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration

    def next(self):
        """Wrap the ``__next__`` method for backwards compatibility.
        """
        return self.__next__()


cdef class JSFunction(JSObject):
    """Specialized wrapper class to make JavaScript functions callable
    from Python."""

    def __call__(self, *args):
        cdef JSValueRef *jsArgs
        cdef JSValueRef result
        cdef JSObjectRef jsThisObject
        cdef JSValueRef jsError = NULL

        if len(args):
            jsArgs = <JSValueRef *>malloc(len(args) * sizeof(JSValueRef))
        else:
            jsArgs = NULL
        for i, arg in enumerate(args):
            jsArgs[i] = pythonToJS(self.jsCtx, arg)
        result = JSObjectCallAsFunction(self.jsCtx, self.jsObject,
                                        NULL, len(args), jsArgs,
                                        &jsError)
        free(jsArgs)
        if jsError != NULL:
            raise makeJSException(self.jsCtx, jsError)
        return jsToPython(self.jsCtx, result)

cdef makeJSFunction(JSContextRef jsCtx, JSObjectRef jsObject):
    """Factory function for 'JSFunction' instances."""
    cdef JSFunction obj = JSFunction()
    obj.setup(jsCtx, jsObject)
    return obj


cdef class JSBoundMethod(JSObject):
    """A JavaScript bound method.

    Instances of this class operate in a similar way to Python bound
    methods, but they encapsulate a JavaScript object and
    function. When they are called, the function is called with the
    object as 'this' object."""

    cdef JSObjectRef thisObj 

    cdef setup2(self, JSContextRef jsCtx, JSObjectRef jsObject,
                JSObjectRef thisObj):
        JSObject.setup(self, jsCtx, jsObject)
        # __dealloc__ unprotects thisObj, so that it's guaranteed to
        # exist as long as this object exists.
        JSValueProtect(jsCtx, thisObj)
        self.thisObj = thisObj

    def __call__(self, *args):
        cdef JSValueRef *jsArgs
        cdef JSValueRef result
        cdef JSValueRef jsError = NULL

        if len(args):
            jsArgs = <JSValueRef *>malloc(len(args) * sizeof(JSValueRef))
        else:
            jsArgs = NULL
        for i, arg in enumerate(args):
            jsArgs[i] = pythonToJS(self.jsCtx, arg)
        result = JSObjectCallAsFunction(self.jsCtx, self.jsObject,
                                        self.thisObj, len(args), jsArgs,
                                        &jsError)
        free(jsArgs)
        if jsError != NULL:
            raise makeJSException(self.jsCtx, jsError)
        return jsToPython(self.jsCtx, result)

    def __dealloc__(self):
        JSValueUnprotect(self.jsCtx, self.thisObj)

cdef makeJSBoundMethod(JSContextRef jsCtx, JSObjectRef jsObject,
                       JSObjectRef thisObj):
    """Factory function for 'JSBoundMethod' instances."""
    cdef JSBoundMethod obj = JSBoundMethod()
    obj.setup2(jsCtx, jsObject, thisObj)
    return obj


cdef class JSContext:
    """Wrapper class for JavaScriptCore context objects.

    Call the constructor without arguments to obtain a new default
    context that can be used to execute JavaScript but that will not
    provide any access to a DOM or any other browser-specific objects.

    A context obtained from another object (e.g. a WebKit browser
    component can also be passed to the constructor in order to gain
    full access to it from Python.
    """

    cdef JSContextRef jsCtx
    cdef object pyCtxExtern

    def __cinit__(self, pyCtxExtern=None):
        if pyCtxExtern is None:
            # Create a new context.
            self.jsCtx = JSGlobalContextCreate(NULL)
            self.pyCtxExtern = None
        else:
            # Extract the actual context object.
            self.jsCtx = <JSContextRef>PyCObject_AsVoidPtr(pyCtxExtern)
            JSGlobalContextRetain(self.jsCtx)
            self.pyCtxExtern = pyCtxExtern

    def __init__(self, pyCtxExtern=None):
        pass

    def evaluateScript(self, script, thisObject=None , sourceURL=None,
                       startingLineNumber=1):
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsValue

        cdef JSStringRef jsScript = createJSStringFromPython(script)
        try:
            jsValue = JSEvaluateScript(self.jsCtx, jsScript,
                                       <JSObjectRef>NULL,
                                       <JSStringRef>NULL,
                                       startingLineNumber,
                                       &jsException)
            if jsException != NULL:
                raise makeJSException(self.jsCtx, jsException)
        finally:
            JSStringRelease(jsScript)

        return jsToPython(self.jsCtx, jsValue)

    def getCtx(self):
        return self.pyCtxExtern

    def __dealloc__(self):
        JSGlobalContextRelease(self.jsCtx)


#
# JavaScript Wrappers for Python Objects
#

cdef JSValueRef callableCb(JSContextRef jsCtx, JSObjectRef function,
                           JSObjectRef thisObject, size_t argumentCount,
                           JSValueRef arguments[],
                           JSValueRef* exception) with gil:
    cdef object wrapped = <object>JSObjectGetPrivate(function)
    cdef int i

    args = [jsToPython(jsCtx, arguments[i])
            for i in range(argumentCount)]
    return pythonToJS(jsCtx, wrapped(*args))
    # TODO: Trap Python exceptions, wrap them into JS exceptions and
    # send them back to the JS interpreter.

cdef void finalizeCb(JSObjectRef function):
    cdef object wrapped = <object>JSObjectGetPrivate(function)
    Py_DECREF(wrapped)

cdef JSClassDefinition callableClassDef = kJSClassDefinitionEmpty
callableClassDef.callAsFunction = callableCb
callableClassDef.finalize = finalizeCb
cdef JSClassRef callableClass = JSClassCreate(&callableClassDef)

cdef JSObjectRef makePyFunction(JSContextRef jsCtx, object function):
        Py_INCREF(function)
        return JSObjectMake(jsCtx, callableClass, <void *>function)
