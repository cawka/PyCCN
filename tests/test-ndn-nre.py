# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (c) 2013, Regents of the University of California
#                     Yingdi Yu, Alexander Afanasyev
#
# BSD license, See the doc/LICENSE file for more information
#
# Author: Yingdi Yu <yingdi@cs.ucla.edu>
#         Alexander Afanasyev <alexander.afanasyev@ucla.edu>
#

import unittest
from ndn import Name
from ndn.nre import *

class Basic (unittest.TestCase):
    def test_on_ComponentMatcher (self):
        m = ComponentMatcher('a', None)
        m.match(Name('/a/b/'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])
        m.match(Name('/a/b/'), 1, 1)
        self.assertEquals (m.matchResult, [])

    def test_on_ComponentSetMatcher (self):
        m = ComponentSetMatcher('<a>', None)
        m.match(Name('/a/b/'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])
        m.match(Name('/a/b/'), 1, 1)
        self.assertEquals (m.matchResult, [])
        m.match(Name('/a/b/'), 0, 2)
        self.assertEquals (m.matchResult, [])

        m = ComponentSetMatcher('[<a><b><c>]', None)
        m.match(Name('/a/b/d'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])
        m.match(Name('/a/b/d'), 2, 1)
        self.assertEquals (m.matchResult, [])
        m.match(Name('/a/b/d'), 0, 2)
        self.assertEquals ( m.matchResult, [])

        m = ComponentSetMatcher('[^<a><b><c>]', None)
        m.match(Name('/b/d/'), 1, 1)
        self.assertEquals (m.matchResult, ['d'])

    def test_on_RepeatMatcher (self):
        m = RepeatMatcher('[<a><b>]*', None, 8)
        m.match(Name('/a/b/c'), 0, 0)
        self.assertEquals (m.matchResult, [])
        m.match(Name('/a/b/c'), 0, 2)
        self.assertEquals (m.matchResult, ['a', 'b'])

        m = RepeatMatcher('[<a><b>]+', None, 8)
        res = m.match(Name('/a/b/c'), 0, 0)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        m.match(Name('/a/b/c'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])
        m.match(Name('/a/b/c'), 0, 2)
        self.assertEquals (m.matchResult, ['a', 'b'])

        m = RepeatMatcher('[<.*>]*', None, 6)
        m.match(Name('/a/b/c/d/e/f'), 0, 6)
        self.assertEquals (m.matchResult, ['a','b','c','d','e','f'])
        res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, [])

        m = RepeatMatcher('[<.*>]+', None, 6)
        res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/c/d/e/f'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])

        m = RepeatMatcher('[<a>]?', None, 5)
        res = m.match(Name('/a/b/c/d/e/f'), 0, 0)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/c/d/e/f'), 0, 1)
        self.assertEquals (m.matchResult, ['a'])
        res = m.match(Name('/a/b/c/d/e/f'), 0, 2)
        self.assertFalse (res, False)
        self.assertEquals (m.matchResult, [])

        m = RepeatMatcher('[<a><b>]{3}', None, 8)
        res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b', 'a'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])

        m = RepeatMatcher('[<a><b>]{2,3}', None, 8)
        res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b', 'a'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 1)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])

        m = RepeatMatcher('[<a><b>]{2,}', None, 8)
        res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b', 'a'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 4)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/a/b/e/f'), 0, 4)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','a','b'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 1)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])

        m = RepeatMatcher('[<a><b>]{,2}', None, 8)
        res = m.match(Name('/a/b/a/d/e/f'), 0, 3)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 2)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'b'])
        res = m.match(Name('/a/b/a/b/e/f'), 0, 1)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a'])
        res = m.match(Name('/a/b/a/d/e/f'), 0, 0)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, [])

    def test_on_BackRefMatcher (self):
        backRef = []
        m = BackRefMatcher('(<a><b>)', backRef)
        res = m.match(Name('/a/b/'), 0, 2)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b'])
        self.assertEquals (len(m.backRef), 1)

        backRef = []
        m = RepeatMatcher('(<a><b>)+', backRef, 8)
        res = m.match(Name('/a/b/a/b/'), 0, 4)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b', 'a', 'b'])
        self.assertEquals (len(m.backRef), 1)

        backRef = []
        m = RepeatMatcher('(<a>(<a><b>){2})+', backRef, 16)
        res = m.match(Name('/a/a/b/a/b/'), 0, 5)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a', 'a', 'b', 'a', 'b'])
        self.assertEquals (len(m.backRef), 2)
        self.assertEquals (backRef[1].matchResult, ['a', 'b'])


    def test_on_PatternListMatcher (self):
        m = PatternListMatcher('<a><b><c>', None)
        m.match(Name('/a/b/c/'), 0, 3)
        self.assertEquals (m.matchResult, ['a', 'b', 'c'])

        m = PatternListMatcher('<a>[<a><b>]', None)
        m.match(Name('/a/b/c/'), 0, 2)
        self.assertEquals (m.matchResult, ['a', 'b'])

        m = PatternListMatcher('<.*>*<a>', None)
        res = m.match(Name('/a/b/c/'), 0, 3)
        self.assertFalse (res)
        self.assertEquals (m.matchResult, [])

        m = PatternListMatcher('<.*>*<a><.*>*', None)
        res = m.match(Name('/a/b/c/'), 0, 3)
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','c'])

    def test_on_RegexMatcher (self):
        m = RegexMatcher('^<a><b><c>')
        res = m.matchName(Name('/a/b/c/d'))
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','c', 'd'])

        m = RegexMatcher('<b><c><d>$')
        res = m.matchName(Name('/a/b/c/d'))
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','c', 'd'])

        m = RegexMatcher('^<a><b><c><d>$')
        res = m.matchName(Name('/a/b/c/d'))
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','c', 'd'])

        m = RegexMatcher('<a><b><c><d>')
        res = m.matchName(Name('/a/b/c/d'))
        self.assertTrue (res)
        self.assertEquals (m.matchResult, ['a','b','c', 'd'])

        m = RegexMatcher('<b><c>')
        res = m.matchName(Name('/a/b/c/d'))
        self.assertTrue (res)

    def test_on_RegexMatcher_BackReference (self):
        m = RegexMatcher('^(<.*>*)<.*>$')
        res = m.matchName(Name('/n/a/b/'))
        self.assertEquals (m.extract('\\1'), ['n', 'a'])

        m = RegexMatcher('^(<.*>*)<.*>')
        res = m.matchName(Name('/n/a/b/c/'))
        self.assertTrue (res)
        self.assertEquals (m.extract('\\1'), [])

