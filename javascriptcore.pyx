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
import collections

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
# Null Singleton
#

class NullType(object):
    """A singleton type to represent JavaScript's `null` value in
    Python."""

    def __init__(self):
        # Make this a singleton class.
        if Null is not None:
            raise TypeError("cannot create '%s' instances"
                            % self.__class__.__name__)

    def __nonzero__(self):
        # As in javascript, the Null value has a false boolean value.
        return False

# Create the actual Null singleton.
Null = None
Null = NullType()


#
# Value Conversion
#

cdef object jsToPython(JSContextRef jsCtx, JSValueRef jsValue):
    """Convert a JavaScript value into a Python value."""

    cdef int jsType = JSValueGetType(jsCtx, jsValue)
    cdef JSStringRef jsStr

    if jsType == kJSTypeUndefined:
        return None
    if jsType == kJSTypeNull:
        return Null
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
    elif JSValueIsObjectOfClass(jsCtx, jsValue, pyObjectClass):
        # This is a wrapped Python object. Just unwrap it.
        return <object>JSObjectGetPrivate(jsValue)
    elif JSObjectIsFunction(jsCtx, jsValue):
        return makeJSFunction(jsCtx, jsValue)
    else:
        return makeJSObject(jsCtx, jsValue)

    return None


class JSException(Exception):
    """Python exception class to encapsulate JavaScript exceptions."""

    def __init__(self, pyWrapped):
        """Create a JavaScript exception object.#

        The parameter is the original exception object thrown by the
        JavaScript code, wrapped as a Python object."""
        self.pyWrapped = pyWrapped
        try:
            self.name = pyWrapped.name
        except AttributeError:
            self.name = '<Unknown error>'
        try:
            self.message = pyWrapped.message
        except AttributeError:
            self.message = '<no message>'

    def __str__(self):
        return self.message

