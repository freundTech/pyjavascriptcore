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


class GlobalObjectTestCase(TestCaseWithContext):
    """Access JavaScript objects directly through the context's global
    object."""

    def testAccess1(self):
        self.ctx.evaluateScript("""
          a = 1;
          b = 'x';
          c = 2.3;
          """)
        self.assertEqual(self.ctx.globalObject.a, 1)
        self.assertEqual(self.ctx.globalObject.b, 'x')
        self.assertAlmostEqual(self.ctx.globalObject.c, 2.3)

    def assertNoVariable(self, varName):
        def evalVar(): self.ctx.evaluateScript(varName)
        self.assertRaises(jscore.JSException, evalVar)

    def testAccess2(self):
        self.assertNoVariable('a')
        self.assertNoVariable('b')
        self.assertNoVariable('c')
        self.ctx.globalObject.a = 1
        self.ctx.globalObject.b = 'x'
        self.ctx.globalObject.c = 2.3
        self.assertEqual(self.ctx.evaluateScript('a'), 1)
        self.assertEqual(self.ctx.evaluateScript('b'), 'x')
        self.assertAlmostEqual(self.ctx.evaluateScript('c'), 2.3)


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

    def testEvaluateError1(self):
        def code():
            program = '(function(x){return x+2 return})(3)'
            self.assertEqual(self.ctx.evaluateScript(program), 5)

        self.assertRaises(jscore.JSException, code)

    def testEvaluateError2(self):
        def code():
            self.ctx.evaluateScript('throw Error("Message");')

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


class WrapUnwrapTestCase(TestCaseWithContext):
    """Wrap objects and unwrap them again.
    """

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          obj = {a: 1, b: 'x'};
          obj;
          """)

    def testWrapUnwrap1(self):
        self.ctx.globalObject.obj2 = self.obj
        self.assertTrue(self.ctx.evaluateScript('obj === obj2'))

    def testWrapUnwrap2(self):
        self.ctx.globalObject.obj2 = self.ctx.globalObject.obj
        self.assertTrue(self.ctx.evaluateScript('obj === obj2'))


class NullUndefTestCase(TestCaseWithContext):
    """Access JavaScript's null and undefined values."""

    def testUndef1(self):
        self.assertTrue(self.ctx.evaluateScript('undefined') is None)

    def testUndef2(self):
        """JavaScript functions without a return  produce None in Python."""
        self.assertTrue(self.ctx.evaluateScript('(function(){})()') is None)

    def testNull1(self):
        self.assertTrue(self.ctx.evaluateScript('null') is jscore.Null)

    def testNull2(self):
        """Null is false."""
        self.assertFalse(self.ctx.evaluateScript('null'))

    def testNull3(self):
        """Null is a singleton."""
        def code():
            n = type(jscore.Null)()

        self.assertRaises(TypeError, code)


class AttributeAccessTestCase(TestCaseWithContext):
    """Access the attributes of JavaScript objects from Python
    """

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          obj = {a: 1,
                 b: 'x',
                 c: {d: 2,
                     e: 'yy'},
                 d: undefined};
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

    def testAccessUndef(self):
        self.assertTrue(self.obj.d is None)

    def testHasattr(self):
        self.assertTrue(hasattr(self.obj, 'a'))
        self.assertTrue(hasattr(self.obj, 'd'))
        self.assertFalse(hasattr(self.obj, 'abc'))

    def testDel(self):
        self.assertTrueJS("obj.hasOwnProperty('a')")
        del self.obj.a
        self.assertTrueJS("!obj.hasOwnProperty('a')")

    def testDelError(self):
        def code():
            del self.obj.abc

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

    def testException(self):
        f = self.ctx.evaluateScript('(function() {throw Error("Message");})')
        self.assertRaises(jscore.JSException, f)


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
                 j: function() {return this.b},
                 k: function() {throw Error('Message')},
                };
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

    def testException(self):
        self.assertRaises(jscore.JSException, self.obj.k)


class ArrayTestCase(TestCaseWithContext):
    """Work with JavaScript array-like objects from Python."""

    def setUp(self):
        TestCaseWithContext.setUp(self)
        self.obj = self.ctx.evaluateScript("""
          ([1, 2, 3, 4, 5])
          """)

    def testLen1(self):
        self.assertEqual(len(self.obj), 5)

    def testIndexing1(self):
        self.assertEqual(self.obj[0], 1)
        self.assertEqual(self.obj[2], 3)
        self.assertEqual(self.obj[4], 5)

    def xtestIndexing2(self):
        # TODO: Raise exceptions when JavaScript returns 'undefined'.
        def get(): return self.obj[6]
        self.assertRaises(get, Exception)

    def testIndexing3(self):
        self.obj[0] = 10
        self.obj[2] = 20
        self.obj[4] = 40
        self.assertEqual(self.obj[0], 10)
        self.assertEqual(self.obj[2], 20)
        self.assertEqual(self.obj[4], 40)
        self.assertEqual(len(self.obj), 5)

    def testIterate1(self):
        i = 0
        for elem in self.obj:
            i += 1
        self.assertEqual(i, 5)

    def testIterate2(self):
        i = 0
        for elem1 in self.obj:
            for elem2 in self.obj:
                i += 1
        self.assertEqual(i, 25)

    def testIterate3(self):
        itr1 = iter(self.obj)
        itr2 = iter(self.obj)

        def next1(): return itr1.next()
        def next2(): return itr2.next()

        self.assertEqual(next1(), 1)
        self.assertEqual(next1(), 2)
        self.assertEqual(next2(), 1)
        self.assertEqual(next1(), 3)
        self.assertEqual(next2(), 2)
        self.assertEqual(next2(), 3)
        self.assertEqual(next2(), 4)
        self.assertEqual(next1(), 4)
        self.assertEqual(next1(), 5)
        self.assertRaises(StopIteration, next1)
        self.assertEqual(next2(), 5)
        self.assertRaises(StopIteration, next2)

    def testContains1(self):
        self.assertTrue(1 in self.obj)
        self.assertTrue(3 in self.obj)
        self.assertTrue(5 in self.obj)

    def testContains2(self):
        self.assertFalse(0 in self.obj)
        self.assertFalse('x' in self.obj)

    def testContains3(self):
        self.assertFalse(None in self.obj)

    def testContains4(self):
        obj =  self.ctx.evaluateScript("""
          (['a', 'b', 'c', 'd', 'e'])
          """)
        self.assertTrue('a' in obj)
        self.assertTrue('c' in obj)
        self.assertTrue('e' in obj)
        self.assertFalse('f' in obj)
        self.assertFalse(1 in obj)
        self.assertFalse(None in obj)

    def testContains5(self):
        obj =  self.ctx.evaluateScript("""[]""")
        self.assertFalse('f' in obj)
        self.assertFalse(1 in obj)
        self.assertFalse(None in obj)

    def testContains6(self):
        class A(object):
            pass
        a = A()
        self.assertFalse(a in self.obj)
        self.obj[2] = a
        self.assertTrue(a in self.obj)

