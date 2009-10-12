cdef extern from "JavaScriptCore/JSObjectRef.h":
    enum :
        kJSPropertyAttributeNone,kJSPropertyAttributeReadOnly,
        kJSPropertyAttributeDontEnum,kJSPropertyAttributeDontDelete
    ctypedef unsigned JSPropertyAttributes
    bool JSObjectHasProperty(JSContextRef ctx, JSObjectRef object, JSStringRef propertyName)
    JSValueRef JSObjectGetProperty(JSContextRef ctx, JSObjectRef object, JSStringRef propertyName, JSValueRef* exception)
    void JSObjectSetProperty(JSContextRef ctx, JSObjectRef object, JSStringRef propertyName, JSValueRef value, JSPropertyAttributes attributes, JSValueRef* exception)
    void JSObjectDeleteProperty(JSContextRef ctx, JSObjectRef object, JSStringRef propertyName, JSValueRef* exception)
    JSValueRef JSObjectGetPropertyAtIndex(JSContextRef ctx, JSObjectRef object, unsigned propertyIndex, JSValueRef* exception)
    void JSObjectSetPropertyAtIndex(JSContextRef ctx, JSObjectRef object, unsigned propertyIndex, JSValueRef value, JSValueRef* exception)
    void* JSObjectGetPrivate(JSObjectRef object)
    bool JSObjectSetPrivate(JSObjectRef object, void* data)
    bool JSObjectIsFunction(JSContextRef ctx, JSObjectRef object)
    JSValueRef JSObjectCallAsFunction(JSContextRef ctx, JSObjectRef object, JSObjectRef thisObject, size_t argumentCount,JSValueRef arguments[], JSValueRef* exception)
    JSObjectIsConstructor(JSContextRef ctx, JSObjectRef object)
    JSPropertyNameArrayRef JSObjectCopyPropertyNames(JSContextRef ctx, JSObjectRef object)
    JSPropertyNameArrayRef JSPropertyNameArrayRetain(JSPropertyNameArrayRef array)
    void JSPropertyNameArrayRelease(JSPropertyNameArrayRef array)
    size_t JSPropertyNameArrayGetCount(JSPropertyNameArrayRef array)
    JSStringRef JSPropertyNameArrayGetNameAtIndex(JSPropertyNameArrayRef array, size_t index)
    void JSPropertyNameAccumulatorAddName(JSPropertyNameAccumulatorRef accumulator, JSStringRef propertyName)