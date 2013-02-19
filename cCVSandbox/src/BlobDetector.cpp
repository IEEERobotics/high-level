/**
 * @file BlobDetector.cpp
 *
 * @date Oct 19, 2012
 * @author Arpan
 */

#include "BlobDetector.hpp"

const float BlobDetector::Blob::minArea = 500;
const float BlobDetector::Blob::minDensity = 0.5;
const Scalar BlobDetector::Blob::maxStdDev = Scalar::all(64);

const float BlobDetector::hueRange[2] = { 0, 180 };
const float BlobDetector::satRange[2] = { 0, 256 };

const int BlobDetector::filterMinSaturation = 50; // minimum saturation used to filter out unwanted pixels
const int BlobDetector::filterMinValue = 64; // minimum value/intensity (as in HSV)

#ifdef DO_GLOBAL_HISTOGRAM
const int BlobDetector::histNumDims = 2;
const int BlobDetector::histChannels[histNumDims] = { 0, 1 }; // hue and saturation channels from an HSV image
const int BlobDetector::hueBins = 64;
const int BlobDetector::satBins = 64;
const int BlobDetector::histSize[histNumDims] = { hueBins, satBins };
const float* BlobDetector::histRanges[histNumDims] = { hueRange, satRange };
const float BlobDetector::hueBinSize = (hueRange[1] - hueRange[0]) / hueBins;
const float BlobDetector::satBinSize = (satRange[1] - satRange[0]) / satBins;
const int BlobDetector::histDisplayScale = 4;

const string BlobDetector::histInputWinName = "Image";
const string BlobDetector::histWinName = "Hue-Sat Histogram";
const int BlobDetector::hueMargin = 16; // note: this is margin on either side, i.e. range of selection is selectedHue +/- hueMargin
const int BlobDetector::satMargin = 64; // note: see note above (for hueMargin); same here
#endif /* DO_GLOBAL_HISTOGRAM */

void BlobDetector::initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	CV_Assert(imageIn.type() == CV_8UC3); // needs to be a color image

	// * Member initializations
	// ** Timing
	timeLast = timeCurrent = timeStart = timeNow;

	// ** Image attributes, buffers
	imageSize = imageIn.size();
	imageType = imageIn.type();
	image.create(imageSize, CV_8UC3);
	imageOut.create(imageSize, CV_8UC3);

	imageGray.create(imageSize, CV_8UC1);
	imageHSV.create(imageSize, CV_8UC3);
	//imageLab.create(imageSize, CV_8UC3);

	// ** L*a*b*-based Filtering
	//lLow = 64;
	//lHigh = 200;
	//namedWindow("L*a*b* Mask");
	//createTrackbar("L* low", "L*a*b* Mask", &lLow, 255);
	//createTrackbar("L* high", "L*a*b* Mask", &lHigh, 255);

#ifdef DO_SEGMENTATION
	// ** Segmentation: GrabCut algorithm
	gcROI = Rect(10, 10, imageSize.width - 20, imageSize.height - 20); // leave some border areas out
	gcMask.create(imageSize, CV_8UC1);
	gcMask.setTo(Scalar(GC_BGD));
	gcMask(gcROI).setTo(Scalar(GC_PR_FGD));
	isGCInitialized = false; // will be set to true on first run
#endif /* DO_SEGMENTATION */

#ifdef DO_LINE_DETECTION
	// ** Line detection
	//imageBinary.create(imageSize, CV_8UC1);
	imageEdges.create(imageSize, CV_8UC1);
#endif /* DO_LINE_DETECTION */

#ifdef DO_GLOBAL_HISTOGRAM
	// ** Global histogram computation
	selectedHue = -1;
	selectedSat = -1;
	drawFlag = false;
	clearFlag = false;
	namedWindow(histInputWinName);
	cvSetMouseCallback(histInputWinName.c_str(), passMouseEvent<0>, this);
	namedWindow(histWinName);
	cvSetMouseCallback(histWinName.c_str(), passMouseEvent<1>, this);
