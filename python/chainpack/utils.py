def print_to_string(*args):
	"""
	helps to create a logging function that behaves like print statement, taking a variable number of arguments, so it is easy to replace print statements with log statements.
	but sends the output to standard python logger instead of stdout. Another option is monkey-patching
	sys.stdout, or giving up print-style logging. This is unwiedly when replacing print statements with log statements
	full print implementation: https://bitbucket.org/pypy/pypy/src/ed43c2dc0a42843bbf9637b14a2c30dfe2785295/pypy/module/__builtin__/app_io.py?at=default&fileviewer=file-view-default#app_io.py-78
	"""
	r = ""
	for i, arg in enumerate(args):
		if i:
			r += " "
		r += str(arg)
	return r
