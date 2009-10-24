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

cdef object jsValueToPython(JSContextRef ctx, JSValueRef jsValue):
    """Convert a JavaScript value into a Python value."""

    cdef JSStringRef jsStr
    cdef int jsType = JSValueGetType(ctx, jsValue)
    cdef object result
    cdef int isFunction
    cdef bool bResult
    cdef size_t strlen

    if jsType == kJSTypeUndefined or jsType == kJSTypeNull:
        return None
    elif jsType == kJSTypeBoolean:
        bResult = JSValueToBoolean(ctx, jsValue)
        if bResult:
            return True
        else:
            return False
    elif jsType == kJSTypeNumber:
        result = JSValueToNumber(ctx, jsValue, NULL)
        return result
    elif jsType == kJSTypeString:
        jsStr = JSValueToStringCopy(ctx, jsValue, NULL)
        strlen = JSStringGetLength(jsStr) * 2
        result = PyUnicode_DecodeUTF16(JSStringGetCharactersPtr(jsStr),
                                       strlen, NULL, 0)
        JSStringRelease(jsStr)
        return result
    elif JSObjectIsFunction(ctx, jsValue) > 0:
        return makeJSFunction(ctx, jsValue)
    else:
        return makeJSObject(ctx, jsValue)

    return None


class JSException(Exception):
    """Python exception class to encapsulate JavaScript exceptions."""

    def __init__(self, name, message):
        self.name = name
        self.mess = message

    def __str__(self):
        return "JSException name: %s message: %s" % (self.name, self.mess)

cdef object makeException(JSContextRef ctx, JSValueRef jsException):
    """Factory function for creating exception objects."""
    e = jsValueToPython(ctx, jsException)
    return JSException(e.name, e.message)


cdef object JSStringRefToPython(JSStringRef jsString):
    cdef size_t strlen = JSStringGetLength(jsString)

    strlen *= 2
    result = PyUnicode_DecodeUTF16(JSStringGetCharactersPtr(jsString),
                                   strlen, NULL, 0)
    return result

cdef JSStringRef pythonToJSString(object pyStr):
    """result has to be released"""
    pyStr = unicode(pyStr).encode("utf-8")
    cdef JSStringRef jsStr = JSStringCreateWithUTF8CString(
        PyString_AsString(pyStr))
    return jsStr

cdef JSValueRef pythonTojsValue(JSContextRef ctx, object pyValue):
    """Convert a Python value into a JavaScript value."""

    if isinstance(pyValue, types.NoneType):
        return JSValueMakeNull(ctx)
    elif isinstance(pyValue, types.BooleanType):
        return JSValueMakeBoolean(ctx, pyValue)
    elif isinstance(pyValue, (types.IntType, types.FloatType)):
        return JSValueMakeNumber(ctx, pyValue)
    elif isinstance(pyValue, types.StringTypes):
        return JSValueMakeString(ctx, pythonToJSString(pyValue))
    elif isinstance(pyValue, JSObject):
        return (<JSObject>pyValue).jsObject
    elif callable(pyValue):
        return makePyFunction(ctx, pyValue)
    else:
        raise ValueError


#
# Python Wrappers for JavaScript objects
#

cdef class JSObject:
    """Wrapper class to make JavaScript objects accessible from Python."""

    cdef JSContextRef ctx
    cdef JSObjectRef jsObject
    cdef object propertyNames
    cdef int index

    def __init__(self):
        self.ctx = NULL
        self.jsObject = NULL
        self.index = 0

    cdef setup(self, JSContextRef ctx, JSObjectRef jsObject):
        self.ctx = ctx
        # __dealloc__ unprotects the JSObject, so that it's guaranteed
        # to exist as long as this object exists.
        JSValueProtect(self.ctx, jsObject)
        self.jsObject = jsObject
        self.propertyNames = dict.fromkeys(self.getPropertyNames(), True)

    def getPropertyNames(self):
        cdef JSPropertyNameArrayRef nameArray = \
            JSObjectCopyPropertyNames(self.ctx, self.jsObject)

        names = []
        for i in range(JSPropertyNameArrayGetCount(nameArray)):
            names.append(JSStringRefToPython(
                    JSPropertyNameArrayGetNameAtIndex(nameArray, i)))
        JSPropertyNameArrayRelease(nameArray)
        return names

    def __getattr__(self, name):
        cdef JSStringRef jsStr
        cdef JSValueRef jsException
        cdef JSValueRef jsResult

        try:
            self.propertyNames[name]
            jsStr = JSStringCreateWithUTF8CString(name) #has to be a UTF8 string
            jsResult = JSObjectGetProperty(self.ctx, self.jsObject,
                                           jsStr, NULL)
            if JSObjectIsFunction(self.ctx, jsResult):
                result = makeJSBoundMethod(self.ctx, jsResult,
                                           self.jsObject)
            else:
                result = jsValueToPython(self.ctx, jsResult)
            JSStringRelease(jsStr)
            return result
        except KeyError:
            raise AttributeError, name

    def __setattr__(self, name, value):
        cdef JSStringRef jsStr

        self.propertyNames[name] = True
        jsStr = JSStringCreateWithUTF8CString(name) #has to be a UTF8 string
        JSObjectSetProperty(self.ctx, self.jsObject, jsStr,
                            pythonTojsValue(self.ctx, value),
                            kJSPropertyAttributeNone, NULL)
        JSStringRelease(jsStr)

    def __getitem__(self, key):
        cdef JSValueRef jsValueRef
        cdef JSValueRef jsException = NULL

        jsValueRef = JSObjectGetPropertyAtIndex(self.ctx, self.jsObject,
                                                key, &jsException)
        if jsException != NULL:
            raise makeException(self.ctx, jsException)
        return jsValueToPython(self.ctx, jsValueRef)

    def __setitem__(self, key, value):
        cdef JSValueRef jsValue = pythonTojsValue(self.ctx, value)
        cdef JSValueRef jsException = NULL

        JSObjectSetPropertyAtIndex(self.ctx, self.jsObject, key, jsValue,
                                   &jsException)
        if jsException != NULL:
            raise makeException(self.ctx, jsException)

    def __dealloc__(self):
        JSValueUnprotect(self.ctx, self.jsObject)

    # these are container methods, so that lists behave correctly
    def __iter__(self):
        return self

    def __next__(self): # 2.6 and 3.0 now use __next__
        if self.index < self.length:
            value = self[self.index]
            self.index += 1
            return value
        else:
            self.index = 0
            raise StopIteration

    def next(self): # wrapper for backwards compatibility
        return self.__next__()

    def __len__(self):
        length = len(self.getPropertyNames())
        if hasattr(self, "length"):
            length += int(self.length)
        return length

