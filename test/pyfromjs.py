# This file is part of PyJavaScriptCore, a binding between CPython and
# WebKit's JavaScriptCore.
#
# Copyright (C) 2009, Martin Soto <soto@freedesktop.org>
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

import unittest

import javascriptcore as jscore

from base import TestCaseWithContext


class WrapUnwrapTestCase(TestCaseWithContext):
    """Wrap objects and unwrap them again.
    """

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = (1, 2, 3)

    def testWrapUnwrap1(self):
        s = self.ctx.evaluateScript('(function(o) { obj = o; })')
        s(self.obj)
        self.assertTrue(self.obj is self.ctx.globalObject.obj)

    def testWrapUnwrap2(self):
        self.ctx.globalObject.obj = self.obj
        self.assertTrue(self.obj is self.ctx.globalObject.obj)

    def testWrapUnwrap3(self):
        self.ctx.globalObject.obj = self.obj
        g = self.ctx.evaluateScript('(function() { return obj; })')
        self.assertTrue(self.obj is g())

    def testWrapUnwrap4(self):
        self.ctx.globalObject.obj = self.obj
        self.assertTrue(self.obj is self.ctx.evaluateScript('obj'))


class FunctionCallTestCase(TestCaseWithContext):
    """Call Python functions from JavaScript."""

    def testCalculate(self):
        def f(x, y): return x + y
        self.ctx.globalObject.f = f
        self.assertEqual(self.ctx.evaluateScript('f(7, 9)'), 16)

    def testPassReturn(self):
        def f(x): return x
        self.ctx.globalObject.f = f
        self.assertEqual(self.ctx.evaluateScript('f(34)'), 34)
        self.assertAlmostEqual(self.ctx.evaluateScript('f(3.456)'), 3.456)
        self.assertEqual(self.ctx.evaluateScript("f('xcdf')"), 'xcdf')

    def testNumParams(self):
        def f(*args): return len(args)
        self.ctx.globalObject.f = f
        self.assertEqual(self.ctx.evaluateScript("f()"), 0)
        self.assertEqual(self.ctx.evaluateScript("f('x')"), 1)
        self.assertEqual(self.ctx.evaluateScript("f('x', 'x')"), 2)
        self.assertEqual(self.ctx.evaluateScript("f('x', 'x', 'x')"), 3)
