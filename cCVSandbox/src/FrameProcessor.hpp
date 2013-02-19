/**
 * @file FrameProcessor.hpp
 *
 * @date Oct 27, 2012
 * @author Arpan
 */

#ifndef FRAMEPROCESSOR_HPP_
#define FRAMEPROCESSOR_HPP_

#include "util.hpp"

/**
 * Base class for sequential frame-by-frame processing applications.
 * Derived classes need only override the process() method, and sometimes initialize().
 */
class FrameProcessor {
public:
	virtual void initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow) { }
	virtual bool process(const Mat& imageIn, Mat& imageOut, const double& timeNow) { return true; }
	virtual void finish(const double& timeNow) { }
	virtual bool onKeyPress(int key) { return true; }
	virtual void onMouseEvent(int event, int x, int y, int flags, void* param) { }
	virtual void onMessage(const string& msg) { }
	virtual ~FrameProcessor() { }
};

/**
 * Mouse callback function that can chain to any FrameProcessor object's onMouseEvent method, with optional window ID template parameter.
 * Use windowId = -1 to call onMouseEvent with param = NULL
 */
template<int windowId>
void passMouseEvent(int event, int x, int y, int flags, void* param) {
	//cout << "passMouseEvent<" << windowId << ">()" << endl;
	FrameProcessor* processor = (FrameProcessor*) (param);
	if(processor != NULL) {
		int winId_temp = windowId; // cannot obtain pointer to template constant, so store in temp variable
		processor->onMouseEvent(event, x, y, flags, (winId_temp == -1 ? NULL : &winId_temp));
	}
}

#endif /* FRAMEPROCESSOR_HPP_ */
