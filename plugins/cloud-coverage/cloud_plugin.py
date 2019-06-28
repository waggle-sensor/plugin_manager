#!/usr/bin/python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

import os
import time
import argparse

import cv2 as cv
import numpy as np

from sklearn.cross_decomposition import PLSRegression

import joblib

#from waggle.pipeline import Plugin, ImagePipelineHandler
#from waggle.protocol.v5.encoder import encode_frame

# Configuration of the pipeline
# name of the pipeline
EXCHANGE = 'image_pipeline'

# output direction of this processor
ROUTING_KEY_EXPORT = 'exporter'  # flush output to Beehive

# test images path
test_path = '/home/waggle-student/waggle/tcs_cloud/test1/'

# temporary image path
TEMP_IMAGE_PATH = '0017.png'

# Model name
MODEL_NAME = 'swimseg_model_128.pkl'

class CloudEstimator():
#class CloudEstimator(Plugin):
    plugin_name = 'image_cloud_estimator'
    plugin_version = '0'
    
    def __init__(self):
        super().__init__()
        #self.hrf = False
        #self.input_handler = ImagePipelineHandler(routing_in=self.config['source'])
        #self.input_image_path = image_name 
        
    '''
    def close(self):
        self.input_handler.close()
    '''

    def Feature_Generator(self, path):
        Input_Image = cv.imread(path)
        Input_Image_RGB = cv.cvtColor(Input_Image, cv.COLOR_BGR2RGBA)
        Input_Image_RGB = Input_Image

        Input_Image_HSV = cv.cvtColor(Input_Image, cv.COLOR_BGR2HSV)

        Image_Array_RGB = np.array(Input_Image_RGB)
        Image_Array_HSV = np.array(Input_Image_HSV)
        
        Image_Shape = Image_Array_RGB.shape
        Pixels_Count = Image_Shape[0] * Image_Shape[1]

        Input_Image_Red = Image_Array_RGB[:,:,2]
        Input_Image_Blue = Image_Array_RGB[:, :, 0]

        Input_Image_Difference = Input_Image_Red / Input_Image_Blue * 100

        One_D_Image_Red = np.transpose(np.matrix(Image_Array_RGB[:, :, 2].ravel()))
        One_D_Image_Blue = np.transpose(np.matrix(Image_Array_RGB[:, :, 0].ravel()))

        One_D_Image_Red = One_D_Image_Red.astype(np.int16)
        One_D_Image_Blue = One_D_Image_Blue.astype(np.int16)

        One_D_Image_S = np.transpose(np.matrix(Image_Array_HSV[:, :, 1].ravel()))

        One_D_Image_Blue[One_D_Image_Blue == 0] = 1

        ratio = One_D_Image_Red / (One_D_Image_Blue)
        One_D_Image_RATIO = ratio
        ratio = np.reshape(ratio, (Image_Shape[0], Image_Shape[1]))
        img_ratio = np.array(ratio * 255, dtype=np.uint8)

        One_D_Image_DIFF = One_D_Image_Red - One_D_Image_Blue

        One_D_Image_NORMALIZED = ( One_D_Image_Blue - One_D_Image_Red ) / (One_D_Image_Blue + One_D_Image_Red)
    
        One_D_Image = np.hstack((One_D_Image_S, \
                    One_D_Image_RATIO, \
                    One_D_Image_NORMALIZED, \
                    ))

        return One_D_Image, Image_Shape

    def PLS_Regression(self, features, labels, image_shape):
        X = features
        y = labels

        pls2 = PLSRegression(n_components=3)
        pls2.fit(X,y)
        Y_pred = pls2.predict(features)
        
        return Y_pred

    def Load_Ground_Truth_Label(self, Image_Name, Image_Shape):

        img_name = Image_Name.split('.')[0]
        groundtruth_image_name = img_name + '_GT.png'

        Image_Ground_Truth = cv.imread(groundtruth_image_name, cv.IMREAD_UNCHANGED)

        cv.imshow('', Image_Ground_Truth)
        cv.waitKey()

        One_D_Ground_Truth = np.transpose(np.matrix(Image_Ground_Truth.ravel()))

        return One_D_Ground_Truth

    def Soft_Thresholding(self, labels):

        min_v = min(labels)
        max_v = max(labels)
        theta = ( labels - min_v ) / ( max_v - min_v )

        return theta

    def Threshold(self,input,target_shape):

        input = [x / 255.0 for x in input]
        za = (np.asarray(input) < 0.5).sum()

        percentage = (za / (target_shape[0] * target_shape[1])) * 100

        return percentage

    def Load_Segmentation_Model(self):
        model = joblib.load(MODEL_NAME)

        return model

    def Coverage_Predictor(self, target_feature, model):
        reg_start = time.time()
        Y_pred = model.predict(target_feature)
        reg_end = time.time()
        print('inference time {}'.format(reg_end-reg_start))
        
        return Y_pred
    
    def Get_Ground_Truth_Value(self, Image_Name):
        filename = image_name
        gt_file_name = filename.split('.')[0] + '_GT.png'

        gt_image = cv.imread(gt_file_name)
        gt_image = cv.cvtColor(gt_image, cv.COLOR_BGR2GRAY)
        gt_one_D_array = gt_image.ravel()

        image_shape = gt_image.shape
        pixel_cnt = image_shape[0] * image_shape[1]
        pixel_cloud = np.count_nonzero(gt_one_D_array)
        print('actual percentage {}%'.format((pixel_cloud / pixel_cnt) * 100))
        
    def run(self):
        start = time.time()

        model = self.Load_Segmentation_Model()

        target_feature, target_shape = self.Feature_Generator(TEMP_IMAGE_PATH)
        predict = self.Coverage_Predictor(target_feature, model)
        soft_thresholded = self.Soft_Thresholding(predict)
        estimation = self.Threshold(soft_thresholded, target_shape)

        end = time.time()

        #self.Get_Ground_Truth_Value(image_name)

        print('time {}'.format(end-start))
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hrf', action='store_true', help='Print in human readable form')
    args = parser.parse_args()
    plugin = CloudEstimator()
    
    try:
        plugin.run()
    except (KeyboardInterrupt, Exception) as ex:
        print(str(ex))
    finally:
        #plugin.close()
        pass
