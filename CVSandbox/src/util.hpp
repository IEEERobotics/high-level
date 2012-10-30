/*
 * util.hpp
 *
 *  Created on: Oct 19, 2012
 *      Author: Arpan
 */

#ifndef UTIL_HPP_
#define UTIL_HPP_

// Standard C++ includes
#include <iostream>

// OpenCV includes
#include <opencv2/opencv.hpp>

// Selected OpenCV version identifiers (major, minor only)
#if CV_MAJOR_VERSION == 2
	#if CV_MINOR_VERSION == 4
		#define CV_2_4
	#elif CV_MINOR_VERSION == 3
		#define CV_2_3
	#elif CV_MINOR_VERSION == 2
		#define CV_2_2
	#endif
#endif

// Pre-processor flags and constants

// Pre-processor macros
#define STRINGIFY(value) #value

#ifdef DEBUG
#	define IFDEBUG(stmt) stmt
#else
#	define IFDEBUG(stmt)
#endif

// Common namespaces
using namespace std;
using namespace cv;

// Global constants
const char filePathSep = '/';
const char fileExtSep = '.';
const string image_file_exts("bmp jpg jpeg png tiff");

// Global variables and objects


// General utility functions
/**
 * Generic toString() function for types with the stream operator << overloaded.
 * Note: This will generate compile time errors if the stream operator << is not overloaded for the type T.
 * Specialize this template function for desired types if necessary.
 */
template<typename T>
inline string toString(const T& value) {
	stringstream sstrm;
	sstrm << value;
	return sstrm.str();
}

/**
 * Specialized toString() function for type bool.
 */
template<>
inline string toString<bool>(const bool& value) {
	return (value ? "true" : "false");
}

/**
 * Specialized toString() function for type Size.
 */
template<>
inline string toString<Size>(const Size& size) {
	stringstream sstrm;
	sstrm << size.width << 'x' << size.height;
	return sstrm.str();
}

/**
 * Specialized toString() function for type Rect.
 */
template<>
inline string toString<Rect>(const Rect& rect) {
	stringstream sstrm;
	sstrm << "[(" << rect.x << ", " << rect.y << ") - (" << (rect.x + rect.width) << ", " << (rect.y + rect.height) << ")]";
	return sstrm.str();
}

/**
 * Specialized toString() function for type Scalar.
 */
template<>
inline string toString<Scalar>(const Scalar& value) {
	stringstream sstrm;
	sstrm << "(" << value[0] << ", " << value[1] << ", " << value[2] << ", " << value[3] << ")";
	return sstrm.str();
}

// File system utility functions
/**
 * Extracts complete file name (with extension, if any), given a file path.
 */
inline string getFileName(const string& filePath) {
	string::size_type pos = filePath.find_last_of(filePathSep);
	if(pos != string::npos)
		return filePath.substr(pos + 1);
	return filePath; // no path separator, so the file path was a pure file name
}

/**
 * Extracts the base part of a file name leaving out the extension, if any.
 * Note: Argument must be a file name; a path with directories containing the extension separator '.' will mess up results.
 */
inline string getBaseFileName(const string& fileName) {
	string::size_type pos = fileName.find_last_of(fileExtSep);
	if(pos != string::npos && pos != 0) // some special files begin with '.'
		return fileName.substr(0, pos);
	return fileName; // no extension separator, so the file name consists only of the base part
}

/**
 * Extracts the extension from a given file name, if any.
 */
inline string getFileExtension(const string& fileName) {
	string::size_type pos = fileName.find_last_of(fileExtSep);
	if(pos != string::npos && pos != 0) // some special files begin with '.'
		return fileName.substr(pos + 1);
	return ""; // no extension separator, so no extension
}

/**
 * Guesses whether given file is a static image, solely from file extension.
 */
inline bool isStaticImageFile(const string& fileName) {
	string ext = getFileExtension(fileName);
	if(ext.length() > 0) {
		IFDEBUG(cout << "isStaticImageFile(\"" << filename << "\"): ext = \"" << ext << "\"" << endl;)
		if(image_file_exts.find(ext) != string::npos)
			return true;
	}
	return false;
}


// OpenCV utility functions
/**
 * Draws a polygon outline on an image, given its vertex coordinates.
 */
inline void drawPolygon(Mat& imageOut, const Point2f* polyPoints, int numPolyPoints, const Scalar& color, int thickness = 1) {
	for(int i = 0; i < numPolyPoints; i++)
		line(imageOut, polyPoints[i], polyPoints[(i + 1) % numPolyPoints], color, thickness);
}

/**
 * Draws a RotatedRect(angle) outline on an image.
 */
inline void drawRotatedRect(Mat& imageOut, const RotatedRect& rotatedRect, const Scalar& color, int thickness = 1) {
	Point2f rectPoints[4];
	rotatedRect.points(rectPoints);
	drawPolygon(imageOut, rectPoints, 4, color, thickness);
}

#endif /* UTIL_HPP_ */