#endif /* DO_GLOBAL_HISTOGRAM */
}

bool BlobDetector::process(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	// * Timing
	timeCurrent = timeNow;
	timeElapsed = timeCurrent - timeLast;
	cout << "BlobDetector::process(): " << (timeElapsed > 0.0 ? 1.0 / timeElapsed : 0.0) << " fps" << endl;

	// * Pre-processing
	// ** Make a copy of input image for modification, clear output image
	imageIn.copyTo(image);
	imageOut.setTo(Scalar::all(0));

	// ** Blur input image to remove noise
	blur(image, image, Size(5, 5));

	// ** Convert to grayscale
	//cvtColor(image, imageGray, CV_BGR2GRAY);

	// ** Convert to HSV color space
	cvtColor(image, imageHSV, CV_BGR2HSV);
	split(imageHSV, imageArrayHSV); // split into 3 planes (images): hue, saturation, value

	// ** Convert to L*a*b* color space
	//cvtColor(image, imageLab, CV_BGR2Lab);
	//split(imageLab, imageArrayLab); // split into 3 planes (images): L*, a*, b*

	// * Enhancement
	// ** Equalize value histogram to boost brightness, colors
	//equalizeHist(imageArrayHSV[2], imageArrayHSV[2]);
	//int fromTo[] = { 2, 2 };
	//mixChannels(imageArrayHSV, 3, &imageHSV, 1, fromTo, 1);
	//Mat imageBGR(imageSize, CV_8UC3);
	//cvtColor(imageHSV, imageBGR, CV_HSV2BGR);
	//imshow("Enhanced Image", imageBGR);

	// * Filtering
	// ** HSV-based filtering
	// *** Create mask that excludes low-saturated and low-intensity regions
	inRange(imageHSV, Scalar(hueRange[0], filterMinSaturation, filterMinValue), Scalar(hueRange[1], satRange[1], 256), imageMask);

	// *** Create mask that includes all white regions, i.e. low-saturation, high-intensity
	Mat imageWhiteMask;
	inRange(imageHSV, Scalar(hueRange[0], satRange[0], 150), Scalar(hueRange[1], filterMinSaturation, 256), imageWhiteMask);

	// ** L*a*b*-based filtering: Create mask that excludes low-lightness regions
	//Mat imageLabMask;
	//inRange(imageLab, Scalar(lLow, 0, 0), Scalar(lHigh, 256, 256), imageLabMask);

	// ** Enhance mask(s) using morphological operations
	morphologyEx(imageMask, imageMask, MORPH_OPEN, getStructuringElement(MORPH_RECT, Size(5, 5)), Point(-1, -1), 2);
	//imshow("Mask", imageMask);
	//morphologyEx(imageLabMask, imageLabMask, MORPH_OPEN, getStructuringElement(MORPH_RECT, Size(5, 5)), Point(-1, -1), 2);
	//imshow("L*a*b* Mask", imageLabMask);
	morphologyEx(imageWhiteMask, imageWhiteMask, MORPH_OPEN, getStructuringElement(MORPH_RECT, Size(3, 3)));
	imshow("White Mask", imageWhiteMask);

	// ** Create exclusion filter, simply an inverse of the mask
	imageFilter = 255 - imageMask;
	//imshow("Filter", imageFilter);

	// ** Apply filter to remove excluded regions from image(s)
	image.setTo(Scalar::all(0), imageFilter);
	//imageGray.setTo(Scalar::all(0), imageFilter);
	imageHSV.setTo(Scalar::all(0), imageFilter);
	//imageLab.setTo(Scalar::all(0), imageFilter);

	// * Show pre-processed, filtered image(s)
	//imshow("Image", image);
	//imshow("HSV", imageHSV);
	//imshow("Hue", imageArrayHSV[0]);
	//imshow("Saturation", imageArrayHSV[1]);
	//imshow("Value", imageArrayHSV[2]);

#ifdef DO_SEGMENTATION
	// * Segmentation
	// ** Execute GrabCut segmentation algorithm (one iteration of it)
	if(isGCInitialized)
		grabCut(image, gcMask, gcROI, bgModel, fgModel, 1);
	else
		grabCut(image, gcMask, gcROI, bgModel, fgModel, 1, GC_INIT_WITH_RECT);

	// ** Visualize GrabCut intermediate results and prepare final output
	//imshow("GC Mask", gcMask);
	//imshow("BG Model", bgModel);
	//imshow("FG Model", fgModel);
	image.copyTo(imageOut, gcMask == GC_PR_FGD);
	rectangle(imageOut, gcROI, Scalar(0, 255, 0), 2);
#endif /* DO_SEGMENTATION */

#ifdef DO_LINE_DETECTION
	// * Line detection
	// ** Adaptive threshold
	//adaptiveThreshold(imageGray, imageBinary, 255, CV_ADAPTIVE_THRESH_MEAN_C, CV_THRESH_BINARY, 25, 0);

	// ** Edge-detection
	Canny(imageWhiteMask, imageEdges, 30, 60); // use imageGray for all lines in image, or imageMask for blob/region outlines only, or imageWhiteMask for white regions only
	//dilate(imageEdges, imageEdges, getStructuringElement(MORPH_RECT, Size(3, 3)));
	imshow("Edges", imageEdges);

	// ** Medial-axis/distance transform
	Mat imageDistTransform = Mat::zeros(imageSize, CV_32FC1);
	distanceTransform(imageWhiteMask, imageDistTransform, CV_DIST_L1, 3);
	normalize(imageDistTransform, imageDistTransform, 0, 255, NORM_MINMAX, CV_8UC1);
	imshow("Distance Transform", imageDistTransform);
	Mat imageSkeleton = Mat::zeros(imageSize, CV_32FC1);
	adaptiveThreshold(imageDistTransform, imageSkeleton, 255, CV_ADAPTIVE_THRESH_GAUSSIAN_C, CV_THRESH_BINARY, 9, 0);
	//Canny(imageDistTransform, imageSkeleton, 30, 60);
	imshow("Skeleton", imageSkeleton);

	// ** Line segment detection using Hough Transform
	Segments_t segments;
	HoughLinesP(imageEdges, segments, 3, 3 * CV_PI / 180, 100, 50, 20); // look for long and solid lines, with less emphasis on accuracy
	cout << "BlobDetector::process(): " << segments.size() << " line segments" << endl;
	for( size_t i = 0; i < segments.size(); i++ ) {
		line(imageOut, Point(segments[i][0], segments[i][1]), Point(segments[i][2], segments[i][3]), Scalar(rand() % 255, rand() % 255, rand() % 255), 3);
	}

	// ** TODO Line segment resolution to combine duplicate and overlapping lines

#endif /* DO_LINE_DETECTION */

#ifdef DO_BLOB_DETECTION
	// * Blob detection
	// ** Find contours
	Mat imageContours = imageMask.clone(); // find contours in mask; deep copy, since findContours() modifies the image
	Contours_t contours;
	findContours(imageContours, contours, CV_RETR_LIST, CV_CHAIN_APPROX_TC89_KCOS);
	IFDEBUG(cout << "BlobDetector::process(): " << contours.size() << " contours" << endl;)

	// ** Analyze and filter out unsuitable contours; create blob objects
	Blobs_t blobs;
	for(Contours_t::size_type i = 0; i < contours.size(); i++) {
		Contours_t::reference contour = contours[i];

		// Blob-creation method #1: Create and compute (works only if members are public)
		//Blobs_t::value_type blob;
		//blob.contour = contour;
		//blob.mask = Mat::zeros(imageSize, CV_8UC1);
		//drawContours(blob.mask, contours, i, Scalar(255), CV_FILLED);
		//blob.colorMean = mean(image, blob.mask);
		//blob.update();

		// Blob-creation method #2: Compute and create
		Mat imageContourMask = Mat::zeros(imageSize, CV_8UC1);
		drawContours(imageContourMask, contours, i, Scalar(255), CV_FILLED);
		Mat imageBlob = Mat::zeros(imageSize, imageType);
		Scalar colorMean;
		Scalar colorStdDev;
		meanStdDev(image, colorMean, colorStdDev, imageContourMask);

		Blobs_t::value_type blob(Mat(contour), imageContourMask, colorMean, colorStdDev);
		IFDEBUG(cout << "BlobDetector::process(): Candidate blob: color mean = " << toString(blob.getColorMean()) << ", s.d. = " << toString(blob.getColorStdDev()) << endl;)

		// Filter out unwanted blobs
		// TODO implement better and more comprehensive filtering, e.g. to drop regions with significant hole areas or inconsistent colors
		if(blob.getArea() >= Blob::minArea
				&& (blob.getArea() / blob.getTightRect().size.area()) >= Blob::minDensity /* note: this favors rectangular shape; for a more generic density filter, compare blob area with area of its convex hull */
				&& (blob.getColorStdDev()[0] <= Blob::maxStdDev[0] && blob.getColorStdDev()[1] <= Blob::maxStdDev[1] && blob.getColorStdDev()[2] <= Blob::maxStdDev[2]))
			blobs.push_back(blob);
	}

	// ** Visualize blobs
	cout << "BlobDetector::process(): " << blobs.size() << " blobs" << endl;
	for(Blobs_t::size_type i = 0; i < blobs.size(); i++) {
		Blobs_t::reference blob = blobs[i];

		blob.renderTo(imageOut);
		putText(imageOut, toString(i), blob.getCentroid(), FONT_HERSHEY_SIMPLEX, 0.8, Scalar(255, 255, 255), 2);
		IFDEBUG(cout << "BlobDetector::process(): \t#" << i << ": " << blob.toString() << endl;)
	}
#endif /* DO_BLOB_DETECTION */

	// * TODO Use MSER analysis to extract colored blobs

#ifdef DO_GLOBAL_HISTOGRAM
	// * Global histogram computation
	// ** Compute global histogram
	calcHist(&imageHSV, 1, histChannels, imageMask, globalHist, histNumDims, histSize, histRanges, true, false);
	//cout << "BlobDetector::process(): hist size = " << hist.cols << "x" << hist.rows << ", type = " << hist.type() << " (CV_32FC1 = " << CV_32FC1 << ")" << ", depth = " << hist.depth() << endl;

	// ** Visualize histogram: 1-D
	/*Mat imageHist(hueBins * histDisplayScale, satBins * histDisplayScale, CV_32FC1, Scalar(0));
	for(int i = 0; i < histSizes[0]; i++) {
		for(int j = 0; j < histSizes[1]; j++) {
			rectangle(imageHist, Rect(j * histDisplayScale, i * histDisplayScale, (j + 1) * histDisplayScale, (i + 1) * histDisplayScale), Scalar(cvRound(hist.at<float>(i, j))), CV_FILLED);
		}
	}
	Mat imageHistNormalized(imageHist.size(), imageHist.type());
	normalize(imageHist, imageHistNormalized, 0, 255, NORM_MINMAX);*/

	// ** Visualize histogram: 2-D
	Mat histNormalized(globalHist.size(), globalHist.type());
	normalize(globalHist, histNormalized, 0, 1, NORM_MINMAX);
	Mat imageHistHSV(hueBins * histDisplayScale, satBins * histDisplayScale, CV_8UC3, Scalar(0, 0, 0)); // rows => hue, cols => sat
	for(int i = 0; i < histSize[0]; i++) {
		for(int j = 0; j < histSize[1]; j++) {
			rectangle(imageHistHSV, Rect(j * histDisplayScale, i * histDisplayScale, (j + 1) * histDisplayScale, (i + 1) * histDisplayScale), Scalar((i + 0.5) * hueBinSize, (j + 0.5) * satBinSize, cvRound(globalHist.at<float>(i, j))), CV_FILLED);
		}
	}
	Mat imageHistBGR(imageHistHSV.size(), CV_8UC3);
	cvtColor(imageHistHSV, imageHistBGR, CV_HSV2BGR);

	imshow(histInputWinName, image);
	imshow(histWinName, imageHistBGR);
	//imshow("Global Histogram", globalHist); // show raw histogram matrix

	// ** Render user-selected region
	// *** Clear output, if instructed
	if(clearFlag) {
		imageOut.setTo(Scalar::all(0));
		clearFlag = false;
	}

	// *** Filter image using selected hue-saturation coordinates
	if(drawFlag && selectedHue >= 0 && selectedHue <= 180 && selectedSat >= 0 && selectedSat <= 255) {
		Mat selectedMask;
		inRange(imageHSV, Scalar(max(float(selectedHue - hueMargin), hueRange[0]), max(float(selectedSat - satMargin), satRange[0]), 0), Scalar(min(float(selectedHue + hueMargin), hueRange[1]), min(float(selectedSat + satMargin), satRange[1]), 256), selectedMask);
		image.copyTo(imageOut, selectedMask);
	}
#endif /* DO_GLOBAL_HISTOGRAM */

	// * TODO Local histogram computation, connected component analysis using histogram matching, robust blob detection

	// * TODO Blob matching and tracking across frames

	// * Timing
	timeLast = timeCurrent;

	return true;
}

