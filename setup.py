# This file is part of PyJavaScriptCore, a binding between CPython and
# WebKit's JavaScriptCore.
#
# Copyright (C) 2009, Martin Soto <soto@freedesktop.org>
# Copyright (C) 2009, john paul janecek (see README file)
# Copyright (C) 2016, Adrian Freund
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
Setup file for PyJavaScriptCore. Cython is required to compile the
module.
"""

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import subprocess
import sys
import os

version = "0.0005"
description = "Javascript Core for Python"
python3 = sys.version_info.major >= 3
pkgconfig_file = "py3javascriptcore.pc" if python3 else "pyjavascriptcore.pc"
header_file = "py3javascriptcore.h" if python3 else "pyjavascriptcore.h"

def createPcFile(PcFile):
    print("creating %s" % PcFile)
    with open(PcFile, 'w') as fo:
        fo.write("""\
prefix=%s

Name: PyJavaScriptCore
Description: %s
Version: %s
Requires: webkit2gtk-4.0
Cflags: -I${prefix}/include/pyjavascriptcore
Libs:
""" % (sys.prefix, description, version)
        )

class custombuild_ext(build_ext):
    def run(self):
        build_ext.run(self)
        if os.path.isfile("pyjavascriptcore_api.h"):
            print("renaming pyjavascriptcore_api.h -> %s" % header_file)
            os.rename("pyjavascriptcore_api.h", header_file)

pkgconfig = subprocess.Popen("pkg-config --cflags webkit2gtk-4.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_compile_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

pkgconfig = subprocess.Popen("pkg-config --libs webkit2gtk-4.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_link_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

createPcFile(pkgconfig_file)

setup(
    name = "pyjavascriptcore",
    version = version,
    description = description, 
    cmdclass = {'build_ext': custombuild_ext},
    ext_modules = [Extension("javascriptcore", ["pyjavascriptcore.pyx"],
                             extra_compile_args = extra_compile_args,
                             extra_link_args = extra_link_args
                             )],
    data_files = [
        ('include/pyjavascriptcore', [header_file]),
        ('lib/pkgconfig', [pkgconfig_file])
        ]
    )
