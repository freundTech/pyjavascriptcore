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

import unittest

import javascriptcore as jscore


class TestCaseWithContext(unittest.TestCase):
    """A fixture that creates a JavaScript global context for each
    test method."""

    def setUp(self):
        self.ctx = jscore.JSContext()

    def tearDown(self):
        del self.ctx


class EvaluateScriptTestCase(TestCaseWithContext):
    """Evaluate arbitrary expressions in the JavaScript interpreter.
    """

    def testEvaluateBoolean1(self):
        self.assertTrue(self.ctx.evaluateScript('true') is True)

    def testEvaluateBoolean2(self):
        self.assertTrue(self.ctx.evaluateScript('false') is False)

    def testEvaluateInt1(self):
        self.assertEqual(self.ctx.evaluateScript('3 + 2'), 5)

    def testEvaluateInt2(self):
        program = '(function(x){return x+2;})(3)'
        self.assertEqual(self.ctx.evaluateScript(program), 5)

    def testEvaluateInt3(self):
        program = 'a = 3; a'
        self.assertEqual(self.ctx.evaluateScript(program), 3)

    def testEvaluateString1(self):
        self.assertEqual(self.ctx.evaluateScript('"a"'), 'a')

    def testEvaluateFloat1(self):
        self.assertAlmostEqual(self.ctx.evaluateScript('3.34'), 3.34)

    def testEvaluateObject1(self):
        # Object initializers are not expressions, the parenthesis
        # create an expression, though.
        obj = self.ctx.evaluateScript("""({a: 1, b: 'x'})""")
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, 'x')

    def testEvaluateError(self):
        def code():
            program = '(function(x){return x+2 return})(3)'
            self.assertEqual(self.ctx.evaluateScript(program), 5)

        self.assertRaises(jscore.JSException, code)


class ContextLifeTestCase(unittest.TestCase):
    """Check that the context remains alive when Python still
    references some of its objects.
    """

    def testContextLife(self):
        ctx = jscore.JSContext()
        obj = ctx.evaluateScript("""({a: 1, b: 'x'})""")

        # Release the Python context object.
        del ctx

        # Check that the object is still useful.
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, 'x')

        # Release the object.
        del obj


class AttributeAccessTestCase(TestCaseWithContext):
    """Access the attributes of JavaScript objects from Python
    """

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          obj = {a: 1,
                 b: 'x',
                 c: {d: 2,
                     e: 'yy'}};
          obj;
          """)

    def testIntAccess(self):
        self.assertEqual(self.obj.a, 1)

    def testStringAccess(self):
        self.assertEqual(self.obj.b, 'x')

    def testNestedObjectAccess(self):
        self.assertEqual(self.obj.c.d, 2)
        self.assertEqual(self.obj.c.e, 'yy')

    def testAccessJSChanged(self):
        self.assertEqual(self.obj.a, 1)
        self.ctx.evaluateScript('obj.a = 4')
        self.assertEqual(self.obj.a, 4)

    def testAccessJSNew(self):
        self.ctx.evaluateScript('obj.f = 4')
        self.assertEqual(self.obj.f, 4)

    def testAccessError(self):
        def code():
            print self.obj.abc

        self.assertRaises(AttributeError, code)


class FunctionCallTestCase(TestCaseWithContext):
    """Call JavaScript functions from Python."""

    def testCalculate(self):
        f = self.ctx.evaluateScript('(function(x, y) {return x + y})')
        self.assertEqual(f(7, 9), 16)

    def testPassReturn(self):
        f = self.ctx.evaluateScript('(function(x) {return x})')
        self.assertEqual(f(34), 34)
        self.assertAlmostEqual(f(3.456), 3.456)
        self.assertEqual(f('xcdf'), 'xcdf')

    def testNumParams(self):
        f = self.ctx.evaluateScript('(function() {return arguments.length})')
        self.assertEqual(f(), 0)
        self.assertEqual(f('x'), 1)
        self.assertEqual(f('x', 'x'), 2)
        self.assertEqual(f('x', 'x', 'x'), 3)


class MethodCallTestCase(TestCaseWithContext):
    """Call JavaScript methods from Python."""

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          obj = {a: 1,
                 b: 'x',
                 f: function(x, y) {return x + y},
                 g: function(x) {return x},
                 h: function() {return arguments.length},
                 i: function() {return this.a},
                 j: function() {return this.b},};
          obj;
          """)

    def testCalculate(self):
        self.assertEqual(self.obj.f(7, 9), 16)

    def testPassReturn(self):
        self.assertEqual(self.obj.g(34), 34)
        self.assertAlmostEqual(self.obj.g(3.456), 3.456)
        self.assertEqual(self.obj.g('xcdf'), 'xcdf')

    def testNumParams(self):
        self.assertEqual(self.obj.h(), 0)
        self.assertEqual(self.obj.h('x'), 1)
        self.assertEqual(self.obj.h('x', 'x'), 2)
        self.assertEqual(self.obj.h('x', 'x', 'x'), 3)

    def testThis(self):
        self.assertEqual(self.obj.i(), 1)
        self.assertEqual(self.obj.j(), 'x')

    def testBound(self):
        boundI = self.obj.i
        self.assertEqual(boundI(), 1)
        boundJ = self.obj.j
        self.assertEqual(boundJ(), 'x')


class ArrayTestCase(TestCaseWithContext):
    """Call JavaScript methods from Python."""

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          ([1, 2, 3, 4, 5])
          """)

    def testIterate1(self):
        i = 0
        for elem in self.obj:
            i += 1
        self.assertEqual(i, 5)


if __name__ == '__main__':
    unittest.main()
