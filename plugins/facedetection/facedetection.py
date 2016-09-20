import waggle.pipeline
import sys, time

try:
	import cv2
except ImportError:
	raise

class FaceDetectionPlugin(waggle.pipeline.Plugin):

	plugin_name = 'face_detection'
	plugin_version = '1'

	def run(self):
		if len(sys.argv) == 2:
			cascPath = sys.argv[1]
		else:
			cascPath = 'plugins/facedetection/haarcascade_frontalface_default.xml'
		
		faceCascade = cv2.CascadeClassifier(cascPath)

		debugging = False
		#if debugging:
		#	self.man[self.name] = 1

		t = 0
		period = 10 # sec

		# index 0 for the first camera (normally internal)
		# index 1 for the second camera (normally external)
		video_capture = cv2.VideoCapture(0)

		#while self.man[self.name] == 1:
		while True:
			num_of_faces = avg_faces = 0
			max_faces = 0
			min_faces = 10000
			# start timer
			t = time.time()

			while True:
				# Capture frame-by-frame
				ret, frame = video_capture.read()

				gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

				faces = faceCascade.detectMultiScale(
				gray,
				scaleFactor=1.1,
				minNeighbors=5,
				minSize=(30, 30),
				#flags=cv2.cv.CV_HAAR_SCALE_IMAGE # python
				flags=0 # python3
				)
				if debugging:
					# Draw a rectangle around the faces
					for (x, y, w, h) in faces:
						cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

					# Display the resulting frame
					cv2.imshow('Video', frame)

					if cv2.waitKey(1) & 0xFF == ord('q'):
						break

				elasped = time.time() - t
				num_of_faces = len(faces)
				if num_of_faces >= max_faces:
					max_faces = num_of_faces
				if num_of_faces <= min_faces:
					min_faces = num_of_faces

				if debugging:
					print("number of faces %d" % (num_of_faces))
				if elasped > period:
					break

			# calculate agv
			if max_faces >= min_faces:
				avg_faces = (max_faces + min_faces) / 2.0
				data = []
				data.append('min:%d' % (min_faces))
				data.append('max:%d' % (max_faces))
				data.append('avg:%.2f' % (avg_faces))
				if debugging:
					print(data)

				self.send(sensor='camera', data=data)
			else:
				self.send(sensor='camera', data=['nodata:error'])


		# When everything is done, release the capture
		video_capture.release()
		cv2.destroyAllWindows()

class register(object):

	def __init__(self, name, man, mailbox_outgoing):
		FaceDetectionPlugin(name, man, mailbox_outgoing).run()


if __name__ == "__main__":
	def callback(data):
		print(data)

	waggle.pipeline.run_standalone(FaceDetectionPlugin, callback)
