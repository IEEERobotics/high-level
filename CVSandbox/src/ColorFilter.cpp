/**
 * @file ColorFilter.cpp
 *
 * @date Sep 25, 2012
 * @author Arpan
 */

#include "ColorFilter.hpp"

void ColorFilter::initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	CV_Assert(imageIn.type() == CV_8UC3); // needs to be a color image
	imageSize = imageIn.size();
	imageOut.create(imageSize, CV_8UC3);
	imageHSV.create(imageSize, CV_8UC3);

	miniColorSwatch.create(Size(1, 1), CV_8UC3);
	miniColorSwatchHSV.create(Size(1, 1), CV_8UC3);
	colorSwatch.create(Size(50, 50), CV_8UC3);
	colorSwatchROI = Mat(imageOut, Rect(0, 0, colorSwatch.size().width, colorSwatch.size().height));
	updateColorSwatch();

	namedWindow("Output");
	createTrackbar("Hue", "Output", &hue, HUE_MAX);
}

bool ColorFilter::process(const Mat& imageIn, Mat& imageOut, const double& timeNow) {
	if(hue != lastHue) {
		color.setHue(hue);
		updateColorSwatch();
		lastHue = hue;
	}

	cvtColor(imageIn, imageHSV, CV_BGR2HSV);
	imageOut.setTo(0);
	for(int y = 0; y < imageIn.rows; y++) {
		for(int x = 0; x < imageIn.cols; x++) {
			const Vec3b& hsv = imageHSV.at<Vec3b>(y, x);
			//const int& hue = hsv[0];
			if(color.matches(hsv)) {
				imageOut.at<Vec3b>(y, x) = imageIn.at<Vec3b>(y, x);
			}
		}
	}
	colorSwatch.copyTo(colorSwatchROI);
	return true;
}

void ColorFilter::updateColorSwatch() {
	miniColorSwatchHSV.at<Vec3b>(0, 0) = Vec3b(hue, 255, 128);
	cvtColor(miniColorSwatchHSV, miniColorSwatch, CV_HSV2BGR);
	colorSwatch.setTo(Scalar(miniColorSwatch.at<Vec3b>(0, 0)));
}
