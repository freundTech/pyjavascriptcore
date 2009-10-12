cdef extern from "JavaScriptCore/JSBase.h":
    struct OpaqueJSContextGroup:
        pass
    ctypedef OpaqueJSContextGroup* JSContextGroupRef

    struct OpaqueJSContext:
        pass
    ctypedef OpaqueJSContext* JSContextRef
    ctypedef OpaqueJSContext* JSGlobalContextRef
    
    struct OpaqueJSString:
        pass
    ctypedef OpaqueJSString* JSStringRef
    
    struct OpaqueJSClass:
        pass
    ctypedef OpaqueJSClass* JSClassRef
    
    struct OpaqueJSPropertyNameArray:
        pass
    ctypedef OpaqueJSPropertyNameArray* JSPropertyNameArrayRef
    
    struct OpaqueJSPropertyNameAccumulator:
        pass
    ctypedef OpaqueJSPropertyNameAccumulator* JSPropertyNameAccumulatorRef
    
    struct OpaqueJSValue:
        pass
    ctypedef OpaqueJSValue* JSValueRef
    ctypedef OpaqueJSValue* JSObjectRef
    
    JSValueRef JSEvaluateScript(JSContextRef ctx, JSStringRef script, JSObjectRef thisObject, JSStringRef sourceURL, int startingLineNumber, JSValueRef* exception)
    bool JSCheckScriptSyntax(JSContextRef ctx, JSStringRef script, JSStringRef sourceURL, int startingLineNumber, JSValueRef* exception)
    void JSGarbageCollect(JSContextRef ctx)