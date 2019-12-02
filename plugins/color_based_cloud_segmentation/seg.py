import argparse
import cv2
import numpy as np

import pickle

import glob

def _feature_generator(image, resizing):
    image = cv2.resize(image, (resizing, resizing))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    r = image[:,:,2].astype('int16')
    b = image[:,:,0].astype('int16')
    g = image[:,:,1].astype('int16')

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    s = hsv[:,:,1].astype('int16')

    rob = r/b
    rsb = r-b
    rbratio = (b-r)/(b+r)

    stand_rob = (rob-np.mean(rob))/np.std(rob)
    stand_rob = (stand_rob-np.mean(stand_rob))

    stand_rsb = (rsb-np.mean(rsb))/np.std(rsb)
    stand_rsb = (stand_rsb-np.mean(stand_rsb))

    stand_rbratio = (rbratio-np.mean(rbratio))/np.std(rbratio)
    stand_rbratio = (stand_rbratio-np.mean(stand_rbratio))

    stand_s = (s-np.mean(s))/np.std(s)
    stand_s = (stand_s-np.mean(stand_s))

    mix = np.hstack((np.transpose(np.matrix(stand_s.flatten())), np.transpose(np.matrix(stand_rob.flatten())), np.transpose(np.matrix(stand_rbratio.flatten()))))

    return mix


def _process(path, model, threshold, resizing, gt_percentage=0):
    image = cv2.imread(path)
    test_feature = _feature_generator(image, resizing)

    pls_loaded = pickle.load(open(model, 'rb'))
    Y_pred = pls_loaded.predict(test_feature)
    # print("Y_pred : {}".format(Y_pred))

    _threshold(Y_pred, gt_percentage, threshold)
    print('>>>>>> min :', np.min(Y_pred), 'max : ', np.max(Y_pred), '\n')


def find_match(key, gt_image_list):
    for file in gt_image_list:
        if key in file:
            return file


def _threshold(result, gt_percentage, thr):
    cloud = (np.asarray(result) > thr).sum()
    percentage = (cloud / (result.shape[0] * result.shape[1]) ) * 100

    # print('>>>>>> segmentation result: ', percentage, '\n')
    print('>>>>>> segmentation result: ', percentage)
    if gt_percentage != None:
        print('>>>>>> absolute diff: ', np.abs(gt_percentage - percentage))


def _ground_truth(path, resizing):
    image = cv2.imread(path, 0).astype('int16')
    image = cv2.resize(image, (resizing, resizing))

    value = [0, 0, 0]
    for i in range(len(image)):
        for j in range(len(image[0])):
            if image[i][j] == 0:
                value[0] += 1
                image[i][j] = np.random.randint(1, 15, 1)
            elif image[i][j] == 255:
                value[1] +=1
            else:
                value[2] += 1

    if value[0] == (image.shape[0]*image.shape[1]):
        # print('>>>>>> all clear sky')
        image = np.random.randint(0, 15, (image.shape[0], image.shape[1]))
    elif value[1] == (image.shape[0]*image.shape[1]):
        # print('>>>>>> overcasted sky')
        image = np.random.randint(240, 255, (image.shape[0], image.shape[1]))
    else:
        pass
        # print('>>>>>> partial cloudy sky')

    cloud = 0
    for i in range(len(image)):
        for j in range(len(image[0])):
            if image[i][j] > 127:    ## 255/2 = 127.5
                cloud += 1

    print('>>>>>> ground truth: ', (cloud/(image.shape[0]*image.shape[1]))*100)

    column_image = (np.transpose(np.matrix(image.flatten()))-np.mean(image))/np.std(image)
    column_image = column_image - np.mean(column_image)
    return_image = np.concatenate((column_image, column_image, column_image), axis=1)

    return return_image, (cloud/(image.shape[0]*image.shape[1]))*100



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some input arguments')
    parser.add_argument('--model', type=str, help='path to the model')
    parser.add_argument('--timage', type=str, help='path to the test image file, along with gtimage (optional)')
    parser.add_argument('--gtimage', type=str, help='path to the ground truth image file, along with timage')
    parser.add_argument('--gt', type=str, help='path to the ground truth image file, along with test')
    parser.add_argument('--test', type=str, help='path to the folder for test images, along with gt (optional)')
    parser.add_argument('--resize', type=int, help='resizing shape')
    parser.add_argument('--threshold', type=float, help='threshold level', default=0.4)

    args = parser.parse_args()

    if args.model == None:
        print('path for input model is necessary')
        parser.print_help()
        exit(1)
    elif args.threshold == None:
        print('>>>>>> default threshold is 0.4')
    elif args.test == None and args.timage == None:
        print('path for input image(s) is necessary')
        parser.print_help()
        exit(1)


    image_list = []
    gt_list = []
    if args.test != None:
        test_images = ''
        gt_path = ''
        if 'swim' in args.test:
            test_images = args.test + '/*.png'
        else:
            test_images = args.test + '/*.jpg'

        if args.gt != None:
            if 'swim' in args.test:
                gt_path = args.gt + '/*_GT.png'
            else:
                gt_path = args.gt + '/*_GT.jpg'


        image_list = glob.glob(test_images)
        gt_list = glob.glob(gt_path)

    elif args.timage != None:
        image_list.append(args.timage)
        if args.gtimage != None:
            gt_list.append(args.gtimage)


    for path in image_list:
        # try:
        if len(gt_list) is not 0:
            key = path.strip().split('/')[-1].split('.')[0]
            if '_' in key:
                key = key.split('_')[-1]
            print('>>>>>> image: ', key)

            gt_path = find_match(key, gt_list)
            print(key, gt_path)
            label, gt_percentage = _ground_truth(gt_path, args.resize)

        else:
            gt_image = None
            gt_percentage = None

        result = _process(path, args.model, args.threshold, args.resize, gt_percentage)
        # print('>>>> cloud coverage: ', result, ' in percentage')

        # except Exception as e:
        #     print(str(e))
        #     pass




