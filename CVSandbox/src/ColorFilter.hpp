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

class ColorFilter: public FrameProcessor {
public:
	class Color {
		int hue;
		int hueMargin;
		int minSaturation;

	public:
		Color(int hue_, int hueMargin_, int minSaturation_ = 32): hue(hue_), hueMargin(hueMargin_), minSaturation(minSaturation_) { }

		bool matches(const int& h) {
			int diff = abs(h-hue);
			if(diff > HUE_MAX / 2) diff = HUE_MAX - diff; // account for hue wrap-around
			return (diff <= hueMargin);
		}

		bool matches(const Vec3b& hsv) {
			return (hsv[1] >= minSaturation && matches(hsv[0]));
		}

		int getHue() const { return hue; }
		void setHue(int hue) { this->hue = hue; }
		int getMargin() const { return hueMargin; }
		void setMargin(int hueMargin) { this->hueMargin = hueMargin; }
	};

private:
	Size imageSize;
	Mat imageHSV;

	Color color;
	int hue, lastHue; // user-controlled
	Mat miniColorSwatch;
	Mat miniColorSwatchHSV;
	Mat colorSwatch;
	Mat colorSwatchROI;

public:
	ColorFilter(const Color& color_ = Color(HUE_MAX / 2, HUE_MAX / 12)): color(color_) { hue = lastHue = color.getHue(); }
	void initialize(const Mat& imageIn, Mat& imageOut, const double& timeNow);
	bool process(const Mat& imageIn, Mat& imageOut, const double& timeNow);

	Color& getColor() { return color; }
	void setColor(const Color& color) { this->color = color; }

	void updateColorSwatch();
};

#endif /* COLORFILTER_HPP_ */
