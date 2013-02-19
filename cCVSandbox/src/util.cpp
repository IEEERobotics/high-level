/**
 * @file util.cpp
 * Useful macros, constants and functions (non-inline and non-templated).
 *
 * @date Nov 1, 2012
 * @author Arpan
 */

#include "util.hpp"

Mat emptyMat = Mat();

bool parseCommandline(int argc, char *argv[], map<string, string>& options) {
	vector<string> args(argv + 1, argv + argc);
	bool acceptAll = options.empty();

	for (vector<string>::iterator argit = args.begin(); argit != args.end(); ++argit) {
		if (*argit == "-h" || *argit == "--help") {
			if(acceptAll)
				cout << "Options unspecified (all options accepted)." << endl;
			else {
				cout << "Options:" << endl;
				for (map<string, string>::iterator opit = options.begin(); opit != options.end(); opit++) {
					cout << '\t' << (*opit).first << endl;
				}
			}
			break;
		}

		if (acceptAll || options.find(*argit) != options.end()) {
			try {
				vector<string>::iterator valit = (argit + 1);
				if(valit == args.end())
					throw Exception();
				options[*argit] = *valit;
				++argit;
			}
			catch(const Exception& e) {
				cerr << "::parseCommandline(): Error parsing option \"" << *argit << "\" (odd number of arguments?)" << endl;
				return false; // parsing failed
			}
		}
	}

	return true; // successfully completed parsing
}
