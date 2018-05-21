import cv2

def capture_frame():
    # Use device on /dev/video1
    cam = cv2.VideoCapture(1)
    cv2.namedWindow("test")

    img_counter = 0

    while True:
        ret, frame = cam.read()
        if not ret:
            print('No camera on /dev/video1')
            exit(0)

        cv2.imshow("test", frame)

        k = cv2.waitKey(1)

        if k%256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break

        elif k%256 == 32:
            # Space bar pressed
            img_name = "opencv_frame_{}.png".format(img_counter)
            cv2.imwrite(img_name, frame)
            print("{} written!".format(img_name))
            img_counter += 1
            break

    cam.release()
    cv2.destroyAllWindows()



