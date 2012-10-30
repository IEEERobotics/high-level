/**
 * @file BlobDetector.hpp
 *
 * @date Oct 19, 2012
 * @author Arpan
 */

#ifndef BLOBDETECTOR_HPP_
#define BLOBDETECTOR_HPP_

#include "util.hpp"
#include "FrameProcessor.hpp"

// Uncomment here, or specify as -D preprocessor arguments to activate different functions
// Ideally, only one or two should be running simultaneously for smooth operation
//#define DO_SEGMENTATION
//#define DO_LINE_DETECTION
#define DO_BLOB_DETECTION
#define DO_GLOBAL_HISTOGRAM

class BlobDetector: public FrameProcessor {
public:
	class Blob {
	public:
		static const float minArea;
		static const float minDensity;
		static const Scalar maxStdDev;

	private:
		Mat contour;
		Mat mask;
		Scalar colorMean;
		Scalar colorStdDev;
		double area;
		Rect rect;
		RotatedRect tightRect;
		Point2f centroid;
		Point2f tightRectPoints[4];

	public:
		inline static double matchBlobs(const Blob& a, const Blob& b) {
			// TODO Incorporate color matching as well, perhaps using a mean-variance scheme
			return matchShapes(a.contour, b.contour, CV_CONTOURS_MATCH_I2, 0);
		}

		Blob() {
		}

		Blob(Mat contour_, Mat mask_, Scalar colorMean_, Scalar colorStdDev_) :
				contour(contour_), mask(mask_), colorMean(colorMean_), colorStdDev(
						colorStdDev_) {
			update();
		}

		inline void update() {
			area = contourArea(contour);
			rect = boundingRect(contour);
			tightRect = minAreaRect(contour);
			centroid = tightRect.center; // centroid using moments is more accurate
			tightRect.points(tightRectPoints); // obtain corner points, useful for rendering
		}

		inline void renderTo(Mat& imageOut,
				const Scalar& rectColor = Scalar(255, 255, 255)) {
			imageOut.setTo(colorMean, mask); // draw blob with constant average color
			//rectangle(imageOut, rect, rectColor, 1); // draw bounding rectangle (axis-aligned)
			drawPolygon(imageOut, tightRectPoints, 4, rectColor, 2); // draw tight rectangle (possibly rotated)
		}

		inline string toString() {
			stringstream out;
			out << "Blob[contour-size = " << max(contour.rows, contour.cols)
					<< ", area = " << area << "]";
			return out.str();
		}

		Mat getContour() const {
			return contour;
		}

		void setContour(Mat contour) {
			this->contour = contour;
		}

		Mat getMask() const {
			return mask;
		}

		void setMask(Mat mask) {
			this->mask = mask;
		}

		Scalar getColorMean() const {
			return colorMean;
		}

		void setColorMean(Scalar colorMean) {
			this->colorMean = colorMean;
		}

		Scalar getColorStdDev() const {
			return colorStdDev;
		}

		void setColorStdDev(Scalar colorStdDev) {
			this->colorStdDev = colorStdDev;
		}

		Rect getRect() const {
			return rect;
		}

		float getArea() const {
			return area;
		}

		RotatedRect getTightRect() const {
			return tightRect;
		}

		Point2f getCentroid() const {
			return centroid;
		}

		const Point2f* getTightRectPoints() const {
			return tightRectPoints;
		}
	};

	typedef vector<Vec4i> Segments_t;
	typedef vector<vector<Point> > Contours_t;
	typedef vector<Blob> Blobs_t;

private:
	static const float hueRange[];
	static const float satRange[];

	static const int filterMinSaturation;
	static const int filterMinValue;

	double timeStart;
	double timeCurrent;
	double timeLast;
	double timeElapsed;

	Size imageSize;
	int imageType;

	Mat image; // working image object
	Mat imageGray; // grayscale
	Mat imageHSV; // HSV
	Mat imageArrayHSV[3]; // HSV split into 3 separate images (note: does not share data with imageHSV)
	//Mat imageLab; // L*a*b*
	//Mat imageArrayLab[3]; // L*a*b* split into 3 separate images (note: does not share data with imageLab)
	//int lLow; // lower bound on L* value
	//int lHigh; // upper bound on L* value
	Mat imageMask; // inclusion mask
	Mat imageFilter; // exclusion filter

#ifdef DO_SEGMENTATION
	Rect gcROI;
	Mat gcMask;
	Mat bgModel, fgModel;
	bool isGCInitialized;
#endif /* DO_SEGMENTATION */

#ifdef DO_LINE_DETECTION
	//Mat imageBinary; // binary image, typically after thresholding grayscale image
	Mat imageEdges; // binary image, result of edge-detection/gradient-thresholding
#endif /* DO_LINE_DETECTION */

#ifdef DO_GLOBAL_HISTOGRAM
	static const int histNumDims;
	static const int histChannels[];
	static const int hueBins;
	static const int satBins;
	static const int histSize[];
	static const float* histRanges[];
	static const float hueBinSize;
	static const float satBinSize;
	static const int histDisplayScale;

	Mat globalHist; // global histogram matrix

	static const string histInputWinName;
	static const string histWinName;
	static const int hueMargin;
	static const int satMargin;

	volatile int selectedHue;
	volatile int selectedSat;
	volatile bool drawFlag;
	volatile bool clearFlag;
#endif /* DO_GLOBAL_HISTOGRAM */

public:
	BlobDetector() { }
	void initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow);
	bool process(const Mat& imageIn, Mat& imageOut, const double& timeNow);
	void onMouseEvent(int event, int x, int y, int flags, void* param = NULL);
};

#endif /* BLOBDETECTOR_HPP_ */