class AggressiveMatch (unittest.TestCase):
    def test_on_RepeatMatcher (self):
         m = RepeatMatcher('[<a><b>]*', None, 8)
         m.aggressiveMatch(Name('/a/b/c'), 0, 0)
         self.assertEquals (m.matchResult, [])
         m.aggressiveMatch(Name('/a/b/c'), 0, 2)
         self.assertEquals (m.matchResult, ['a', 'b'])

         m = RepeatMatcher('[<a><b>]+', None, 8)
         res = m.aggressiveMatch(Name('/a/b/c'), 0, 0)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         m.aggressiveMatch(Name('/a/b/c'), 0, 1)
         self.assertEquals (m.matchResult, ['a'])
         m.aggressiveMatch(Name('/a/b/c'), 0, 2)
         self.assertEquals (m.matchResult, ['a', 'b'])

         m = RepeatMatcher('[<.*>]*', None, 6)
         m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 6)
         self.assertEquals (m.matchResult, ['a','b','c','d','e','f'])
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, [])

         m = RepeatMatcher('[<.*>]+', None, 6)
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 1)
         self.assertEquals (m.matchResult, ['a'])

         m = RepeatMatcher('[<a>]?', None, 5)
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 0)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 1)
         self.assertEquals (m.matchResult, ['a'])
         res = m.aggressiveMatch(Name('/a/b/c/d/e/f'), 0, 2)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])

         m = RepeatMatcher('[<a><b>]{3}', None, 8)
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b', 'a'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])

         m = RepeatMatcher('[<a><b>]{2,3}', None, 8)
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b', 'a'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 1)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])

         m = RepeatMatcher('[<a><b>]{2,}', None, 8)
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b', 'a'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 4)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/a/b/e/f'), 0, 4)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','a','b'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 1)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])

         m = RepeatMatcher('[<a><b>]{,2}', None, 8)
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 3)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 2)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'b'])
         res = m.aggressiveMatch(Name('/a/b/a/b/e/f'), 0, 1)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a'])
         res = m.aggressiveMatch(Name('/a/b/a/d/e/f'), 0, 0)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, [])

    def test_on_BackRefMatcher (self):
         backRef = []
         m = BackRefMatcher('(<a><b>)', backRef)
         res = m.match(Name('/a/b/'), 0, 2)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b'])
         self.assertEquals (len(m.backRef), 1)

         backRef = []
         m = RepeatMatcher('(<a><b>)+', backRef, 8)
         res = m.match(Name('/a/b/a/b/'), 0, 4)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b', 'a', 'b'])
         self.assertEquals (len(m.backRef), 1)

         backRef = []
         m = RepeatMatcher('(<a>(<a><b>){2})+', backRef, 16)
         res = m.match(Name('/a/a/b/a/b/'), 0, 5)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a', 'a', 'b', 'a', 'b'])
         self.assertEquals (len(m.backRef), 2)
         self.assertEquals (backRef[1].matchResult, ['a', 'b'])


    def test_on_PatternListMatcher (self):
         m = PatternListMatcher('<a><b><c>', None)
         m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
         self.assertEquals (m.matchResult, ['a', 'b', 'c'])

         m = PatternListMatcher('<a>[<a><b>]', None)
         m.aggressiveMatch(Name('/a/b/c/'), 0, 2)
         self.assertEquals (m.matchResult, ['a', 'b'])

         m = PatternListMatcher('<.*>*<a>', None)
         res = m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
         self.assertFalse (res)
         self.assertEquals (m.matchResult, [])

         m = PatternListMatcher('<.*>*<a><.*>*', None)
         res = m.aggressiveMatch(Name('/a/b/c/'), 0, 3)
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','c'])

    def test_on_RegexMatcher (self):
         m = RegexMatcher('^<a><b><c>')
         res = m.matchN(Name('/a/b/c/d'))
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','c', 'd'])

         m = RegexMatcher('<b><c><d>$')
         res = m.matchN(Name('/a/b/c/d'))
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','c', 'd'])

         m = RegexMatcher('^<a><b><c><d>$')
         res = m.matchN(Name('/a/b/c/d'))
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','c', 'd'])

         m = RegexMatcher('<a><b><c><d>')
         res = m.matchN(Name('/a/b/c/d'))
         self.assertTrue (res)
         self.assertEquals (m.matchResult, ['a','b','c', 'd'])

         m = RegexMatcher('<b><c>')
         res = m.matchN(Name('/a/b/c/d'))
         self.assertTrue (res)

         m = RegexMatcher('^(<.*>*)<.*>')
         res = m.matchN(Name('/n/a/b/c/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\1'), ['n','a','b'])

         m = RegexMatcher('^(<.*>*)<.*><c>(<.*>)<.*>')
         res = m.matchN(Name('/n/a/b/c/d/e/f/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\1\\2'), ['n','a', 'd'])

         m = RegexMatcher('(<.*>*)<.*>$')
         res = m.matchN(Name('/n/a/b/c/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\1'), ['n', 'a', 'b'])

         m = RegexMatcher('<.*>(<.*>*)<.*>$')
         res = m.matchN(Name('/n/a/b/c/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\1'), ['a','b'])

         m = RegexMatcher('<a>(<.*>*)<.*>$')
         res = m.matchN(Name('/n/a/b/c/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\1'), ['b'])

         m = RegexMatcher('^<.*><(.+)\.(.+)><c>(<.*>)')
         res = m.matchN(Name('/n/a.b/c/d/e/f/'))
         self.assertTrue (res)
         self.assertEquals (m.extract('\\2\\1\\3'), ['b','a','d'])

if __name__ == '__main__':
    unittest.main()

