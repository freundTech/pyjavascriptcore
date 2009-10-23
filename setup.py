"""
setup file for cython wrapper for JSContextRef in pywebkitgtk
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

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import subprocess

pkgconfig = subprocess.Popen("pkg-config --cflags webkit-1.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_compile_args = pkgconfig.stdout.read().split()

pkgconfig = subprocess.Popen("pkg-config --libs webkit-1.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_link_args = pkgconfig.stdout.read().split()

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("javascriptcore", ["javascriptcore.pyx"],
                             extra_compile_args = extra_compile_args,
                             extra_link_args = extra_link_args
                             )]
    )
