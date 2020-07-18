from __future__ import absolute_import

__license__ = """
Copyright (c) 2020 R. Tohid

Distributed under the Boost Software License, Version 1.0. (See accompanying
file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
"""

from numpy import ndarray

from phyfleaux.api.directives import polyhedral

def guard():
    print()
    print("==================================================================")
    print()

guard()

@polyhedral
def function0():
    buf0 = ndarray(10, dtype=int)
    for i in range(10):
        buf0[i] = 3 + 4
    return buf0

print(function0())
guard()