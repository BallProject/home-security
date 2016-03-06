from multiprocessing import Process
from pushbullet import Pushbullet
import datetime, cv2, numpy, scapy.all as scapy
from time import sleep 
MOTION_RECORD_TIME = datetime.timedelta(seconds = 10)
DEVICE_MAC = "" # e.g. "3d:f9:c2:d8:0f:d5"
SUBNET = "" # e.g. "192.168.1.0/24"
PUSHBULLET_API_KEY = "" # e.g. "o.Wdc5J0toGUwnKS8hjt2jj9DfPlOxZipC"
PUSHBULLET_DEVICE_NAME = "" # e.g. "Galaxy S4"

###### HEARTBEAT ###### for questions please contact me on "sadeguyproject@gmail.com"
PUSHBULLET_API_KEY_HB = "" # Heartbeat's API Key
PUSHBULLET_DEVICE_NAME_HB = "" # Heartbeat's Device Name
HBPATH = "" #Heartbeat's PATH. can be made either manualy or once main is called
scapy.conf.verb = 0

def have_motion(frame1, frame2):
	if frame1 is None or frame2 is None:
		return False
	delta = cv2.absdiff(frame1, frame2)
	thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
	return numpy.sum(thresh) > 0

def is_device_connected(mac_addr):
	answer, _ = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=SUBNET), timeout=2)
	return mac_addr in (rcv.src for _, rcv in answer)

def push_file(filename, isHB): # Added a isHB boolean paramter in order to use this function for sending heartbeats aswell
        push_api_key = ""
        push_device_name = ""
        if (not isHB): # the following code only matters if isHB is False
                push_api_key = PUSHBULLET_API_KEY #
                push_device_name = PUSHBULLET_DEVICE_NAME # local vars for dynamics reasons 
                if is_device_connected(DEVICE_MAC):
                	print "Device is connected, not sending"
                	return
                print "Sending Video File ", filename
	else:
                push_api_key = PUSHBULLET_API_KEY_HB
                push_device_name = PUSHBULLET_DEVICE_NAME_HB # ^^
                print "Sending Heartbeat ", filename
        
	pushbullet = Pushbullet(push_api_key) 
	my_device = pushbullet.get_device(push_device_name)
	file_data = pushbullet.upload_file(open(filename, "rb"), filename)
	pushbullet.push_file(device = my_device, **file_data)
	print "Sent!"

def main():
	cap = cv2.VideoCapture(0)
	frame_size = (int(cap.get(3)), int(cap.get(4)))
	fourcc = cv2.cv.CV_FOURCC(*"XVID")

	prev_frame = None
	last_motion = None
	motion_filename = None
	motion_file = None

	while cap.isOpened():
		now = datetime.datetime.now()
		success, frame = cap.read()
		assert success, "failed reading frame"
                
		frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		frame_gray = cv2.GaussianBlur(frame_gray, (21, 21), 0)

		if have_motion(prev_frame, frame_gray):
			if motion_file is None:
				motion_filename = now.strftime("%Y_%m_%d_%H_%M_%S_MOTION.avi")
				motion_file = cv2.VideoWriter(motion_filename, fourcc, 20.0, frame_size)
			last_motion = now
			print "Motion!", last_motion

		if motion_file is not None:
			motion_file.write(frame)
			if now - last_motion > MOTION_RECORD_TIME:
				motion_file.release()
				motion_file = None
				Process(target = push_file, args = (motion_filename, False )).start()

		prev_frame = frame_gray
		cv2.imshow('frame', frame)
                Process(target = push_file, args = (HBPATH, True )).start() # Hearbeat
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	cap.release()
	cv2.destroyAllWindows()

if __name__ == "__main__":
	main()
