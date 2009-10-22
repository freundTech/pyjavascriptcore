import gobject
import gtk
import pango
import webkit
import jswebkit


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
        ctx = jswebkit.JSContext(self.get_main_frame().get_global_context())
        window = ctx.EvaluateScript("window")
        document = ctx.EvaluateScript("document")

        clickp = document.getElementById('clickp')
        clickp.addEventListener('click', self.event_cb, False)

    def event_cb(self, event):
        print 'You clicked on (%d, %d)' % (event.x, event.y)

    def start(self):
        self.open("file://test.html")


if __name__ == '__main__':
    try:
        gobject.threads_init()
        view = WebView()
        view.show_all()
        view.start()
        gtk.main()
    except KeyboardInterrupt:
        gtk.main_quit()
