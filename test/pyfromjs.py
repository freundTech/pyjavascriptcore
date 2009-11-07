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


class NullUndefTestCase(TestCaseWithContext):
    """Access JavaScript's null and undefined values."""

    def testUndef1(self):
         self.ctx.globalObject.ud = None
         self.assertEqualJS("ud === undefined", True)

    def testNull1(self):
         self.ctx.globalObject.n = jscore.Null
         self.assertEqualJS("n === null", True)


class AttributeAccessTestCase(TestCaseWithContext):
    """Access the attributes of Python objects from JavaScript
    """

    def setUp(self):
        TestCaseWithContext.setUp(self)
        class A: pass
        obj = A()
        obj.a, obj.b, obj.c, obj.d = 1, 'x', A(), None
        obj.c.d, obj.c.e = 2, 'yy'
        self.obj = obj
        self.ctx.globalObject.obj = obj

    def testIntAccess(self):
        self.assertEqualJS('obj.a', 1)

    def testStringAccess(self):
        self.assertEqualJS('obj.b', 'x')

    def testNestedObjectAccess(self):
        self.assertEqualJS('obj.c.d', 2)
        self.assertEqualJS('obj.c.e', 'yy')

    def testAccessInexistent(self):
        self.assertTrueJS('obj.abc === undefined')

    def testAccessNone(self):
        self.assertTrueJS('obj.d === undefined')

    def testAccessChanged(self):
        self.assertEqualJS('obj.a', 1)
        self.obj.a = 4
        self.assertEqualJS('obj.a', 4)

    def testAccessJSNew(self):
        self.obj.f = 4
        self.assertEqualJS('obj.f', 4)

    def testSet(self):
        self.assertEqual(self.obj.a, 1)
        self.ctx.evaluateScript('obj.a = 4')
        self.assertEqual(self.obj.a, 4)

    def testHasOwnProp(self):
        self.assertTrueJS("obj.hasOwnProperty('a')")
        self.assertTrueJS("obj.hasOwnProperty('d')")
        self.assertTrueJS("!obj.hasOwnProperty('abc')")

    def testDelete(self):
        self.assertTrue(hasattr(self.obj, 'a'))
        self.ctx.evaluateScript('delete obj.a')
        self.assertFalse(hasattr(self.obj, 'a'))

    def testDeleteInexistent(self):
        self.assertFalse(hasattr(self.obj, 'abc'))
        self.ctx.evaluateScript('delete obj.abc')
        self.assertFalse(hasattr(self.obj, 'abc'))


class FunctionCallTestCase(TestCaseWithContext):
    """Call Python functions from JavaScript."""

    def testCalculate(self):
        def f(x, y): return x + y
        self.ctx.globalObject.f = f
        self.assertEqualJS('f(7, 9)', 16)

    def testPassReturn(self):
        def f(x): return x
        self.ctx.globalObject.f = f
        self.assertEqualJS('f(34)', 34)
        self.assertAlmostEqualJS('f(3.456)', 3.456)
        self.assertEqualJS("f('xcdf')", 'xcdf')

    def testNumParams(self):
        def f(*args): return len(args)
        self.ctx.globalObject.f = f
        self.assertEqualJS("f()", 0)
        self.assertEqualJS("f('x')", 1)
        self.assertEqualJS("f('x', 'x')", 2)
        self.assertEqualJS("f('x', 'x', 'x')", 3)

    def testExceptionSimple(self):
        def f(): raise Exception('-*Message*-')
        self.ctx.globalObject.f = f
        msg = self.ctx.evaluateScript("""
            try {
                f();
                msg = '';
            } catch (e) {
                msg = e.message;
            }
            msg;
            """)
        self.assertEqual(msg, '-*Message*-')

    def testExceptionRoundTrip(self):
        def f(): raise Exception('-*Message*-')
        self.ctx.globalObject.f = f
        try:
            self.ctx.evaluateScript("f()")
            self.fail("No exception raised")
        except jscore.JSException as e:
            self.assertEqual(str(e), '-*Message*-')
