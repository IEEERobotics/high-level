/**
 * @file util.hpp
 * Useful macros, constants and functions (inline and templated functions only).
 *
 * @date Nov 1, 2012
 * @author Arpan
 */

#ifndef UTIL_HPP_
#define UTIL_HPP_

// Standard C++ includes
#include <iostream>
#include <string>
#include <sstream>
#include <cmath>

// Boost includes
#ifdef BOOST
#	include <boost/filesystem.hpp>
#endif

// Android includes
#ifdef ANDROID
#	include <android/log.h>
#endif

// OpenCV includes
#include <opencv2/opencv.hpp>

// OpenCV version (major, minor only)
#if CV_MAJOR_VERSION == 2
	#if CV_MINOR_VERSION == 4
		#define CV_2_4
	#elif CV_MINOR_VERSION == 3
		#define CV_2_3
	#elif CV_MINOR_VERSION == 2
		#define CV_2_2
	#endif
#endif

// Common namespaces
using namespace std;
using namespace cv;

// Pre-processor constants
#define WHITESPACE " \t\n\r" ///< Default set of whitespace characters used by *trim() functions
#ifndef M_PI
#define M_PI 3.14159265358979323846
#define M_SQRT2 1.41421356237309504880
#define M_SQRTPI 1.77245385090551602792981
#endif
#define DEG2RAD (M_PI / 180.0) //< Value of 1 degree in radians
#define FLOAT_EPSILON 1.0e-05 //< like DBL_EPSILON (deprecated; use FLT_EPSILON)

#define XML_FILE_HEADER "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
#define XML_CDATA_BEGIN "<![CDATA["
#define XML_CDATA_END "]]>"

// Typed global constants
const double ticks_per_sec = getTickFrequency();
const double M_SQRT_TWOPI = M_SQRT2 * 1.77245385090551602792981; //M_SQRTPI;

const char filePathSep = '/';
const char fileExtSep = '.';
const string image_file_exts("bmp jpg jpeg png tiff");

extern RNG& rng; ///< thread-local Random Number Generator from OpenCV
extern Mat emptyMat; ///< used to return an empty image (Mat) when a reference has to be returned

// Macros
#define STRINGIFY(value) #value

#ifdef DEBUG
#	define IFDEBUG(stmt) stmt
#	ifndef LOG_DEBUG
#		define LOG_DEBUG
#	endif
#else
#	define IFDEBUG(stmt)
#endif

#define LOGI(tag, text) (void)0;
#define LOGD(tag, text) (void)0;
#define LOGE(tag, text) (void)0;
#ifdef ANDROID
#	ifdef LOG_INFO
#		undef LOGI
#		define LOGI(tag, text) __android_log_write(ANDROID_LOG_INFO, tag, text);
#	endif
#	ifdef LOG_DEBUG
#		undef LOGD
#		define LOGD(tag, text) __android_log_write(ANDROID_LOG_DEBUG, tag, text);
#	endif
#	ifdef LOG_ERROR
#		undef LOGE
#		define LOGE(tag, text) __android_log_write(ANDROID_LOG_ERROR, tag, text);
#	endif
#else
#	ifdef LOG_INFO
#		undef LOGI
#		define LOGI(tag, text) cout << tag << "::" << text << endl;
#	endif
#	ifdef LOG_DEBUG
#		undef LOGD
#		define LOGD(tag, text) cout << tag << "::" << text << endl;
#	endif
#	ifdef LOG_ERROR
#		undef LOGE
#		define LOGE(tag, text) cerr << tag << "::" << text << endl;
#	endif
#endif

#define DUMPOUT(var) cout << #var << " = " << var;
#define DM(var) << #var << " = " << var << ", "
#define DME(var) << #var << " = " << var
#define DUMPM(stuff) cout##stuff << endl;

#define DOUT cout
#define DVAR(var) << #var << " = " << var << ", "
#define DEND << endl;
#define DVAREND(var) << #var << " = " << var << endl;

