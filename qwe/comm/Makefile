# Makefile for generating Python wrappers for C/C++ code using SWIG

CC = g++
CFLAGS = -fPIC # needed for shared libraries
PYINCLUDE = /usr/include/python2.7/ # C/C++ include files for Python extensions

TARGETS = pyComm.py _pyComm.so
OBJECTS = SerialInterface.o SerialCommands.o
PYOBJECTS = pyComm_wrap.o
WRAPPERS = pyComm_wrap.cxx

all: $(TARGETS)

# Cleans up intermediate files after build
smart: all tidy

# Generates Python module (%.py) and SWIG wrapper (%_wrap.cxx) from interface (%.i)
%.py %_wrap.cxx: %.i
	swig -c++ -python $<

# Builds shared library
_pyComm.so: $(OBJECTS) $(PYOBJECTS)
	$(CC) -shared $(OBJECTS) $(PYOBJECTS) -o $@

$(OBJECTS): %.o: %.cpp %.h
	$(CC) -c $(CFLAGS) $< -o $@

$(PYOBJECTS): %.o: %.cxx
	$(CC) -c $(CFLAGS) $< -o $@ -I$(PYINCLUDE)

.PHONY: clean tidy

clean: tidy
	rm -f $(TARGETS)

tidy:
	rm -f $(OBJECTS) $(PYOBJECTS) $(WRAPPERS)