cdef makeJSObject(JSContextRef ctx, JSObjectRef jsObject):
    """Factory function for 'JSObject' instances."""
    cdef JSObject obj = JSObject()
    obj.setup(ctx, jsObject)
    return obj


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
            jsArgs[i] = pythonTojsValue(self.ctx, arg)
        result = JSObjectCallAsFunction(self.ctx, self.jsObject,
                                        NULL, len(args), jsArgs,
                                        &jsError)
        free(jsArgs)
        if jsError != NULL:
            raise makeException(self.ctx, jsError)
        return jsValueToPython(self.ctx, result)

cdef makeJSFunction(JSContextRef ctx, JSObjectRef jsObject):
    """Factory function for 'JSFunction' instances."""
    cdef JSFunction obj = JSFunction()
    obj.setup(ctx, jsObject)
    return obj


cdef class JSBoundMethod(JSObject):
    """A JavaScript bound method.

    Instances of this class operate in a similar way to Python bound
    methods, but they encapsulate a JavaScript object and
    function. When they are called, the function is called with the
    object as 'this' object."""

    cdef JSObjectRef thisObj 

    cdef setup2(self, JSContextRef ctx, JSObjectRef jsObject,
                JSObjectRef thisObj):
        JSObject.setup(self, ctx, jsObject)
        # __dealloc__ unprotects thisObj, so that it's guaranteed to
        # exist as long as this object exists.
        JSValueProtect(ctx, thisObj)
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
            jsArgs[i] = pythonTojsValue(self.ctx, arg)
        result = JSObjectCallAsFunction(self.ctx, self.jsObject,
                                        self.thisObj, len(args), jsArgs,
                                        &jsError)
        free(jsArgs)
        if jsError != NULL:
            raise makeException(self.ctx, jsError)
        return jsValueToPython(self.ctx, result)

    def __dealloc__(self):
        JSValueUnprotect(self.ctx, self.thisObj)

cdef makeJSBoundMethod(JSContextRef ctx, JSObjectRef jsObject,
                       JSObjectRef thisObj):
    """Factory function for 'JSBoundMethod' instances."""
    cdef JSBoundMethod obj = JSBoundMethod()
    obj.setup2(ctx, jsObject, thisObj)
    return obj


cdef class JSContext:
    """Wrapper class for JavaScriptCore context objects.

    Call the constructor without arguments to obtain a new default
    context that can be used to execute JavaScript but that will not
    provide any access to a DOM or any other browser-specific objects.

    A context obtained from another object (e.g. a WebKit browser
    component can also be passed to the constructor in order to gaina
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
        script = unicode(script).encode("utf-8")
        cdef JSStringRef jsScript = \
            JSStringCreateWithUTF8CString(PyString_AsString(script))
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsValue = JSEvaluateScript(self.jsCtx, jsScript,
                                                   <JSObjectRef>NULL,
                                                   <JSStringRef>NULL,
                                                   startingLineNumber,
                                                   &jsException)
        JSStringRelease(jsScript)
        if jsException != NULL:
            raise makeException(self.jsCtx, jsException)
        return jsValueToPython(self.jsCtx, jsValue)

    def getCtx(self):
        return self.pyCtxExtern

    def __dealloc__(self):
        JSGlobalContextRelease(self.jsCtx)


#
# JavaScript Wrappers for Python Objects
#

cdef JSValueRef callableCb(JSContextRef ctx, JSObjectRef function,
                           JSObjectRef thisObject, size_t argumentCount,
                           JSValueRef arguments[],
                           JSValueRef* exception) with gil:
    cdef object wrapped = <object>JSObjectGetPrivate(function)
    cdef int i

    args = [jsValueToPython(ctx, arguments[i])
            for i in range(argumentCount)]
    return pythonTojsValue(ctx, wrapped(*args))
    # TODO: Trap Python exceptions, wrap them into JS exceptions and
    # send them back to the JS interpreter.

cdef void finalizeCb(JSObjectRef function):
    cdef object wrapped = <object>JSObjectGetPrivate(function)
    Py_DECREF(wrapped)

cdef JSClassDefinition callableClassDef = kJSClassDefinitionEmpty
callableClassDef.callAsFunction = callableCb
callableClassDef.finalize = finalizeCb
cdef JSClassRef callableClass = JSClassCreate(&callableClassDef)

cdef JSObjectRef makePyFunction(JSContextRef ctx, object function):
        Py_INCREF(function)
        return JSObjectMake(ctx, callableClass, <void *>function)
