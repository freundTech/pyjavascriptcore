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

"""
Setup file for PyJavaScriptCore. Cython is required to compile the
module.
"""

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import subprocess
import sys

version = "0.0005"
description = "Javascript Core for Python"
pkgconfig_file = "pyjavascriptcore.pc"

def createPcFile(PcFile):
    print("creating %s" % PcFile)
    with open(PcFile, 'w') as fo:
        fo.write("""\
prefix=%s

Name: PyJavaScriptCore
Description: %s
Version: %s
Requires: webkit-1.0
Cflags: -I${prefix}/include/pyjavascriptcore
Libs:
""" % (sys.prefix, description, version)
        )

pkgconfig = subprocess.Popen("pkg-config --cflags webkit-1.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_compile_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

pkgconfig = subprocess.Popen("pkg-config --libs webkit-1.0",
                             stdout=subprocess.PIPE, shell=True)
pkgconfig.wait()
extra_link_args = [s.decode("utf-8") for s in pkgconfig.stdout.read().split()]

createPcFile(pkgconfig_file)

setup(
    name = "pyjavascriptcore",
    version = version,
    description = description, 
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("javascriptcore", ["pyjavascriptcore.pyx"],
                             extra_compile_args = extra_compile_args,
                             extra_link_args = extra_link_args
                             )],
    data_files = [
        ('include/pyjavascriptcore', ['pyjavascriptcore.h']),
        ('lib/pkgconfig', [pkgconfig_file])
        ]
    )
