import argparse
import cv2
import numpy as np

import joblib

def _feature_generator(image):
    image = cv2.resize(image, (600, 600))

    r = image[:,:,2].astype('float64')
    b = image[:,:,0].astype('float64')
    g = image[:,:,1].astype('float64')

    # hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # s = hsv[:,:,1].astype('float64')

    rob = r/b
    # rsb = r-b
    # rbratio = (b-r)/(b+r)

    stand_rob = (rob-np.mean(rob))/np.std(rob)
    stand_rob = (stand_rob-np.mean(stand_rob))

    # stand_rsb = (rsb-np.mean(rsb))/np.std(rsb)
    # stand_rsb = (stand_rsb-np.mean(stand_rsb))

    # stand_rbratio = (rbratio-np.mean(rbratio))/np.std(rbratio)
    # stand_rbratio = (stand_rbratio-np.mean(stand_rbratio))

    # stand_s = (s-np.mean(s))/np.std(s)
    # stand_s = (stand_s-np.mean(s))

    # final_feature = np.hstack((stand_rob, stand_rsb, stand_rbratio))

    final_feature = stand_rob

    return final_feature


def _coverage_predictor(feature, model, threshold):
    y_pred = model.predict(feature)

    ### soft thresholding
    min_y = y_pred.min()
    max_y = y_pred.max()
    pred = ( y_pred - min_y ) / ( max_y - min_y )

    ## threshold
    za = 0
    for row in pred:
        for i in row:
            if i > threshold:
                za += 1

    percentage = (za / (pred.shape[0] * pred.shape[1])) * 100

    return percentage

def _process(path, model, threshold):
    image = cv2.imread(path)

    feature = _feature_generator(image)
    prediction = _coverage_predictor(feature, model, threshold)

    return prediction


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some input arguments')
    parser.add_argument('--timage', type=str, help='path to the test image file')
    parser.add_argument('--model', type=str, help='path to the model')
    parser.add_argument('--threshold', type=float, help='threshold level in range of [0, 1]', default=0.4)

    args = parser.parse_args()

    if args.model == None:
        print('path for input model is necessary')
        parser.print_help()
        exit(0)
    elif args.threshold == None:
        print('default threshold is 0.39')
    elif args.timage == None:
        print('path for input image(s) is necessary')
        parser.print_help()
        exit(0)

    model = joblib.load(args.model)

    # try:
    result = _process(args.timage, model, args.threshold)
    print('cloud coverage: ', result, ' in percentage')

    # except Exception as e:
    #     print(str(e))
    #     pass

