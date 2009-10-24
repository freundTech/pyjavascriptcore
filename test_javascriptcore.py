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
    """Create a context, evaluate scripts in it and check their return
    values."""

    def setUp(self):
        self.ctx = jscore.JSContext()

    def tearDown(self):
        self.ctx = None

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

    def testEvaluateError(self):
        def code():
            program = '(function(x){return x+2 return})(3)'
            self.assertEqual(self.ctx.evaluateScript(program), 5)

        self.assertRaises(jscore.JSException, code)


if __name__ == '__main__':
    unittest.main()