cdef object jsExceptionToPython(JSContextRef jsCtx, JSValueRef jsException):
    """Factory function for creating exception objects."""
    return JSException(jsToPython(jsCtx, jsException))


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
    protected if it is going to be permanently stored (e.g., inside an
    object)."""

    if isinstance(pyValue, types.NoneType):
        return JSValueMakeUndefined(jsCtx)
    elif isinstance(pyValue, NullType):
        return JSValueMakeNull(jsCtx)
    elif isinstance(pyValue, types.BooleanType):
        return JSValueMakeBoolean(jsCtx, pyValue)
    elif isinstance(pyValue, (types.IntType, types.FloatType)):
        return JSValueMakeNumber(jsCtx, pyValue)
    elif isinstance(pyValue, types.StringTypes):
        return JSValueMakeString(jsCtx, createJSStringFromPython(pyValue))
    elif isinstance(pyValue, _JSObject):
        # This is a wrapped JavaScript object, just unwrap it.
        return (<_JSObject>pyValue).jsObject
    else:
        # Wrap all other Python objects into a generic wrapper.
        return makePyObject(jsCtx, pyValue)


#
# Python Wrappers for JavaScript objects
#

# The name of the length array property.
cdef JSStringRef jsLengthName = JSStringCreateWithUTF8CString("length")


cdef class _JSObject:
    """Wrapper class to make JavaScript objects accessible from Python.

    Since it is impossible to reliably distinguish between JavaScript
    arrays and other types of objects, JSObjects have the ability of
    behaving like Python sequences. Some of the operations depend on
    the presence of a 'length' property, and will fail with a
    ``TypeError`` when it isn't present.

    Since Cython extension classes cannot inherit from Python classes,
    we first define class ``_JSObject`` and then define ``JSObject``
    as a standard Python class that mixes in ``MutableSequence`` from
    the ``collections`` module."""

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

    def __getattr__(self, pyName):
        cdef JSStringRef jsName
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsResult

        jsName = createJSStringFromPython(pyName)
        try:
            jsResult = JSObjectGetProperty(self.jsCtx, self.jsObject,
                                           jsName, &jsException)
            if jsException != NULL:
                raise jsExceptionToPython(self.jsCtx, jsException)

            if JSValueIsUndefined(self.jsCtx, jsResult):
                # This may be a property with an undefined value, or
                # no property at all.
                if JSObjectHasProperty(self.jsCtx, self.jsObject, jsName):
                    return jsToPython(self.jsCtx, jsResult)
                else:
                    # For inexisting properties, we use Python
                    # behavior.
                    raise AttributeError, \
                        "JavaScript object has no property '%s'" % pyName
            elif not JSValueIsObjectOfClass(self.jsCtx, jsResult,
                                          pyObjectClass) and \
                  JSObjectIsFunction(self.jsCtx, jsResult):
                # This is a native JavaScript function, we mimic
                # Python's behavior and return it bound to this
                # object.
                return makeJSBoundMethod(self.jsCtx, jsResult,
                                         self.jsObject)
            else:
                return jsToPython(self.jsCtx, jsResult)
        finally:
            JSStringRelease(jsName)

    def __setattr__(self, pyName, pyValue):
        cdef JSStringRef jsName
        cdef JSValueRef jsException = NULL

        jsName = createJSStringFromPython(pyName)
        try:
            JSObjectSetProperty(self.jsCtx, self.jsObject, jsName,
                                pythonToJS(self.jsCtx, pyValue),
                                kJSPropertyAttributeNone, &jsException)
            if jsException != NULL:
                raise jsExceptionToPython(self.jsCtx, jsException)
        finally:
            JSStringRelease(jsName)

    def __delattr__(self, pyName):
        cdef JSStringRef jsName
        cdef JSValueRef jsException = NULL

        jsName = createJSStringFromPython(pyName)
        try:
            if not JSObjectHasProperty(self.jsCtx, self.jsObject, jsName):
                # Use Python behavior for inexisting properties.
                raise AttributeError, \
                    "JavaScript object has no property '%s'" % pyName

            if not JSObjectDeleteProperty(self.jsCtx, self.jsObject,
                                          jsName, &jsException):
                raise AttributeError, \
                    "property '%s' of JavaScript object cannot " \
                    "be deleted" % pyName
            if jsException != NULL:
                raise jsExceptionToPython(self.jsCtx, jsException)
        finally:
            JSStringRelease(jsName)


    #
    # Sequence-related standard methods
    #

    cdef int getLength(self) except -1:
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsResult
        cdef int result

        jsResult = JSObjectGetProperty(self.jsCtx, self.jsObject,
                                       jsLengthName, &jsException)
        if jsException != NULL or JSValueIsUndefined(self.jsCtx, jsResult):
            raise TypeError, "not an array or array-like JavaScript object"

        result = <int>JSValueToNumber(self.jsCtx, jsResult, &jsException)
        if jsException != NULL:
            raise TypeError, "not an array or array-like JavaScript object"

        return result

    cdef JSValueRef getItem(self, int pyKey) except NULL:
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsResult

        jsResult = JSObjectGetPropertyAtIndex(self.jsCtx, self.jsObject,
                                              pyKey, &jsException)
        if jsException != NULL:
            raise jsExceptionToPython(self.jsCtx, jsException)

        return jsResult

    def __contains__(self, pyItem):
        cdef JSValueRef jsItem = pythonToJS(self.jsCtx, pyItem)
        cdef JSValueRef jsElem

        for i in range(self.getLength()):
            jsElem = self.getItem(i)
            if JSValueIsObjectOfClass(self.jsCtx, jsElem, pyObjectClass):
                # This is a wrapped Python object, compare according
                # to Python rules.
                if <object>JSObjectGetPrivate(jsElem) == pyItem:
                    return True
            else:
                # Compare according to JavaScript rules.
                if JSValueIsStrictEqual(self.jsCtx, jsItem, jsElem):
                    return True
        return False

    def __len__(self):
        return self.getLength()

    def __iter__(self):
        return _JSObjectIterator(self)

    def __getitem__(self, pyIndex):
        cdef int index
        cdef int length = self.getLength()

        if isinstance(pyIndex, int) or isinstance(pyIndex, long):
            index = pyIndex

            # Handle negative indexes.
            if index < 0:
                index += length

            # Exclude out-of-range indexes.
            if index < 0 or index >= length:
                raise IndexError, "list index out of range"

            return jsToPython(self.jsCtx, self.getItem(index))
        elif isinstance(pyIndex, slice):
            # Don't know how efficient this is, but it looks cool
            # anyway.
            return [jsToPython(self.jsCtx, self.getItem(i))
                    for i in xrange(*pyIndex.indices(length))]
        else:
            raise TypeError, "list indices must be integers, not %s" % \
                pyIndex.__class__.__name__

    def __setitem__(self, pyKey, pyValue):
        cdef JSValueRef jsValue = pythonToJS(self.jsCtx, pyValue)
        cdef JSValueRef jsException = NULL

        JSObjectSetPropertyAtIndex(self.jsCtx, self.jsObject, pyKey, jsValue,
                                   &jsException)
        if jsException != NULL:
            raise jsExceptionToPython(self.jsCtx, jsException)

    def __delitem__(self, pyKey):
        pass

    def insert(self, pyPos, pyItem):
        pass


class JSObject(_JSObject, collections.MutableSequence):
    """Mix ``_JSObject`` and ``collections.MutableSequence``."""
    __slots__ = ()


cdef makeJSObject(JSContextRef jsCtx, JSObjectRef jsObject):
    """Factory function for 'JSObject' instances."""
    cdef _JSObject obj = JSObject()
    obj.setup(jsCtx, jsObject)
    return obj


cdef class _JSObjectIterator:
    """Iterator class for JavaScript array-like objects."""

    cdef _JSObject pyObj
    cdef int index

    def __init__(self, pyObj):
        self.pyObj = pyObj
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < self.pyObj.getLength():
            value = self.pyObj[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration

    def next(self):
        """Wrap the ``__next__`` method for backwards compatibility.
        """
        return self.__next__()


cdef class JSFunction(_JSObject):
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
            raise jsExceptionToPython(self.jsCtx, jsError)
        return jsToPython(self.jsCtx, result)

cdef makeJSFunction(JSContextRef jsCtx, JSObjectRef jsObject):
    """Factory function for 'JSFunction' instances."""
    cdef JSFunction obj = JSFunction()
    obj.setup(jsCtx, jsObject)
    return obj


cdef class JSBoundMethod(_JSObject):
    """A JavaScript bound method.

    Instances of this class operate in a similar way to Python bound
    methods, but they encapsulate a JavaScript object and
    function. When they are called, the function is called with the
    object as 'this' object."""

    cdef JSObjectRef thisObj 

    cdef setup2(self, JSContextRef jsCtx, JSObjectRef jsObject,
                JSObjectRef thisObj):
        _JSObject.setup(self, jsCtx, jsObject)
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
            raise jsExceptionToPython(self.jsCtx, jsError)
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

    property globalObject:
        """Global object for this context."""

        def __get__(self):
            return jsToPython(self.jsCtx,
                              JSContextGetGlobalObject(self.jsCtx))

    def evaluateScript(self, script, thisObject=None, sourceURL=None,
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
                raise jsExceptionToPython(self.jsCtx, jsException)
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

cdef JSValueRef pyExceptionToJS(JSContextRef jsCtx, object exc):
    """Make a JavaScript exception object from a Python exception
    object."""
    cdef JSStringRef jsMsgStr
    cdef JSValueRef jsMsg

    # Make a string from the exception object (the unicode conversion
    # in createJSStringFromPython takes care of extracting the
    # message).
    jsMsgStr = createJSStringFromPython(exc)
    jsMsg = JSValueMakeString(jsCtx, jsMsgStr)
    JSStringRelease(jsMsgStr)

    return JSObjectMakeError(jsCtx, 1, &jsMsg, NULL)


# PythonObject operations:

cdef bool pyObjHasProperty(JSContextRef jsCtx,
                           JSObjectRef jsObj,
                           JSStringRef jsPropertyName):
    """Invoked to determine if an an object has a property with the
    given name."""
    cdef object pyObj = <object>JSObjectGetPrivate(jsObj)
    cdef object pyPropertyName = pyStringFromJS(jsPropertyName)

    try:
        return hasattr(pyObj, pyPropertyName)
    except BaseException:
        return False

cdef JSValueRef pyObjGetProperty(JSContextRef jsCtx,
                                 JSObjectRef jsObj,
                                 JSStringRef jsPropertyName,
                                 JSValueRef* jsExc) with gil:
    """Invoked to get properties in a wrapped object."""
    cdef object pyObj = <object>JSObjectGetPrivate(jsObj)
    cdef object pyPropertyName = pyStringFromJS(jsPropertyName)

    try:
        return pythonToJS(jsCtx, getattr(pyObj, pyPropertyName))
    except AttributeError:
        # Use the standard JavaScript attribute behavior when
        # attributes can't be found.
        return JSValueMakeUndefined(jsCtx)
    except BaseException, e:
        jsExc[0] = pyExceptionToJS(jsCtx, e)

cdef bool pyObjSetProperty(JSContextRef jsCtx,
                           JSObjectRef jsObj,
                           JSStringRef jsPropertyName,
                           JSValueRef jsValue,
                           JSValueRef* jsExc) with gil:
    """Invoked to set properties in a wrapped object."""
    cdef object pyObj = <object>JSObjectGetPrivate(jsObj)
    cdef object pyPropertyName = pyStringFromJS(jsPropertyName)
    cdef object pyValue = jsToPython(jsCtx, jsValue)

    try:
        setattr(pyObj, pyPropertyName, pyValue)
        return True
    except BaseException, e:
        jsExc[0] = pyExceptionToJS(jsCtx, e)

cdef bool pyObjDeleteProperty(JSContextRef jsCtx,
                              JSObjectRef jsObj,
                              JSStringRef jsPropertyName,
                              JSValueRef* jsExc):
    """Invoked to delete properties in a wrapped object."""
    cdef object pyObj = <object>JSObjectGetPrivate(jsObj)
    cdef object pyPropertyName = pyStringFromJS(jsPropertyName)

    try:
        delattr(pyObj, pyPropertyName)
    except AttributeError:
        pass
    except BaseException, e:
        jsExc[0] = pyExceptionToJS(jsCtx, e)    

    return True

cdef JSValueRef pyObjCallAsFunction(JSContextRef jsCtx,
                                    JSObjectRef jsObj,
                                    JSObjectRef jsThisObj,
                                    size_t argumentCount,
                                    JSValueRef jsArgs[],
                                    JSValueRef* jsExc) with gil:
    """Invoked when a wrapped object is called as a function."""
    cdef object pyObj = <object>JSObjectGetPrivate(jsObj)
    cdef int i

    args = [jsToPython(jsCtx, jsArgs[i])
            for i in range(argumentCount)]
    try:
        return pythonToJS(jsCtx, pyObj(*args))
    except BaseException, e:
        jsExc[0] = pyExceptionToJS(jsCtx, e)

cdef void finalizeCb(JSObjectRef jsObj):
    """Invoked when a wrapper object is garbage-collected."""
    cdef object wrapped = <object>JSObjectGetPrivate(jsObj)
    Py_DECREF(wrapped)

# Initialize the class definition structure for the wrapper objects.
cdef JSClassDefinition pyObjectClassDef = kJSClassDefinitionEmpty
pyObjectClassDef.className = 'PythonObject'
pyObjectClassDef.hasProperty = pyObjHasProperty
pyObjectClassDef.getProperty = pyObjGetProperty
pyObjectClassDef.setProperty = pyObjSetProperty
pyObjectClassDef.deleteProperty = pyObjDeleteProperty
pyObjectClassDef.callAsFunction = pyObjCallAsFunction
pyObjectClassDef.finalize = finalizeCb

# The wrapper object class.
cdef JSClassRef pyObjectClass = JSClassCreate(&pyObjectClassDef)

cdef JSObjectRef makePyObject(JSContextRef jsCtx, object jsObj):
    """Wrap a Python object into a JavaScript object."""
    Py_INCREF(jsObj)
    return JSObjectMake(jsCtx, pyObjectClass, <void *>jsObj)
