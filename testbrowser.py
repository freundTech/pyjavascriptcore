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

import gobject
import gtk
import pango
import webkit

import javascriptcore as jscore


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
        settings.set_property("auto-load-images", False)
        settings.set_property("enable-plugins", False)
        self.connect("load-finished", self.load_finished_cb)

    def show_all(self):
        self.mainWindow.show_all()

    def load_finished_cb(self, view, frame):
        print "load_finished"
        ctx = jscore.JSContext(self.get_main_frame().get_global_context())
        window = ctx.evaluateScript("window")
        #window.alert(None, "window")
        #window.foo = "bar"
        #print ctx.evaluateScript("window.foo")
        document = ctx.evaluateScript("document")
        #print "Title : ", document.title
        #form = document.forms[0]
        #print form.action
        #form.elements[1].value = "this is me"
        #form.elements[2].click(form.elements[2])
        atags = document.getElementsByTagName("a")
        print atags.getPropertyNames()
        for a in atags :
            print a.href

    def start(self):
        self.open("http://www.google.com")


if __name__ == '__main__':
    try:
        gobject.threads_init()
        view = WebView()
        view.show_all()
        view.start()
        gtk.main()
    except KeyboardInterrupt:
        gtk.main_quit()
