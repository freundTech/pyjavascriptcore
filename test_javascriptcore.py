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


class EvaluateScriptTestCase(unittest.TestCase):
    """Evaluate arbitrary expressions in the JavaScript interpreter.
    """

    def setUp(self):
        self.ctx = jscore.JSContext()

    def tearDown(self):
        del self.ctx

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


class ContextLiveTestCase(unittest.TestCase):
    """Check that the context remains alive when Python still
    references some of its objects.
    """

    def testContextLive(self):
        ctx = jscore.JSContext()
        obj = ctx.evaluateScript("""({a: 1, b: 'x'})""")

        # Release the Python context object.
        del ctx

        # Check that the object is still useful.
        self.assertEqual(obj.a, 1)
        self.assertEqual(obj.b, 'x')

        # Release the object.
        del obj


class AttributeAccessTestCase(unittest.TestCase):
    """Access the attributes of JavaScript objects from Python
    """

    def setUp(self):
        self.ctx = jscore.JSContext()
        self.obj = self.ctx.evaluateScript("""
          obj = {a: 1,
                 b: 'x',
                 c: {d: 2,
                     e: 'yy'}};
          obj;
          """)

    def tearDown(self):
        del self.ctx

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


if __name__ == '__main__':
    unittest.main()
