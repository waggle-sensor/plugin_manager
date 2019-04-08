/* ANL:waggle-license */
/* This file is part of the Waggle Platform.  Please see the file
 * LICENSE.waggle.txt for the legal details of the copyright and software
 * license.  For more details on the Waggle project, visit:
 *          http://www.wa8.gl
 */
/* ANL:waggle-license */
/*
 * blur_kernel smoothes a grayscale image by convolving each pixel with a 3x3 Gaussian kernel
 * Input: Image w/ 8-bit 1-channel data
 * Output: smoothed image w/ 8-bit 1-channel data
 */

#pragma OPENCL EXTENSION cl_khr_fp64 : enable

//Gaussian kernel
__constant float gaussian[3][3] = {{0.0625, 0.125, 0.0625},
				   {0.125, 0.250, 0.125},
				   {0.0625, 0.125, 0.0625}};

//Main kernel
__kernel void gaussian_blur_kernel(__global uchar* in,
			      __global uchar* out,
			      const int rows,
			      const int cols)
{
	int value = 0;
	size_t col = get_global_id(0);
	size_t row = get_global_id(1);
	size_t pos = row*cols + col;

	//Apply the Gaussian kernel to the surrounding patch of pixels
	for(int i = 0; i < 3; i++)
	{
		for(int j = 0; j < 3; j++)
		{
			value += gaussian[i][j]*in[(i + row - 1)*cols + (j + col - 1)];
		}
	}

	out[pos] = min(255, max(0, value));
}
