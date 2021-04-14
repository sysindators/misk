#!/usr/bin/env python3
# This file is a part of misk and is subject to the the terms of the MIT license.
# Copyright (c) Mark Gillard <mark.gillard@outlook.com.au>
# See https://github.com/marzer/misk/blob/master/LICENSE.txt for the full license text.
# SPDX-License-Identifier: MIT

import sys as _sys
import shutil as _shutil
import fnmatch as _fnmatch
import requests as _requests
import hashlib as _hashlib
import logging as _logging
import traceback as _traceback
import subprocess as _subprocess
from pathlib import Path as _Path
from io import StringIO



#=======================================================================================================================
# shared lib state
#=======================================================================================================================

class _State(object):

	def __init__(self):
		self.entry_script_dir = _Path(_sys.argv[0]).resolve().parent
		self.python = 'py' if _shutil.which('py') is not None else 'python3'
		self.logger = _logging.getLogger(__name__)
		self.logger.setLevel(_logging.INFO)



	def __call__(self, msg):
		self.logger.info(msg)



__state = None
def _state():
	global __state
	if __state is None:
		__state = _State()
	return __state



def _log(msg):
	return _state().logger.info(msg)



#=======================================================================================================================
# functions
#=======================================================================================================================



def add_log_handler(log_handler):
	'''
	Adds a log handler to the internal logger instance used by misk.
	'''
	_state().logger.addHandler(log_handler)



def is_collection(val):
	'''
	Returns true if an object is an instance of one of the python built-in iterable collections.
	'''
	if isinstance(val, (list, tuple, dict, set, range)):
		return True
	return False



def print_exception(exc, file=_sys.stderr, include_type=False, include_traceback=False, skip_frames=0):
	'''
	Pretty-prints an exception with optional traceback.
	'''
	if isinstance(exc, AssertionError):
		include_type=True
		include_traceback=True
	buf = StringIO()
	print(rf'Error: ', file=buf, end='')
	if include_type:
		print(rf'[{type(exc).__name__}] ', file=buf, end='')
	print(str(exc), file=buf)
	if include_traceback:
		tb = exc.__traceback__
		while skip_frames > 0 and tb.tb_next is not None:
			skip_frames = skip_frames - 1
			tb = tb.tb_next
		_traceback.print_exception(type(exc), exc, tb, file=buf)
	print(buf.getvalue(),file=file, end='')



def entry_script_dir():
	'''
	Returns a pathlib.Path representing the directory of the script used to enter the python process.
	'''
	return _state().entry_script_dir



def _coerce_path(path):
	assert path is not None
	if not isinstance(path, _Path):
		path = _Path(str(path))
	return path



def assert_existing_file(path):
	'''
	Asserts that a path represents an existing file on disk.
	'''
	path = _coerce_path(path)
	if not path.exists() and path.is_file():
		raise Exception(rf'{path} did not exist or was not a file')



def assert_existing_directory(path):
	'''
	Asserts that a path represents an existing directory on disk.
	'''
	path = _coerce_path(path)
	if not path.exists() and path.is_dir():
		raise Exception(f'{path} did not exist or was not a directory')



def delete_directory(path):
	'''
	Deletes a directory (and all its contents).
	'''
	path = _coerce_path(path)
	if path.exists():
		if not path.is_dir():
			raise Exception(rf'{path} was not a directory')
		_log(rf'Deleting {path}')
		_shutil.rmtree(str(path.resolve()))



def copy_file(source, dest):
	'''
	Copies a single file.
	'''
	source = _coerce_path(source)
	dest = _coerce_path(dest)
	assert_existing_file(source)
	_log(rf'Copying {source} to {dest}')
	_shutil.copy(str(source), str(dest))



def move_file(source, dest):
	'''
	Moves a single file.
	'''
	source = _coerce_path(source)
	dest = _coerce_path(dest)
	assert_existing_file(source)
	_log(rf'Moving {source} to {dest}')
	_shutil.move(str(source), str(dest))



def delete_file(path):
	'''
	Deletes a single file.
	'''
	path = _coerce_path(path)
	if path.exists():
		if not path.is_file():
			raise Exception(rf'{path} was not a file')
		_log(rf'Deleting {path}')
		path.unlink()



def get_all_files(path, all=None, any=None, recursive=False, sort=True):
	'''
	Collects all files in a directory matching some filters.
	'''
	path = _coerce_path(path)
	if not path.exists():
		return []
	if not path.is_dir():
		raise Exception(rf'{path} was not a directory')

	child_files = []
	files = []
	for p in path.iterdir():
		if p.is_dir():
			if recursive:
				child_files = child_files + get_all_files(p, all=all, any=any, recursive=True, sort=False)
		elif p.is_file():
			files.append(str(p))

	if files and all is not None:
		if not is_collection(all):
			all = (all,)
		all = [f for f in all if f is not None]
		for fil in all:
			files = _fnmatch.filter(files, fil)

	if files and any is not None:
		if not is_collection(any):
			any = (any,)
		any = [f for f in any if f is not None]
		if any:
			results = set()
			for fil in any:
				results.update(_fnmatch.filter(files, fil))
			files = [f for f in results]

	files = [_Path(f) for f in files] + child_files
	if sort:
		files.sort()
	return files



def read_all_text_from_file(path, fallback_url=None, encoding='utf-8'):
	'''
	Reads all the text from a file, optionally downloading it if the file did not exist on disk or a read error occured.
	'''
	path = _coerce_path(path)
	if fallback_url is None:
		assert_existing_file(path)
	try:
		_log(rf'Reading {path}')
		with open(path, 'r', encoding=encoding) as f:
			text = f.read()
		return text
	except:
		if fallback_url is not None:
			_log(rf"Couldn't read file locally, downloading from {fallback_url}")
			response = _requests.get(
				fallback_url,
				timeout=1
			)
			text = response.text
			with open(path, 'w', encoding='utf-8', newline='\n') as f:
				f.write(text)
			return text
		else:
			raise



def run_python_script(path, *args, cwd=None, **kwargs):
	'''
	Invokes a python script as a subprocess.
	'''
	path = _coerce_path(path)
	if not path.exists():
		raise Exception(rf'{path} was not an existing directory or file')

	return _subprocess.run(
		[_state().python, str(path)] + [arg for arg in args],
		check=True,
		cwd=path.cwd() if cwd is None else cwd,
		**kwargs
	)



def _do_hash(hasher, obj, *objs):
	assert obj is not None
	append = lambda o: hasher.update(str(o).encode('utf-8'))
	append(obj)
	if objs:
		for o in objs:
			assert o is not None
			append(o)
	return hasher.hexdigest()



def sha1(obj, *objs):
	'''
	Returns an SHA-1 hash of one or more objects.
	'''
	return _do_hash(_hashlib.sha1(), obj, *objs)



def sha256(obj, *objs):
	'''
	Returns an SHA-256 hash of one or more objects.
	'''
	return _do_hash(_hashlib.sha256(), obj, *objs)



def is_pow2(n):
	'''
	Returns true if a positive integer is a power of two.
	'''
	n = int(n)
	return n and (n & (n - 1) == 0)



def next_pow2(n):
	'''
	Rounds an integer up to the next positive power of two.
	'''
	n = int(n)
	if n <= 0:
		return 1
	if n & (n - 1) == 0:
		return n
	while n & (n - 1) > 0:
		n &= (n - 1)
	return n << 1
