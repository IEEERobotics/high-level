/**
 * @file ColorFilter.hpp
 *
 * @date Sep 25, 2012
 * @author Arpan
 */

#ifndef COLORFILTER_HPP_
#define COLORFILTER_HPP_

#include "util.hpp"
#include "FrameProcessor.hpp"

#define HUE_MAX 180
#define HALF_HUE_MAX HUE_MAX / 2

/**
 * Performs hue/saturation-based color filtering, accounting for hue wrap-around.
 */
class ColorFilter: public FrameProcessor {
public:
	/**
	 * Represents a color specified as a hue (between 0 to 180 degrees), with +/- hueMargin variation, and a minimum saturation level (minSat).
	 */
	class HSVColor {
		int hue;
		int hueMargin;
		int minSat;

	public:
		HSVColor(int hue_, int hueMargin_, int minSat_ = 32): hue(hue_), hueMargin(hueMargin_), minSat(minSat_) { }

		bool matches(const int& h) {
			int diff = abs(h-hue);
			if(diff > HALF_HUE_MAX) diff = HUE_MAX - diff; // account for hue wrap-around
			return (diff <= hueMargin);
		}

		bool matches(const Vec3b& hsv) {
			return (hsv[1] >= minSat && matches(hsv[0]));
		}

		int getHue() const { return hue; }
		void setHue(int hue) { this->hue = hue; }
		int getMargin() const { return hueMargin; }
		void setMargin(int hueMargin) { this->hueMargin = hueMargin; }
	};

private:
	Size imageSize; ///< Base size of all input and output frames (images).
	Mat imageHSV; ///< Current image being processed, transformed to HSV space.

	HSVColor color; ///< The color this filter is currently tuned to.
	int hue, lastHue; ///< User-controlled hue, selected using a trackbar.

	Mat miniColorSwatchHSV; ///< 1x1 HSV image to draw the currently selected color on.
	Mat miniColorSwatch; ///< 1x1 BGR image to convert miniColorSwatchHSV to BGR space.
	Mat colorSwatch; ///< Larger BGR image to be filled with currently selected color (from miniColorSwatch)
	Mat colorSwatchROI; ///< Selected region-of-interest (ROI) within output image where colorSwatch is to be drawn (e.g. in the upper-left corner, same size as colorSwatch).

public:
	ColorFilter(const HSVColor& color_ = HSVColor(HUE_MAX / 2, HUE_MAX / 12)): color(color_) { hue = lastHue = color.getHue(); }
	void initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow);
	bool process(const Mat& imageIn, Mat& imageOut, const double& timeNow);

	HSVColor& getColor() { return color; }
	void setColor(const HSVColor& color) { this->color = color; }

	void updateColorSwatch();
};

#endif /* COLORFILTER_HPP_ */
