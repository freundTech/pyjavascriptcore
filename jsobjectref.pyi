cdef extern from "JavaScriptCore/JSObjectRef.h":
    enum :
        kJSPropertyAttributeNone, kJSPropertyAttributeReadOnly, 
        kJSPropertyAttributeDontEnum, kJSPropertyAttributeDontDelete
    ctypedef unsigned JSPropertyAttributes

    ctypedef struct JSClassDefinition

    JSClassRef JSClassCreate(JSClassDefinition* definition)


    bool JSObjectHasProperty(JSContextRef ctx, JSObjectRef object,
                             JSStringRef propertyName)
    JSValueRef JSObjectGetProperty(JSContextRef ctx, JSObjectRef object,
                                   JSStringRef propertyName,
                                   JSValueRef* exception)
    void JSObjectSetProperty(JSContextRef ctx, JSObjectRef object,
                             JSStringRef propertyName, JSValueRef value,
                             JSPropertyAttributes attributes,
                             JSValueRef* exception)
    void JSObjectDeleteProperty(JSContextRef ctx, JSObjectRef object,
                                JSStringRef propertyName,
                                JSValueRef* exception)
    JSValueRef JSObjectGetPropertyAtIndex(JSContextRef ctx,
                                          JSObjectRef object,
                                          unsigned propertyIndex,
                                          JSValueRef* exception)
    void JSObjectSetPropertyAtIndex(JSContextRef ctx, JSObjectRef object,
                                    unsigned propertyIndex,
                                    JSValueRef value, JSValueRef* exception)
    void* JSObjectGetPrivate(JSObjectRef object)
    bool JSObjectSetPrivate(JSObjectRef object, void* data)
    bool JSObjectIsFunction(JSContextRef ctx, JSObjectRef object)
    JSValueRef JSObjectCallAsFunction(JSContextRef ctx, JSObjectRef object,
                                      JSObjectRef thisObject,
                                      size_t argumentCount,
                                      JSValueRef arguments[],
                                      JSValueRef* exception)
    JSObjectIsConstructor(JSContextRef ctx, JSObjectRef object)
    JSPropertyNameArrayRef JSObjectCopyPropertyNames(JSContextRef ctx,
                                                     JSObjectRef object)
    JSPropertyNameArrayRef JSPropertyNameArrayRetain(
        JSPropertyNameArrayRef array)
    void JSPropertyNameArrayRelease(JSPropertyNameArrayRef array)
    size_t JSPropertyNameArrayGetCount(JSPropertyNameArrayRef array)
    JSStringRef JSPropertyNameArrayGetNameAtIndex(
        JSPropertyNameArrayRef array, size_t index)
    void JSPropertyNameAccumulatorAddName(
        JSPropertyNameAccumulatorRef accumulator, JSStringRef propertyName)


    ctypedef unsigned JSClassAttributes

    ctypedef void (*JSObjectInitializeCallback) (
        JSContextRef ctx, JSObjectRef object)

    ctypedef void (*JSObjectFinalizeCallback) (JSObjectRef object)

    ctypedef bool (*JSObjectHasPropertyCallback) (
        JSContextRef ctx, JSObjectRef object, JSStringRef propertyName)

    ctypedef JSValueRef (*JSObjectGetPropertyCallback) (
        JSContextRef ctx, JSObjectRef object, JSStringRef propertyName,
        JSValueRef* exception)

    ctypedef bool (*JSObjectSetPropertyCallback) (
        JSContextRef ctx, JSObjectRef object, JSStringRef propertyName,
        JSValueRef value, JSValueRef* exception)

    ctypedef bool (*JSObjectDeletePropertyCallback) (
        JSContextRef ctx, JSObjectRef object, JSStringRef propertyName,
        JSValueRef* exception)

    ctypedef void (*JSObjectGetPropertyNamesCallback) (
        JSContextRef ctx, JSObjectRef object,
        JSPropertyNameAccumulatorRef propertyNames)

    ctypedef JSValueRef (*JSObjectCallAsFunctionCallback) (
        JSContextRef ctx, JSObjectRef function, JSObjectRef thisObject,
        size_t argumentCount, JSValueRef arguments[], JSValueRef* exception)

    ctypedef JSObjectRef (*JSObjectCallAsConstructorCallback) (
        JSContextRef ctx, JSObjectRef constructor, size_t argumentCount,
        JSValueRef arguments[], JSValueRef* exception)

    ctypedef bool (*JSObjectHasInstanceCallback)  (
        JSContextRef ctx, JSObjectRef constructor,
        JSValueRef possibleInstance, JSValueRef* exception)

    ctypedef JSValueRef (*JSObjectConvertToTypeCallback) (
        JSContextRef ctx, JSObjectRef object, JSType type,
        JSValueRef* exception)

    ctypedef struct JSStaticFunction:
        char* name
        JSObjectCallAsFunctionCallback callAsFunction
        JSPropertyAttributes attributes

    ctypedef struct JSStaticValue:
        char* name
        JSObjectGetPropertyCallback getProperty
        JSObjectSetPropertyCallback setProperty
        JSPropertyAttributes attributes

    ctypedef struct JSClassDefinition:
        int version # current (and only) version is 0
        JSClassAttributes attributes

        char* className
        JSClassRef parentClass
 
        JSStaticValue* staticValues
        JSStaticFunction* staticFunctions
 
        JSObjectInitializeCallback initialize
        JSObjectFinalizeCallback finalize
        JSObjectHasPropertyCallback hasProperty
        JSObjectGetPropertyCallback getProperty
        JSObjectSetPropertyCallback setProperty
        JSObjectDeletePropertyCallback deleteProperty
        JSObjectGetPropertyNamesCallback getPropertyNames
        JSObjectCallAsFunctionCallback callAsFunction
        JSObjectCallAsConstructorCallback callAsConstructor
        JSObjectHasInstanceCallback hasInstance
        JSObjectConvertToTypeCallback convertToType

    JSClassDefinition kJSClassDefinitionEmpty

    JSObjectRef JSObjectMake(
        JSContextRef ctx,
        JSClassRef jsClass,
        void *data)

    JSObjectRef JSObjectMakeFunctionWithCallback(
        JSContextRef ctx,
        JSStringRef name,
        JSObjectCallAsFunctionCallback callAsFunction)
