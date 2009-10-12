"""
test file for cython wrapper for JSContextRef in pywebkitgtk
This is the documentation :)
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

import gobject
import gtk
import pango
import webkit
import jswebkit
import signal

gobject.threads_init()

class WebView(webkit.WebView):
    def __init__(self):
        webkit.WebView.__init__(self)
        self.mainWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.mainWindow.connect("delete_event", lambda *x: gtk.main_quit ())
        self.mainWindow.set_size_request(800, 600)
        self.scrolledWindow = gtk.ScrolledWindow()
        self.mainWindow.add(self.scrolledWindow)
        self.scrolledWindow.add(self)
        settings = self.get_settings()
        settings.set_property("auto-load-images",False)
        settings.set_property("enable-plugins",False)
        self.connect("load-finished",self.load_finished_cb)
        
    def show_all(self):
        self.mainWindow.show_all()

    def load_finished_cb(self,view,frame):
        print "load_finished"
        ctx = jswebkit.JSContext(self.get_main_frame().get_global_context())
        window = ctx.EvaluateScript("window")
        #window.alert(None, "window")
        #window.foo = "bar"
        #print ctx.EvaluateScript("window.foo")
        document = ctx.EvaluateScript("document")
        #print "Title : ",document.title
        #form = document.forms[0]
        #print form.action
        #form.elements[1].value = "this is me"
        #form.elements[2].click(form.elements[2])
        atags = document.getElementsByTagName(document, "a")
        print atags.getPropertyNames()
        for a in atags :
            print a.href
        
    def start(self):
        self.open("http://www.google.com")
        
try:
    view = WebView()
    view.show_all()
    view.start()
    gtk.main()
except KeyboardInterrupt:
    gtk.main_quit()

