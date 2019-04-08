import argparse
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import cv2
import os


parser = argparse.ArgumentParser()
parser.add_argument('--confidence', type=float, default=0.3)
parser.add_argument('--rotate', type=float, default=0.0)
parser.add_argument('results_dir')
parser.add_argument('images', nargs='*')
args = parser.parse_args()

results_dir = os.path.abspath(args.results_dir)
os.makedirs(results_dir, exist_ok=True)


def read_classes(path):
    classes = {}

    with open(path) as file:
        for line in file:
            fields = line.split()
            classes[int(fields[0])] = fields[1]

    return classes


model = cv2.dnn.readNetFromTensorflow('models/ssd_mobilenet_coco.pb', 'models/ssd_mobilenet_coco.pbtxt')
classes = read_classes('models/ssd_mobilenet_coco.classes')

for image_path in args.images:
    image = cv2.imread(os.path.abspath(image_path))
    image_cols = image.shape[1]
    image_rows = image.shape[0]

    # if rotation needed. should do this ahead of time in the image proc pipeline.
    M = cv2.getRotationMatrix2D((image_cols/2, image_rows/2), args.rotate, 1)
    image = cv2.warpAffine(image, M, (image_cols, image_rows))

    image_blob = cv2.dnn.blobFromImage(
        image,
        0.00784,
        (300, 300),
        (127.5, 127.5, 127.5),
        swapRB=True,
        crop=False,
    )

    model.setInput(image_blob)
    output = model.forward()

    results = {}

    for detection in output[0, 0, :, :]:
        score = float(detection[2])

        if score > args.confidence:
            class_index = int(detection[1])
            class_name = classes[class_index]
            if class_name not in results:
                results[class_name] = []

            left = int(detection[3] * image_cols)
            top = int(detection[4] * image_rows)
            right = int(detection[5] * image_cols)
            bottom = int(detection[6] * image_rows)

            results[class_name].append({
                'score': score,
                'location': (left, top, right, bottom),
            })

            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0))
            cv2.putText(image, '{} {}'.format(class_name, round(score, 3)), (left, bottom), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)

    results_path = os.path.join(results_dir, os.path.basename(image_path))
    cv2.imwrite(results_path, image)

    print({
        'image': image_path,
        'results': results,
    })