#define VECLOOPBEGIN(type, var, vec) \
	/* Note: vec will be evaluated twice if it is a function/operation! */ \
	for(vector<type >::iterator var##_it = (vec).begin(); var##_it != (vec).end(); var##_it++) { \
		type& var = *var##_it;
#define VECLOOPEND }

#define CONSTVECLOOPBEGIN(type, var, vec) \
	/* Note: vec will be evaluated twice if it is a function/operation! */ \
	for(vector<type >::const_iterator var##_it = (vec).begin(); var##_it != (vec).end(); var##_it++) { \
		type const& var = *var##_it;
#define CONSTVECLOOPEND }

#define LISTLOOPBEGIN(type, var, lst) \
	/* Note: lst will be evaluated twice if it is a function/operation! */ \
	for(list<type >::iterator var##_it = (lst).begin(); var##_it != (lst).end(); var##_it++) { \
		type& var = *var##_it;
#define LISTLOOPEND }

#define CONSTLISTLOOPBEGIN(type, var, lst) \
	/* Note: lst will be evaluated twice if it is a function/operation! */ \
	for(list<type >::const_iterator var##_it = (lst).begin(); var##_it != (lst).end(); var##_it++) { \
		type const& var = *var##_it;
#define CONSTLISTLOOPEND }

#define MATLOOPBEGIN(type, image, width, height, xstep, ystep) \
	/* Note: image will be evaluated multiple times if it is a function/operation! Better use an object. */ \
	for(int y = 0; y < (height); y += (ystep)) { \
		for(int x = 0; x < (width); x += (xstep)) { \
			type& pixelValue = (image).at<type>(y, x);
#define MATLOOPEND } }

#define MATROWLOOPBEGIN(height, ystep) for(int y = 0; y < (height); y += (ystep)) {
#define MATROWLOOPEND }

#define MATCOLLOOPBEGIN(width, xstep) for(int x = 0; x < (width); x += (xstep)) {
#define MATCOLLOOPEND }

#define MATLOOPGETPIXEL(type, var, image) type& var = (image).at<type>(y, x);

#define NAMEDWINDOW(name, arg) (void)0
#define IMSHOW(window, image) (void)0
#define WAITKEY(delay) (void)0
#ifdef GUI
#	undef NAMEDWINDOW
#	define NAMEDWINDOW(name, arg) namedWindow(name, arg)
#	undef IMSHOW
#	define IMSHOW(window, image) imshow(window, image)
#	undef WAITKEY
#	define WAITKEY(delay) waitKey(delay)
#endif

// General utility functions
/**
 * Trims leading whitespaces. Does not modify original string.
 */
inline string ltrim(const string& str) {
	if(!str.empty()) {
		string::size_type startpos = str.find_first_not_of(WHITESPACE); // leading whitespace
		if(startpos != string::npos) {
		    return str.substr(startpos);
		}
		else
			return ""; // all characters are whitespace!
	}
	return str;
}

/**
 * Trims trailing whitespaces. Does not modify original string.
 */
inline string rtrim(const string& str) {
	if(!str.empty()) {
		string::size_type endpos = str.find_last_not_of(WHITESPACE); // trailing whitespace
		if(endpos != string::npos) {
		    return str.substr(0, endpos + 1);
		}
		else
			return ""; // all characters are whitespace!
	}
	return str;
}

/**
 * Trims leading and trailing whitespaces. Does not modify original string.
 */
inline string trim(const string& str) {
	return ltrim(rtrim(str));
}

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

// Command-line processing functions
/**
 * Returns command line argument at position specified by pos, or defaultValue if argument array isn't long enough.
 */
inline string getCLArg(int argc, char* argv[], int pos, string defaultValue="") {
	if(argc > pos)
		return argv[pos];
	else
		return defaultValue;
}

/**
 * Processes command line arguments and creates a key-value map in options. If options is non-empty, only the arguments specified as its keys are read, otherwise all arguments are read. Returns true if parsing was successful.
 */
bool parseCommandline(int argc, char *argv[], map<string, string>& options);

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
		IFDEBUG(cout << "isStaticImageFile(\"" << fileName << "\"): ext = \"" << ext << "\"" << endl;)
		if(image_file_exts.find(ext) != string::npos)
			return true;
	}
	return false;
}

#ifdef BOOST
/**
 * Returns the filename (sans path) and extension of a given complete filepath, separated into an STL pair. Uses Boost library.
 */
inline pair<string, string> getFilenameParts(const string& filepath) {
	boost::filesystem::path myPath(filepath);
	return make_pair(myPath.stem().string(), myPath.extension().string());
}
#endif

// OpenCV utility functions
/**
 * Returns the slope of a straight line, given delta values (along X and Y axes)
 */
inline double slopeFromDelta(const Point& delta) {
	return (delta.y == 0
			? 0.0
			: (delta.x == 0
				? (delta.y > 0 ? 1 : -1) * numeric_limits<double>::infinity()
				: double(delta.y) / delta.x));
}

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

/**
 * Pauses program and lets OpenCV handle window events. Use WAITKEY() directly for pausing without a prompt.
 */
inline int pauseKey(const string& prompt = "", int delay = 0) {
	cout << (prompt.empty() ? "Press any key to continue..." : prompt) << endl;
#ifdef GUI
	return WAITKEY(delay);
#else
	cout << "[Non-GUI mode - type a single character and press enter]: ";
	char ch;
	cin >> ch;
	return ((int) ch); // Note: -1 signals no key was pressed, apt for a no GUI mode?
#endif
}

/**
 * Normalizes a floating-point image to 0..255 range and converts it to 8-bit unsigned image, suitable for display purposes.
 */
inline Mat toDisplayImage(const Mat& image) {
	CV_Assert(image.channels() == 1); // due to the min-max normalization, this only works on single-channel images

	Mat imageNormalized;
	normalize(image, imageNormalized, 0, 255, NORM_MINMAX);
	Mat image8U;
	imageNormalized.convertTo(image8U, CV_8U);
	return image8U;
}

#endif /* UTIL_HPP_ */
