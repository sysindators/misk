#!/usr/bin/env python3
# This file is a part of misk and is subject to the the terms of the MIT license.
# Copyright (c) Mark Gillard <mark.gillard@outlook.com.au>
# See https://github.com/marzer/misk/blob/master/LICENSE.txt for the full license text.
# SPDX-License-Identifier: MIT

import time as _time
from datetime import timedelta as _timedelta

class ScopeTimer(object):
	'''
	A utility class for scoped timing blocks of code using python's "with" keyword.
	'''

	def __init__(self, description, print_start=False, print_func=print):
		self.__description = str(description)
		self.__print_start = print_start
		self.__print_func = print_func

	def __enter__(self):
		self.__start = _time.perf_counter_ns()
		if self.__print_start:
			self.__print_func(self.__description)

	def __exit__(self ,type, value, traceback):
		if traceback is None:
			nanos = _time.perf_counter_ns() - self.__start
			micros = int(nanos / 1000)
			nanos = int(nanos % 1000)
			micros = float(micros) + float(nanos) / 1000.0
			self.__print_func(rf'{self.__description} completed in {_timedelta(microseconds=micros)}.')
