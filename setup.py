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

python3 = sys.version_info.major >= 3

name = "pyjavascriptcore3"
modulename = "javascriptcore3"
version = "0.0006"
description = "Javascriptcore-3.0 for Python (for use with webkitgtk-3.0)"
jscoreversion = "javascriptcoregtk-3.0"
basefilename = "py%sjavascriptcore3" % ("3" if python3 else "")
pkgconfig_file = basefilename+".pc"
header_file = basefilename+".h"

def createPcFile(PcFile):
    print("creating %s" % PcFile)
    with open(PcFile, 'w') as fo:
        fo.write("""\
prefix=%s

Name: PyJavaScriptCore3
Description: %s
Version: %s
Requires: %s
Cflags: -I${prefix}/include/pyjavascriptcore
Libs:
""" % (sys.prefix, description, version, jscoreversion)
        )

class custombuild_ext(build_ext):
    def run(self):
        build_ext.run(self)
        if os.path.isfile("pyjavascriptcore_api.h"):
            print("renaming pyjavascriptcore_api.h -> %s" % header_file)
            os.rename("pyjavascriptcore_api.h", header_file)

pkgconfig = subprocess.Popen("pkg-config --cflags %s" % jscoreversion,
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_compile_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

pkgconfig = subprocess.Popen("pkg-config --libs %s" % jscoreversion,
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_link_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

createPcFile(pkgconfig_file)

setup(
    name = name,
    version = version,
    description = description, 
    cmdclass = {'build_ext': custombuild_ext},
    ext_modules = [Extension(modulename, ["pyjavascriptcore.pyx"],
                             extra_compile_args = extra_compile_args,
                             extra_link_args = extra_link_args
                             )],
    data_files = [
        ('include/pyjavascriptcore', [header_file]),
        ('lib/pkgconfig', [pkgconfig_file])
        ]
    )
