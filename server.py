import pickle
import socket
import cv2
import numpy as np
import sys
from os import listdir
from os import getcwd
import time
import multiprocessing as mp
import copy
import concurrent.futures

def recv_all(conn, count):
    buf = b''
    while count:
        newbuf = conn.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def thread_Job(connected_socket, addr):
    #此函式內為每個thread各自要執行的部分
    sit=str(recv_all(connected_socket,8))
    print("receive sit")
    #print(sit)
    k = 0
    
    if "upload" in str(sit):
        fourcc=cv2.VideoWriter_fourcc(*"XVID")
        t=time.strftime('%X').split(":")
        name="output"+"".join(t)+".avi"
        out=cv2.VideoWriter(name,fourcc,24,(640,480))
        print(name)
        # demo.VideoCapture()

        while True:
            length = int(recv_all(connected_socket, 16))
            print("received length:", length)
            stringData = recv_all(connected_socket, length)
            print("received")
            data = np.frombuffer(stringData, dtype='uint8')
            decimg = cv2.imdecode(data, 1)
            if k < 10:
                k+=1
            else:
                k=0
            fin = open("liveframe"+str(k), "wb")
            flen = open("length"+str(k), "w")
            fin.truncate()
            flen.truncate()
            flen.write(str(length))
            fin.write(stringData)
            fin.close()
            flen.close()
            # live_frame = (length, copy.deepcopy(stringData))
            # print("live_frame added", live_frame[0])
            #cv2.imwrite("data%d.jpg" %i, decimg)
            out.write(decimg)
            cv2.waitKey(20)
        try:
            while True:
                length = int(recv_all(connected_socket, 16))
                print("received length:", length)
                stringData = recv_all(connected_socket, length)
                print("received")
                data = np.frombuffer(stringData, dtype='uint8')
                decimg = cv2.imdecode(data, 1)
                if k < 10:
                    k+=1
                else:
                    k=0
                fin =open("liveframe.txt"+str(k), "wb")
                fin.truncate()
                fin.write(bytes(str(length)+" "+stringData))
                fin.close()
                # live_frame = (length, copy.deepcopy(stringData))
                # print("live_frame added", live_frame[0])
                #cv2.imwrite("data%d.jpg" %i, decimg)
                out.write(decimg)
                cv2.waitKey(20)
                if 0xFF==ord("q"):
                    break
                else:
                    # cv2.imshow("data",decimg)
                    pass
                # time.sleep(0.03)
        except:
            print("live ended")
            connected_socket.close()
            # lock.acquire()
            fin =open("liveframe.txt", "w")
            fin.truncate()
            fin.write("0 0")
            fin.close()
            cv2.destroyAllWindows()
            # live_frame = 0
            # out.release()
    elif "old" in str(sit):
        #發送影片列表
        my_path=getcwd()
        files=listdir(my_path)
        for f in files:
            if f[-4:]=='.avi' or f[-4:]==".mp4":
                connected_socket.send((str(f)+'\n').encode("utf-8"))
        connected_socket.send(b'End\n')
        #接收使用者選擇
        video_name=recv_all(connected_socket,27).decode("utf-8")
        video_cap=cv2.VideoCapture(video_name)
        #發送影片長度
        length = video_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = video_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print("Checked 1")
        connected_socket.send((str(int(length))+" "+str(int(width))+" "+str(int(height))+'\n').encode("utf-8"))
        print("Checked 2")
        print(connected_socket.recv(20).decode('utf-8'), ", transmit session start")
        #開始播放
        while(video_cap.isOpened()):
            time.sleep(0.01)
            return_code,frame=video_cap.read()
            if not return_code:
                break
            #cv2.imshow("frame",frame)
            frame=cv2.GaussianBlur(frame,(5,5),0)
            imgencode = cv2.imencode('.jpg', frame,[int(cv2.IMWRITE_JPEG_QUALITY),90])[1]
            data = np.array(imgencode)
            stringData = data.tostring()
            connected_socket.send( str(len(stringData)).ljust(16).encode("utf-8"))
            sys.stdout.write("send length\n")
            connected_socket.send( stringData )
            sys.stdout.write("send       \n")
            response = connected_socket.recv(100).decode('utf-8')
            if "time change:" in response:
                print("\nresponse:", response)
                response = response.strip().strip().split("time change:")
                for i in response:
                    try:
                        int(i.strip())
                    except:
                        pass
                    else:
                        new_frame = i.strip()
                print("changing to:", new_frame)
                video_cap.set(cv2.CAP_PROP_POS_FRAMES, int(new_frame))
                continue
            elif response[0:9] == "continue":
                continue
        video_cap.release()
    elif "live" in str(sit):
        while True:
            # print("live frame:", live_frame)
            if k < 10:
                k+=1
            else:
                k=0
            fin = open("liveframe"+str(k), "rb")
            flen = open("length"+str(k), "r")
            length = int(flen.readline())
            stringData = (fin.read())
            fin.close()
            flen.close()
            print(length)
            if length == 0:
                connected_socket.send(str(0).ljust(16).encode("utf-8"))
                connected_socket.close()
                break
            else:
                print("live!")
                connected_socket.send(str(length).ljust(16).encode("utf-8"))
                print("send length")
                connected_socket.send(stringData)
                print("send")
                time.sleep(0.033)
    else:
        connected_socket.send("400 Bad Request".encode("utf-8"))
        connected_socket.close()

# def event_setter(set_time):
#     while True:
#         time.sleep(set_time)
#             i.set()

#以下是主thread負責的部分
if __name__ == "__main__":
    localIP=socket.gethostbyname_ex(socket.gethostname())[2][-1]    #取得現在IP
    HOST = localIP
    PORT = 8089
    print("local IP: %s, PORT = %s"%(localIP,PORT))
    live_frame = 0
    # lock = thr.Lock()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')

    s.bind((HOST, PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    #將接到的connection一一送入threads
    sockets = []
    threads = []
    # event_control = thr.Thread(target=event_setter(0.025))
    # i=0
    # while True:
    #     try:
    #         conn, addr = s.accept()
    #         print("connected from: ", addr)
    #         threads.append(mp.Process(target=thread_Job(conn, addr)))
    #         threads[-1].start()
    #         # i+=1
    #     except ConnectionResetError:
    #         print("ConnectionResetError. 遠端主機可能已強制關閉連線")
    #         print("local IP: %s, PORT = %s"%(localIP,PORT))
    #     except:
    #         print("發生未知的錯誤")
    #         print("local IP: %s, PORT = %s"%(localIP,PORT))
    # for i in range(len(threads)):
    #     threads[i].join()
    while True:
        conn, addr = s.accept()
        print("connected from: ", addr)
        threads.append(mp.Process(target=thread_Job(conn, addr)))
        threads[-1].start()
        # i+=1