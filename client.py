import socket
import pickle
import cv2
import numpy as np
import sys
import tkinter as tk
import PIL.Image, PIL.ImageTk

clientsocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
clientsocket.connect(("192.168.0.21",8089))
print('connected to server..')

class basic_videoplayer():
	def __init__(self, window, window_title, video_length, inputframe, changetime, width=640, height=360):
		self.window = window
		self.window.title(window_title)
		self.width = width
		self.height = height
		self.video_length = video_length
		self.video_canvas = tk.Canvas(self.window, width=self.width, height=self.height)
		self.video_canvas.pack()
		self.inputframe = inputframe
		self.changetime = changetime

		self.panel_frame = tk.Frame(self.window)
		self.panel_frame.pack(anchor = tk.NW)

		self.btn_pause_txt = tk.StringVar()
		self.btn_pause_txt.set("pause")
		self.btn_pause = tk.Button(self.panel_frame, textvariable=self.btn_pause_txt, width=6, command = self.pause_action)
		self.btn_pause.pack(side = 'left')

		self.time = tk.IntVar()
		self.time.set(0)
		self.timeline = tk.Scale(self.panel_frame, from_ = 0, to = self.video_length, orient = tk.HORIZONTAL, length = (self.width-50), showvalue = 0, command = self.get_scale_time, variable = self.time)
		self.timeline.pack(side = 'left')
		self.pause_stat = False
		self.updateframe()
		self.window.mainloop()

	def updateframe(self):
		if self.time.get() == self.video_length:
			if self.pause_stat == False:
				self.pause_action()
			# 播到底就停止
		elif self.pause_stat == False:
			#print("request a new frame.")
			self.frame = self.inputframe()
			#print("get frame!")
			self.time.set(self.time.get() + 1)
			self.video_canvas.create_image(0, 0, image = self.frame, anchor = tk.NW)
			#print("video refreshed!")
		self.window.after(33, self.updateframe)

	def pause_action(self):
		if self.pause_stat == False:
			self.pause_stat = True
			self.btn_pause_txt.set("play")
		else:
			self.pause_stat = False
			self.btn_pause_txt.set("pause")

	def get_scale_time(self, v):
		self.changetime(int(v))

def inputframe():
	length = int(recvall(clientsocket, 16))
	print("received length")
	stringData = recvall(clientsocket, length)
	print("received")
	data = np.frombuffer(stringData, dtype='uint8')
	decimg = cv2.imdecode(data, 1)
	decimg = cv2.cvtColor(decimg, cv2.COLOR_BGR2RGB)
	clientsocket.send("continue ".encode("utf-8"))
	#print("continue")
	return PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(decimg))

def changetime(new_time):
	clientsocket.send(("time change: "+str(new_time)+" ").encode("utf-8"))
	print("time change: "+str(new_time))
	# clientsocket.recv(30)

sit1="live"
sit2="old"
sit3="upload"

def recvall(conn, count):
	buf = b''
	while count:
		newbuf = conn.recv(count)
		if not newbuf: return None
		buf += newbuf
		count -= len(newbuf)
	return buf

x = 0
while x == 0:
	x = input("按下 1 開始觀看直播\n按下 2 選擇觀看影片\n按下 3 向其他人直播！\n")
	if x=="1":
		print("live start")
		clientsocket.send(sit1.ljust(8).encode("utf-8"))
		print("send sit") 
		while True:
			length = int(recvall(clientsocket, 16))
			print("received length")
			if length == 0:
				print("The live has ended.")
				break
			stringData = recvall(clientsocket, length)
			print("received")
			data = np.frombuffer(stringData, dtype='uint8')
			decimg = cv2.imdecode(data, 1)
			#cv2.imwrite("data%d.jpg" %i, decimg)
			# i+=1
			cv2.imshow("data",decimg)
			if cv2.waitKey(30) & 0xFF == ord("q"):
				break
		clientsocket.close()

	elif x=="2":
		clientsocket.send(sit2.ljust(8).encode("utf-8"))
		print("send sit")
		print("===========================")
		#顯示server端的目錄(影片選項)
		going=True
		while going:
			temp=clientsocket.recv(1000).decode('utf-8')
			menu=temp.split('\n')
			for line in menu:
				if line=='End':
					going=False
					break
				else:
					print(line)
		print("===========================")
		#使用者選擇影片
		video_name=input("choose one\n")
		clientsocket.send(video_name.ljust(27).encode("utf-8"))
		#詢問影片長度
		video_info = clientsocket.recv(100).decode('utf-8').strip().split()
		total_frames, width, height = int(video_info[0]), int(video_info[1]), int(video_info[2])
		#開始播放
		clientsocket.send("client ready".encode("utf-8"))
		print("video start")
		video = basic_videoplayer(tk.Tk(), video_name, total_frames, inputframe, changetime, width=width, height=height)
		clientsocket.close

	elif x == "3":
		cap=cv2.VideoCapture(0)
		print("start")
		clientsocket.send(sit3.ljust(8).encode("utf-8"))
		print("send sit")
		print("camera start")

		while(cap.isOpened()):
			return_bool,frame=cap.read()
			if not return_bool:break
			frame=cv2.flip(frame,1)  #flip horizontally

			cv2.imshow("your camera",frame)
			#直播主可以看到自己的臉
			
			#print(frame)
			#print(frame.shape) #(480,640,3)=>frame size

			frame=cv2.GaussianBlur(frame,(3,3),0)
			imgencode = cv2.imencode('.jpg', frame,[int(cv2.IMWRITE_JPEG_QUALITY),90])[1]
			data = np.array(imgencode)
			stringData = data.tostring()
			clientsocket.send( str(len(stringData)).ljust(16).encode("utf-8"))
			print("send length")
			clientsocket.send( stringData )
			print("send")
			#cv2.imwrite("frame%d.jpg" % i, frame)

			if cv2.waitKey(33) & 0xFF==ord("q"): break
		cap.release()
		cv2.destroyAllWindows()
		clientsocket.close()
	
	else:
		print("錯誤輸入喔！請重新輸入，並注意輸入半形阿拉伯數字 1 、 2 或 3 ！")
		x = 0
