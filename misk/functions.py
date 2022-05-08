#!/usr/bin/env python3
# This file is a part of misk and is subject to the the terms of the MIT license.
# Copyright (c) Mark Gillard <mark.gillard@outlook.com.au>
# See https://github.com/marzer/misk/blob/master/LICENSE.txt for the full license text.
# SPDX-License-Identifier: MIT

import sys
import shutil
import fnmatch
import requests
import hashlib
import logging
import traceback
import subprocess
import io
import re
import pathlib
from pathlib import Path
from typing import List, Union

__all__ = []

#=======================================================================================================================
# shared lib state
#=======================================================================================================================

class _State(object):

	def __init__(self):
		self.entry_script_dir = Path(sys.argv[0]).resolve().parent
		self.python = 'py' if shutil.which('py') is not None else 'python3'



__state = None
def _state() -> _State:
	global __state
	if __state is None:
		__state = _State()
	return __state



#=======================================================================================================================
# functions
#=======================================================================================================================

def _log(logger, msg, level=logging.INFO):
	if logger is None or msg is None:
		return
	if isinstance(logger, bool):
		if logger:
			print(msg, file=sys.stderr if level >= logging.WARNING else sys.stdout)
	elif isinstance(logger, logging.Logger):
		logger.log(level, msg)
	elif isinstance(logger, io.IOBase):
		print(msg, file=logger)
	else:
		logger(msg)



__all__.append(r'is_collection')
def is_collection(val) -> bool:
	'''
	Returns true if an object is an instance of one of the python built-in iterable collections.
	'''
	if isinstance(val, (list, tuple, dict, set, range)):
		return True
	return False

__all__.append(r'coerce_collection')
def coerce_collection(val) -> Union[list, tuple, dict, set, range]:
	'''
	Returns the input if it already satisfies is_collection(), otherwise returns the input boxed into a tuple.
	'''
	assert val is not None
	if not is_collection(val):
		val = ( val, )
	return val



__all__.append(r'print_exception')
def print_exception(exc, logger=sys.stderr, include_type=False, includetraceback=False, skip_frames=0):
	'''
	Pretty-prints an exception with optional traceback.
	'''
	if isinstance(exc, (AssertionError, NameError, TypeError)):
		include_type=True
		includetraceback=True
	with io.StringIO() as buf:
		if includetraceback:
			tb = exc._traceback__
			while skip_frames > 0 and tb.tb_next is not None:
				skip_frames = skip_frames - 1
				tb = tb.tb_next
			traceback.print_exception(type(exc), exc, tb, file=buf)
		else:
			print(rf'Error: ', file=buf, end='')
			if include_type:
				print(rf'[{type(exc).__name__}] ', file=buf, end='')
			print(str(exc), file=buf, end='')
		_log(logger, buf.getvalue(), level=logging.ERROR)



__all__.append(r'entry_script_dir')
def entry_script_dir() -> pathlib.Path:
	'''
	Returns a pathlib.Path representing the directory of the script used to enter the python process.
	'''
	return _state().entry_script_dir



__all__.append(r'coerce_path')
def coerce_path(arg, *args) -> pathlib.Path:
	'''
	Buildes path from one or more inputs.
	'''
	assert arg is not None
	if args is not None and len(args):
		return Path(str(arg), *[str(a) for a in args])
	else:
		if not isinstance(arg, Path):
			arg = Path(str(arg))
		return arg



__all__.append(r'assert_existing_file')
def assert_existing_file(path):
	'''
	Asserts that a path represents an existing file on disk.
	'''
	path = coerce_path(path)
	if not path.exists() or not path.is_file():
		raise Exception(rf'{path} did not exist or was not a file')



__all__.append(r'assert_existing_directory')
def assert_existing_directory(path):
	'''
	Asserts that a path represents an existing directory on disk.
	'''
	path = coerce_path(path)
	if not path.exists() or not path.is_dir():
		raise Exception(f'{path} did not exist or was not a directory')



__all__.append(r'delete_directory')
def delete_directory(path, logger=None):
	'''
	Deletes a directory (and all its contents).
	'''
	path = coerce_path(path)
	if path.exists():
		if not path.is_dir():
			raise Exception(rf'{path} was not a directory')
		_log(logger, rf'Deleting {path}')
		shutil.rmtree(str(path.resolve()))



__all__.append(r'copy_file')
def copy_file(source, dest, logger=None):
	'''
	Copies a single file.
	'''
	source = coerce_path(source)
	dest = coerce_path(dest)
	assert_existing_file(source)
	_log(logger, rf'Copying {source} to {dest}')
	shutil.copy(str(source), str(dest))



__all__.append(r'move_file')
def move_file(source, dest, logger=None):
	'''
	Moves a single file.
	'''
	source = coerce_path(source)
	dest = coerce_path(dest)
	assert_existing_file(source)
	_log(logger, rf'Moving {source} to {dest}')
	shutil.move(str(source), str(dest))



__all__.append(r'delete_file')
def delete_file(path, logger=None):
	'''
	Deletes a single file.
	'''
	path = coerce_path(path)
	if path.exists():
		if not path.is_file():
			raise Exception(rf'{path} was not a file')
		_log(logger, rf'Deleting {path}')
		path.unlink()



