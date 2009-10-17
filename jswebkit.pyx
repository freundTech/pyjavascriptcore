"""
version 0.0003
Applied the patches supplied by MonkeeSage Thanx :)
This fixes the ucs2/ucs4 bug which I had earlier
Also MonkeeSage fixed other things, he make call function nicer and fixed lists so the work properly
Also fixed his patch so it works with both ucs2/ucs4 python
Fixed the setup.py so that it can use pkg-config instead

version 0.0002
I need a versioning system lol
cython wrapper for JSContextRef in pywebkitgtk
you need cython to make it
So you can call Javascript functions etc from python
Made by john paul janecek
Free Beer copyright, do what the heck you want with it, just give me credit
Also do not blame me if your things blow up
if you need to contact me, i might answer back :) I am lazy when it comes to making fixes
unless I actually am using library myself :)

my email
import binascii
binascii.a2b_base64('anBqYW5lY2VrQGdtYWlsLmNvbQ==\n')
"""

import sys
import types
cdef:
    ctypedef unsigned short bool

include "stdlib.pyi"
include "python.pyi"
include "jsbase.pyi"
include "jsstringref.pyi"
include "jsvalueref.pyi"
include "jsobjectref.pyi"


cdef object jsValueToPython(JSContextRef ctx, JSValueRef jsValue):
    cdef JSStringRef jsStr
    cdef int jsType = JSValueGetType(ctx, jsValue)
    cdef JSObject jsObject
    cdef JSFunction jsFunction
    cdef object result
    cdef int isFunction
    cdef bool bResult
    cdef size_t strlen
    if jsType == kJSTypeUndefined or jsType == kJSTypeNull:
        JSValueUnprotect(ctx, jsValue)
        return None
    elif jsType == kJSTypeBoolean:
        bResult = JSValueToBoolean(ctx, jsValue)
        JSValueUnprotect(ctx, jsValue)
        if bResult > 0:
            return True
        else:
            return False
    elif jsType == kJSTypeNumber:
        result = JSValueToNumber(ctx, jsValue, NULL)
        JSValueUnprotect(ctx, jsValue)
        return result
    elif jsType == kJSTypeString:
        jsStr = JSValueToStringCopy(ctx, jsValue, NULL)
        strlen = JSStringGetLength(jsStr)
        strlen *= 2
        result = PyUnicode_DecodeUTF16(JSStringGetCharactersPtr(jsStr),
                                       strlen, NULL, 0)
        JSStringRelease(jsStr)
        JSValueUnprotect(ctx, jsValue)
        return result
    else:
        if JSObjectIsFunction(ctx, jsValue) > 0:
            jsFunction = JSFunction()
            jsFunction.setup(ctx, jsValue)
            return jsFunction
        else:
            jsObject = JSObject()
            jsObject.setup(ctx, jsValue)
            return jsObject
    return None


class JSException(Exception):
    def __init__(self, name, message):
        self.name = name
        self.mess = message

    def __str__(self):
        return "JSException name: %s message: %s" % (self.name, self.mess)


cdef object makeException(JSContextRef ctx, JSValueRef jsException):
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
    elif isinstance(pyValue, JSCallable):
        return (<JSCallable>pyValue).jsFunction
    else:
        raise ValueError

cdef class JSObject:
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

        try:
            self.propertyNames[name]
            jsStr = JSStringCreateWithUTF8CString(name) #has to be a UTF8 string
            result = jsValueToPython(self.ctx,
                                     JSObjectGetProperty(self.ctx,
                                                         self.jsObject,
                                                         jsStr, NULL))
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

    def __del__(self):
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


cdef class JSFunction(JSObject):
    def __init__(self):
        JSObject.__init__(self)

    def __call__(self, thisObj, *args):
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
        if thisObj:
            jsThisObject = (<JSObject>thisObj).jsObject
        else:
            jsThisObject = NULL
        result = JSObjectCallAsFunction(self.ctx, self.jsObject,
                                        jsThisObject, len(args), jsArgs,
                                        &jsError)
        free(jsArgs)
        if jsError != NULL:
            raise makeException(self.ctx, jsError)
        return jsValueToPython(self.ctx, result)


cdef class JSContext:
    cdef JSContextRef jsCtx
    cdef object ctx

    def __init__(self, ctx):
        self.ctx = ctx
        self.jsCtx = <JSContextRef>PyCObject_AsVoidPtr(ctx)

    def EvaluateScript(self, script, thisObject = None , sourceURL = None,
                       startingLineNumber = 1):
        script = unicode(script).encode("utf-8")
        cdef JSStringRef jsScript = \
            JSStringCreateWithUTF8CString(PyString_AsString(script))
        cdef JSValueRef jsException = NULL
        cdef JSValueRef jsValue = JSEvaluateScript(self.jsCtx, jsScript,
                                                   <JSObjectRef>NULL,
                                                   <JSStringRef>NULL,
                                                   startingLineNumber,
                                                   &jsException)
        JSValueProtect(self.jsCtx, jsValue)
        JSStringRelease(jsScript)
        if jsException != NULL:
            raise makeException(self.jsCtx, jsException)
        return jsValueToPython(self.jsCtx, jsValue)

    def getCtx(self):
        return self.ctx


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
    # send them to the back to the JS interpreter.

cdef void finalizeCb(JSObjectRef function):
    cdef object wrapped = <object>JSObjectGetPrivate(function)
    Py_DECREF(wrapped)

cdef JSClassDefinition callableClassDef = kJSClassDefinitionEmpty
callableClassDef.callAsFunction = callableCb
callableClassDef.finalize = finalizeCb
cdef JSClassRef callableClass = JSClassCreate(&callableClassDef)

cdef class JSCallable:
    """A wrapper for Python callable objects that makes them callable
    from JavaScript.

    This is useful for attaching Python code as a callback to
    JavaScript objects."""

    cdef object wrapped
    cdef JSObjectRef jsFunction

    def __init__(self, wrapped, ctx):
        self.wrapped = wrapped

        if not isinstance(ctx, JSContext):
            raise TypeError, "ctx must be a JSContext"
        cdef JSContextRef jsCtx = (<JSContext>ctx).jsCtx

        Py_INCREF(wrapped)
        self.jsFunction = JSObjectMake(jsCtx, callableClass,
                                       <void *>wrapped)
