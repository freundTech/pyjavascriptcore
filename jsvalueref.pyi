cdef extern from "JavaScriptCore/JSValueRef.h":
    cdef enum JSType :
         kJSTypeUndefined,kJSTypeNull,kJSTypeBoolean,kJSTypeNumber,kJSTypeString,kJSTypeObject
    JSType JSValueGetType(JSContextRef ctx, JSValueRef value)
    bool JSValueToBoolean(JSContextRef ctx, JSValueRef value)
    double JSValueToNumber(JSContextRef ctx, JSValueRef value, JSValueRef* exception)
    JSStringRef JSValueToStringCopy(JSContextRef ctx, JSValueRef value, JSValueRef* exception)
    JSObjectRef JSValueToObject(JSContextRef ctx, JSValueRef value, JSValueRef* exception)
    
    JSValueRef JSValueMakeUndefined(JSContextRef ctx)
    JSValueRef JSValueMakeNull(JSContextRef ctx)
    JSValueRef JSValueMakeBoolean(JSContextRef ctx, bool boolean)
    JSValueRef JSValueMakeNumber(JSContextRef ctx, double number)
    JSValueRef JSValueMakeString(JSContextRef ctx, JSStringRef string)
    void JSValueProtect(JSContextRef ctx, JSValueRef value)
    void JSValueUnprotect(JSContextRef ctx, JSValueRef value)