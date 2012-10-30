/**
 * @file EMClusteringDemo.cpp
 * Illustrates how to perform color-based clustering using OpenCV's Expectation-Maximization (EM) model.
 *
 * @date Oct 20, 2012
 * @author Arpan
 */

#include "util.hpp"
#include <opencv2/ml/ml.hpp>

int EMClusteringDemo(int argc, char** argv) {
	if(argc < 2)
		return -1;

	Mat imageIn = imread(argv[1]);

	const int N = 6;
	const int N1 = (int)sqrt((double)N);
	const Scalar colors[] =
	{
			Scalar(0,0,255), Scalar(0,255,0),
			Scalar(0,255,255),Scalar(255,255,0)
	};

	int i, j;
	int nsamples = 1000;
	Mat samples( nsamples, 5, CV_32FC1 );
	Mat labels;
	Mat img = imageIn; // Mat::zeros( Size( 500, 500 ), CV_8UC3 );
	Mat sample( 1, 5, CV_32FC1 );
	CvEM em_model;
	CvEMParams params;

	samples = samples.reshape(5, 0);
	/*for( i = 0; i < N; i++ )
	{
		// form the training samples
		Mat samples_part = samples.rowRange(i*nsamples/N, (i+1)*nsamples/N );

		Scalar mean(((i%N1)+1)*img.rows/(N1+1),
				((i/N1)+1)*img.rows/(N1+1));
		Scalar sigma(30,30);
		randn( samples_part, mean, sigma );
	}*/

	for(int i = 0; i < nsamples; i++) {
		int x = rand() % img.size().width, y = rand() % img.size().height;
		Vec3b pixelValue = img.at<Vec3b>(y, x);
		samples.at<Vec<float, 5> >(i) = Vec<float, 5>(x, y, pixelValue[0], pixelValue[1], pixelValue[2]);
	}

	samples = samples.reshape(1, 0);

	//Mat imageGray(imageIn.size(), CV_8UC1);
	//cvtColor(imageIn, imageGray, CV_BGR2GRAY);

	//Mat imageGray32FC1(imageIn.size(), CV_32FC1);
	//imageGray.convertTo(imageGray32FC1, imageGray32FC1.type());

	//samples = imageGray32FC1.reshape(1, 0);

	// initialize model parameters
	params.covs      = NULL;
	params.means     = NULL;
	params.weights   = NULL;
	params.probs     = NULL;
	params.nclusters = N;
	params.cov_mat_type       = CvEM::COV_MAT_SPHERICAL;
	params.start_step         = CvEM::START_AUTO_STEP;
	params.term_crit.max_iter = 300;
	params.term_crit.epsilon  = 0.1;
	params.term_crit.type     = CV_TERMCRIT_ITER|CV_TERMCRIT_EPS;

	// cluster the data
	em_model.train( samples, Mat(), params, &labels );

#if 0
	// the piece of code shows how to repeatedly optimize the model
	// with less-constrained parameters
	//(COV_MAT_DIAGONAL instead of COV_MAT_SPHERICAL)
	// when the output of the first stage is used as input for the second one.
	CvEM em_model2;
	params.cov_mat_type = CvEM::COV_MAT_DIAGONAL;
	params.start_step = CvEM::START_E_STEP;
	params.means = em_model.get_means();
	params.covs = (const CvMat**)em_model.get_covs();
	params.weights = em_model.get_weights();

	em_model2.train( samples, Mat(), params, &labels );
	// to use em_model2, replace em_model.predict()
	// with em_model2.predict() below
#endif
	Mat imageOut = Mat::zeros(img.size(), CV_8UC3);
	// classify every image pixel
	for( i = 0; i < img.rows; i++ )
	{
		for( j = 0; j < img.cols; j++ )
		{
			sample.at<float>(0) = (float) j;
			sample.at<float>(1) = (float) i;

			Vec3b pixelValue = img.at<Vec3b>(i, j);
			sample.at<float>(2) = (float) pixelValue[0];
			sample.at<float>(3) = (float) pixelValue[1];
			sample.at<float>(4) = (float) pixelValue[2];

			int response = cvRound(em_model.predict( sample ));
			Scalar c = colors[response];

			circle( imageOut, Point(j, i), 1, c*0.5, CV_FILLED );
		}
	}

	//draw the clustered samples
	for( i = 0; i < nsamples; i++ )
	{
		Point pt(cvRound(samples.at<float>(i, 0)), cvRound(samples.at<float>(i, 1)));
		circle( imageOut, pt, 1, colors[labels.at<int>(i)], CV_FILLED );
	}

	imshow("Input", img);
	imshow("EM-clustering result", imageOut);
	waitKey(0);

	return 0;
}