// TODO Abstract out mouse-event processing functionality into MouseEventListener interface (abstract class) and have BlobDetector implement it
void BlobDetector::onMouseEvent(int event, int x, int y, int flags, void* param) {
	int winId = -1;
	if(param != NULL) {
		winId = *(static_cast<int*>(param));
		//cout << "BlobDetector::onMouseEvent(): @(" << x << ", " << y << "), window #" << winId << endl;
	}

	switch(winId) {
#ifdef DO_GLOBAL_HISTOGRAM
		case 0: {
			// Image window
			switch(event) {
				case CV_EVENT_LBUTTONUP: {
					// Left-click to select hue, sat from image
					Vec3b pixelHSV = imageHSV.at<Vec3b>(y, x);
					selectedHue = pixelHSV[0];
					selectedSat = pixelHSV[1];
					float histValue = globalHist.at<float>(selectedHue / hueBinSize, selectedSat / satBinSize);
					cout << "BlobDetector::onMouseEvent(): [CLICK] @(" << x << ", " << y << "), window #" << winId <<" (Image): Selected hue = " << selectedHue << ", sat = " << selectedSat << ", count = " << histValue << endl;
					drawFlag = true;
				}
				break;

				case CV_EVENT_RBUTTONUP: {
					// Right-click to clear
					clearFlag = true;
					drawFlag = false;
					selectedHue = -1;
					selectedSat = -1;
				}
				break;
			}
		}
		break;

		case 1: {
			// Hue-Saturation selection window
			switch(event) {
				case CV_EVENT_LBUTTONUP: {
					// Left-click to select hue, sat from histogram grid
					selectedHue = (y / histDisplayScale + 0.5) * hueBinSize;
					selectedSat = (x / histDisplayScale + 0.5) * satBinSize;
					float histValue = globalHist.at<float>(selectedHue / hueBinSize, selectedSat / satBinSize);
					cout << "BlobDetector::onMouseEvent(): [CLICK] @(" << x << ", " << y << "), window #" << winId <<" (Histogram): Selected hue = " << selectedHue << ", sat = " << selectedSat << ", count = " << histValue << endl;
					drawFlag = true;
				}
				break;

				case CV_EVENT_RBUTTONUP: {
					// Right-click to clear
					clearFlag = true;
					drawFlag = false;
					selectedHue = -1;
					selectedSat = -1;
				}
				break;
			}
		}
		break;
#endif /* DO_GLOBAL_HISTOGRAM */

		default:
			// Unknown window
			switch(event) {
				case CV_EVENT_LBUTTONUP:
				case CV_EVENT_RBUTTONUP:
					cout << "BlobDetector::onMouseEvent(): @(" << x << ", " << y << "), unknown window" << endl;
				break;
			}
		break;
	}
}
