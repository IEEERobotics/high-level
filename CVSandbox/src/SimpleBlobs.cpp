/**
 * Based on: http://nghiaho.com/?p=1102
 */

#include "util.hpp"

void FindBlobs(const Mat &imageIn, vector < vector<Point2i> > &blobs);

int SimpleBlobsDemo(int argc, char **argv) {
	const int minSaturation = 64;
	const int minIntensity = 64; // intensity = value (as in HSV)

	if(argc < 2){
        cerr << "SimpleBlobsDemo(): No image file specified" << endl;
        return -1;
    }

    Mat imageIn = imread(argv[1]);
    if(!imageIn.data) {
        cerr << "SimpleBlobsDemo(): File not found" << endl;
        return -1;
    }

    blur(imageIn, imageIn, Size(5, 5));
    imshow("Input", imageIn);
    Size imageSize = imageIn.size();
    Mat imageOut = Mat::zeros(imageSize, CV_8UC3);

    //Mat imageGray(imageSize, CV_8UC1);
    //cvtColor(imageIn, imageGray, CV_BGR2GRAY);
    //imshow("Grayscale", imageGray);

    //Mat imageThresh;
    //threshold(imageGray, imageThresh, 32, 255, THRESH_TOZERO);
    //imshow("Thresholded", imageThresh);

    Mat imageHSV(imageSize, CV_8UC3);
    cvtColor(imageIn, imageHSV, CV_BGR2HSV);
    blur(imageHSV, imageHSV,Size(5, 5));

    Mat imageArrayHSV[3];
    split(imageHSV, imageArrayHSV);

    // Filter out low-saturated and low-intensity regions
    Mat imageFilter = (imageArrayHSV[1] < minSaturation) | (imageArrayHSV[2] < minIntensity);
    morphologyEx(imageFilter, imageFilter, MORPH_OPEN, getStructuringElement(MORPH_RECT, Size(3, 3)));
    imageHSV.setTo(Scalar::all(0), imageFilter);

    imshow("HSV", imageHSV);
	imshow("Hue", imageArrayHSV[0]);
	imshow("Sat", imageArrayHSV[1]);
	imshow("Val", imageArrayHSV[2]);

    vector<vector<Point2i> > blobs;
    FindBlobs(imageHSV, blobs);
    cout << "SimpleBlobsDemo(): " << blobs.size() << " blobs found" << endl;

    // Randomly color the blobs
    for(size_t i = 0; i < blobs.size(); i++) {
        unsigned char r = 255 * (rand()/(1.0 + RAND_MAX));
        unsigned char g = 255 * (rand()/(1.0 + RAND_MAX));
        unsigned char b = 255 * (rand()/(1.0 + RAND_MAX));

        for(size_t j=0; j < blobs[i].size(); j++) {
            int x = blobs[i][j].x;
            int y = blobs[i][j].y;

            imageOut.at<Vec3b>(y,x)[0] = b;
            imageOut.at<Vec3b>(y,x)[1] = g;
            imageOut.at<Vec3b>(y,x)[2] = r;
        }
    }

    imshow("Labeled", imageOut);
    waitKey(0);

    return 0;
}

void FindBlobs(const Mat &imageIn, vector<vector<Point2i> > &blobs) {
	const size_t minBlobSize = 200;
	const uint maxBlobs = numeric_limits<uint>::max() - 2;

    blobs.clear();

    // Fill the label_image with the blobs
    // 0  - background
    // 1  - unlabelled foreground
    // 2+ - labelled foreground

    Mat image = imageIn; // shallow copy
    Mat imageLabels;
    //image.convertTo(imageLabels, CV_32FC1); // weird it doesn't support CV_32S!
    //image.copyTo(imageLabels);
    imageLabels = Mat::zeros(image.size(), CV_16SC1);

    Mat maskLabeled = Mat::zeros(image.size().height + 2, image.size().width + 2, CV_8UC1);

    uint label_count = 0;
    for(int y=0; y < image.rows; y++) {
        for(int x=0; x < image.cols; x++) {
            if(maskLabeled.at<uchar>(y + 1, x + 1) != 0) {
                continue;
            }

            //Mat blobMask = Mat::zeros(image.size().height + 2, image.size().width + 2, CV_8UC1);
            Mat blobMask = maskLabeled.clone();
            Rect rect;
            floodFill(image, blobMask, Point(x,y), Scalar(255), &rect, Scalar(32, 64, 64), Scalar(32, 64, 64), 4 + FLOODFILL_FIXED_RANGE + FLOODFILL_MASK_ONLY);
            //imshow("Blob Mask", blobMask); waitKey(20);

            Mat maskDiff;
            absdiff(blobMask, maskLabeled, maskDiff);
            //imshow("Current Blob Mask", maskDiff != 0); waitKey(20);

            // Use blobMask and maskDiff to update maskLabeled and imageLabels (note the slight offset)
            maskLabeled |= maskDiff;

            vector<Point2i> blob;
            for(int i = rect.y; i < (rect.y + rect.height); i++) {
                for(int j = rect.x; j < (rect.x + rect.width); j++) {
                    //if((int)imageLabels.at<uchar>(i,j) != label_count) {
                    //    continue;
                    //}

                    if(maskDiff.at<uchar>(i, j) == 0)
                    	continue;

                    blob.push_back(Point2i(j, i));
                    //maskLabeled.at<uchar>(i, j) = 1;
                    //imageLabels.at<uint>(i, j) = label_count;
                }
            }

            if(blob.size() >= minBlobSize) {
				blobs.push_back(blob);

				imageLabels.setTo(Scalar(label_count), maskDiff);

				if(label_count >= maxBlobs) {
					cerr << "FindBlobs(): Too many blobs! Aborting..." << endl;
					return;
				}

				label_count++;
            }
        }
    }
}

