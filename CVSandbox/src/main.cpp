/**
 * @file main.cpp
 *
 * @date Oct 19, 2012
 * @author Arpan
 */

#include "util.hpp"
#include "ColorFilter.hpp"
#include "BlobDetector.hpp"

#define WAITKEY_DELAY 10
#define OUT_DIR "out/"

// Keep only one of the following defined (uncomment here, or specify with -D preprocessor flag)
// The first uncommented/specified module (in the following order) will be executed
//#define RUN_GRAB_CUT_DEMO
//#define RUN_EM_CLUSTERING_DEMO
//#define RUN_FLOOD_FILL_DEMO
//#define RUN_SIMPLE_BLOBS_DEMO
#define RUN_FRAME_PROCESSOR // run a custom frame-by-frame processor; specify class name in FRAME_PROCESSOR
#define FRAME_PROCESSOR BlobDetector //ColorFilter

// Usage: CVSandbox [image/video file]
// Opens image/video file if passed in, or tries to open camera for live input
int main(int argc, char* argv[]) {
	// Demo programs (simply call-through to respective "main-like" function)
#if defined(RUN_GRAB_CUT_DEMO)
	int GrabCutDemo(int argc, char** argv);
	return GrabCutDemo(argc, argv);
#elif defined(RUN_EM_CLUSTERING_DEMO)
	int EMClusteringDemo(int argc, char** argv);
	return EMClusteringDemo(argc, argv);
#elif defined(RUN_FLOOD_FILL_DEMO)
	int FloodFillDemo(int argc, char** argv);
	return FloodFillDemo(argc, argv);
#elif defined(RUN_SIMPLE_BLOBS_DEMO)
	int SimpleBlobsDemo(int argc, char **argv);
	return SimpleBlobsDemo(argc, argv);
#elif defined(RUN_FRAME_PROCESSOR)
	// Custom FrameProcessor - class name specified in FRAME_PROCESSOR
	cout << "main(): FrameProcessor: " << STRINGIFY(FRAME_PROCESSOR) << endl;
	const int cameraFrameWidth = 640, cameraFrameHeight = 480; // desired camera resolution; will try to request this, but not guaranteed to succeed

	Mat imageIn, imageOut;
	VideoCapture videoIn;

	// Command-line argument parsing
	bool isOkay = false, isStaticImage, isLiveVideo;
	string filePath;
	if(argc > 1) {
		filePath = string(argv[1]);
		cout << "main(): File: \"" << filePath << "\"" << endl;

		if(isStaticImageFile(filePath)) {
			isStaticImage = true;

			// Try to read static image file
			imageIn = imread(filePath);

			if(!imageIn.empty()) {
				IFDEBUG(cout << "main(): Static image size: " << imageIn.size().width << "x" << imageIn.size().height << endl;)
				isOkay = true;
			}
			else {
				cerr << "main(): Error opening image file; aborting..." << endl;
				isOkay = false;
			}
		}
		else {
			isLiveVideo = false;

			// Try to read video file
			videoIn.open(filePath);
			if(videoIn.isOpened()) {
				IFDEBUG(cout << "main(): Video frame size: " << videoIn.get(CV_CAP_PROP_FRAME_WIDTH) << "x" << videoIn.get(CV_CAP_PROP_FRAME_HEIGHT) << endl;) //<< " at " << videoIn.get(CV_CAP_PROP_FPS) << " fps" << endl;
				isOkay = true;
			}
			else {
				cerr << "main(): Error opening video file; aborting..." << endl;
				isOkay = false;
				videoIn.release();
			}
		}
	}
	else {
		// Try to open default camera as video source
		videoIn.open(0);
		if(videoIn.isOpened()) {
			IFDEBUG(cout << "main(): Camera frame size [BEFORE]: " << videoIn.get(CV_CAP_PROP_FRAME_WIDTH) << "x" << videoIn.get(CV_CAP_PROP_FRAME_HEIGHT) << endl;)
			videoIn.set(CV_CAP_PROP_FRAME_WIDTH, cameraFrameWidth);
			videoIn.set(CV_CAP_PROP_FRAME_HEIGHT, cameraFrameHeight);
			IFDEBUG(cout << "main(): Camera frame size [AFTER]: " << videoIn.get(CV_CAP_PROP_FRAME_WIDTH) << "x" << videoIn.get(CV_CAP_PROP_FRAME_HEIGHT) << endl;)
			isOkay = true;
		}
		else {
			cerr << "main(): Error opening camera; aborting..." << endl;
			isOkay = false;
			videoIn.release();
		}
	}

	// Processing loop
	if(isOkay) {
		FRAME_PROCESSOR processor;
		double timeStart, timeNow;
		bool fresh = true;
		namedWindow("Input");
		namedWindow("Output");
		while(true) {
			// Grab input image (if static image, we already have it in imageIn)
			if(!isStaticImage)
				videoIn >> imageIn;

			if(!imageIn.empty()) {
				imshow("Input", imageIn);

				if(fresh) {
					cout << "main(): Image size: " << imageIn.size().width << "x" << imageIn.size().height << endl;
					// Initialize processor, output image
					timeStart = getTickCount() / getTickFrequency();
					processor.initialize(imageIn, imageOut, 0.0); // initialize at 0 secs.
					fresh = false;
				}

				// Process image (if static image, we may not need to process it again, unless there are live parameter changes)
				timeNow = getTickCount() / getTickFrequency() - timeStart;
				processor.process(imageIn, imageOut, timeNow); // time relative to when processor was initialized

				// Show output image
				imshow("Output", imageOut);

				// Delay and window, keyboard event processing
				int key = waitKey(WAITKEY_DELAY);
				if(key == 0x1b) // 0x1b = Escape
					break;
				else {
					switch(key) {
					case 's':
					case 'S':
						// Save output image
						if(isStaticImage) {
							string inFileName = getFileName(filePath);
							string outFilename = getBaseFileName(inFileName) + "-out." + getFileExtension(inFileName);
							string outPath = OUT_DIR + outFilename;
							cout << "main(): Saving to " << outPath << "...";
							if(imwrite(outPath, imageOut))
								cout << "done." << endl;
							else
								cout << "failed." << endl;
						}
						break;

					default:
						processor.onKeyPress(key); // pass all other key events to FrameProcessor
						break;
					}
				}
			}
			else {
				if(!fresh) {
					// indicates that at least one frame was successfully read, so wait for user
					cout << "main(): " << (isLiveVideo ? "No more frames available from camera" : "End of video") << "; press any key to terminate..." << endl;
					waitKey();
				}
				else {
					IFDEBUG(cerr << "main(): Error reading frames from " << (isLiveVideo ? "camera" : "video file") << "; aborting..." << endl;)
				}
				break;
			}
		}
	}
#endif /* defined(RUN_FRAME_PROCESSOR) */
}