__all__.append(r'enumerate_files')
def enumerate_files(root, all=None, any=None, recursive=False, sort=True) -> List[pathlib.Path]:
	'''
	Collects all files in a directory matching some filename filters.
	'''
	root = coerce_path(root)
	if not root.exists():
		return []
	if not root.is_dir():
		raise Exception(rf'{root} was not a directory')

	child_files = []
	files = []
	for p in root.iterdir():
		if p.is_dir():
			if recursive:
				child_files = child_files + enumerate_files(p, all=all, any=any, recursive=True, sort=False)
		elif p.is_file():
			files.append(str(p.name))

	if files and all is not None:
		if not is_collection(all):
			all = (all,)
		all = [f for f in all if f is not None]
		for fil in all:
			files = fnmatch.filter(files, fil)

	if files and any is not None:
		if not is_collection(any):
			any = (any,)
		any = [f for f in any if f is not None]
		if any:
			results = set()
			for fil in any:
				results.update(fnmatch.filter(files, fil))
			files = [f for f in results]

	files = [Path(root, f) for f in files] + child_files
	if sort:
		files.sort()
	return files



__all__.append(r'get_all_files')
def get_all_files(path, all=None, any=None, recursive=False, sort=True)-> List[pathlib.Path]:
	return enumerate_files(path, all=all, any=any, recursive=recursive, sort=sort)



__all__.append(r'enumerate_directories')
def enumerate_directories(root, filter=None, recursive=False, sort=True) -> List[pathlib.Path]:
	'''
	Collects all subdirectories in a directory.
	'''
	root = coerce_path(root)
	if not root.exists():
		return []
	if not root.is_dir():
		raise Exception(rf'{root} was not a directory')

	subdirs = []
	for p in root.iterdir():
		if p.is_dir():
			if filter is not None and not filter(p):
				continue
			subdirs.append(p)
			if recursive:
				subdirs = subdirs + enumerate_directories(p, filter=filter, recursive=True, sort=False)
	if sort:
		subdirs.sort()
	return subdirs



__all__.append(r'read_all_text_from_file')
def read_all_text_from_file(path, fallback_url=None, encoding='utf-8', logger=None) -> str:
	'''
	Reads all the text from a file, optionally downloading it if the file did not exist on disk or a read error occured.
	'''
	path = coerce_path(path)
	if fallback_url is None:
		assert_existing_file(path)
	try:
		_log(logger, rf'Reading {path}')
		with open(path, 'r', encoding=encoding) as f:
			text = f.read()
		return text
	except:
		if fallback_url is not None:
			_log(logger, rf"Couldn't read file locally, downloading from {fallback_url}")
			response = requests.get(
				fallback_url,
				timeout=1
			)
			text = response.text
			with open(path, 'w', encoding='utf-8', newline='\n') as f:
				f.write(text)
			return text
		else:
			raise



__all__.append(r'run_python_script')
def run_python_script(path, *args, cwd=None, check=True, **kwargs) -> subprocess.CompletedProcess:
	'''
	Invokes a python script as a subprocess.
	'''
	path = coerce_path(path)
	if not path.exists():
		raise Exception(rf'{path} was not an existing directory or file')

	return subprocess.run(
		[_state().python, str(path)] + [arg for arg in args],
		check=check,
		cwd=path.cwd() if cwd is None else cwd,
		**kwargs
	)



def _do_hash(hasher, obj, *objs) -> str:
	assert obj is not None
	append = lambda o: hasher.update(str(o).encode('utf-8'))
	append(obj)
	if objs:
		for o in objs:
			assert o is not None
			append(o)
	return hasher.hexdigest()



__all__.append(r'sha1')
def sha1(obj, *objs) -> str:
	'''
	Returns an SHA-1 hash of one or more objects.
	'''
	return _do_hash(hashlib.sha1(), obj, *objs)



__all__.append(r'sha256')
def sha256(obj, *objs) -> str:
	'''
	Returns an SHA-256 hash of one or more objects.
	'''
	return _do_hash(hashlib.sha256(), obj, *objs)



__all__.append(r'is_pow2')
def is_pow2(n) -> bool:
	'''
	Returns true if a positive integer is a power of two.
	'''
	n = int(n)
	return n and (n & (n - 1) == 0)



__all__.append(r'next_pow2')
def next_pow2(n) -> int:
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



__all__.append(r'replace_metavar')
def replace_metavar(name, repl, text) -> str:
	'''
	Replaces named meta variables in strings. Meta variables can be in any of the following formats:
	   - {% name %}
	   - $( name )
	   - %( name )

	Meta variable names are case sensitive.

	Whitespace inside the meta variables is ignored (i.e. {%name%} matches the same as {% name %}).
	'''
	assert name is not None
	assert repl is not None
	assert text is not None

	if not isinstance(name, str):
		name = str(name)
	name = re.escape(name.strip())
	if not isinstance(repl, str):
		repl = str(repl)
	if not isinstance(text, str):
		text = str(text)

	#  {% name %}
	text = re.sub(rf'{{%[\t ]*{name}[\t ]*%}}', repl, text)

	#  $( name ) and %( name )
	text = re.sub(rf'[$%]\([\t ]*{name}[\t ]*\)', repl, text)

	return text
