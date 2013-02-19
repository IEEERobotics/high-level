/**
 * @file ColorFilter.cpp
 *
 * @date Sep 25, 2012
 * @author Arpan
 */

#include "ColorFilter.hpp"

void ColorFilter::initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	// * Ensure input image is 8-bit 3-channel (color image)
	CV_Assert(imageIn.type() == CV_8UC3);

	// * Get size of input image, initialize output and HSV images
	imageSize = imageIn.size();
	imageOut.create(imageSize, CV_8UC3);
	imageHSV.create(imageSize, CV_8UC3);

	// * Initialize color swatch
	miniColorSwatchHSV.create(Size(1, 1), CV_8UC3);
	miniColorSwatch.create(Size(1, 1), CV_8UC3);
	colorSwatch.create(Size(50, 50), CV_8UC3);
	colorSwatchROI = Mat(imageOut, Rect(0, 0, colorSwatch.size().width, colorSwatch.size().height));
	updateColorSwatch();

	// * Create trackbar to let user select hue
	namedWindow("Output"); // ensures there is a window named "Output"; if not, creates one
	createTrackbar("Hue", "Output", &hue, HUE_MAX);
}

bool ColorFilter::process(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	// * If hue was changed by user, update color and color swatch
	if(hue != lastHue) {
		color.setHue(hue);
		updateColorSwatch();
		lastHue = hue;
	}

	// * Convert input image to HSV space, clear output image (set all pixels to black)
	cvtColor(imageIn, imageHSV, CV_BGR2HSV);
	imageOut.setTo(0);

	// * Traverse the entire image, pixel by pixel, and copy pixels that match selected color from input image to output image
	MATLOOPBEGIN(Vec3b, imageHSV, imageSize.width, imageSize.height, 1, 1)
		if(color.matches(pixelValue)) {
			imageOut.at<Vec3b>(y, x) = imageIn.at<Vec3b>(y, x);
		}
	MATLOOPEND

	// * Draw color swatch on output image, by copying onto selected ROI
	colorSwatch.copyTo(colorSwatchROI);

	// * Return true to indicate that processing should go on
	return true;
}

void ColorFilter::updateColorSwatch() {
	// * Draw a single pixel in mini HSV swatch with selected hue, full saturation (255) and half brightness/value (128)
	miniColorSwatchHSV.at<Vec3b>(0, 0) = Vec3b(hue, 255, 128);

	// * Convert the mini HSV swatch to BGR
	cvtColor(miniColorSwatchHSV, miniColorSwatch, CV_HSV2BGR);

	// * Set all pixels of larger swatch to the mini swatch color
	colorSwatch.setTo(Scalar(miniColorSwatch.at<Vec3b>(0, 0)));
}
