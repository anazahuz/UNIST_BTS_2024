import time
import tkinter as tk
import threading
from queue import Queue
from utils.trackir_wrapper import TrackIRWrapper
from PIL import Image, ImageTk 

class DataCollector(threading.Thread):
    def __init__(self, trackir, data_queue, data_event):
        super().__init__()
        self.trackir = trackir
        self.data_queue = data_queue
        self.data_event = data_event
        self.running = True

    def run(self):
        while self.running:
            data = self.trackir.get_data()
            self.data_queue.put((time.time(), data))
            self.data_event.set() 
            time.sleep(1/120)

class App:
    def __init__(self):
        self.times = []
        self.start_time = time.time()
        self.pitch_data = []
        self.yaw_data = []

        self.root = tk.Tk()
        self.root.title("Recognition of Head Motion")

        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.img_cw = ImageTk.PhotoImage(Image.open('images/cw.png'))
        self.img_ccw = ImageTk.PhotoImage(Image.open('images/ccw.png'))
        self.img_go = ImageTk.PhotoImage(Image.open('images/go.png'))
        self.img_back = ImageTk.PhotoImage(Image.open('images/back.png'))

        self.yaw_image_label = tk.Label(self.image_frame)
        self.yaw_image_label.pack(side=tk.LEFT, padx=10, pady=10)

        self.pitch_image_label = tk.Label(self.image_frame)
        self.pitch_image_label.pack(side=tk.LEFT, padx=10, pady=10)

        self.yaw_in_range_time = None
        self.yaw_image_displayed = False
        self.yaw_current_range = None

        self.pitch_in_range_time = None
        self.pitch_image_displayed = False
        self.pitch_current_range = None

        self.yaw_left = (15, 25)
        self.yaw_right = (-30, -20)
        self.pitch_down = (5, 15)
        self.pitch_up = (-15, -10)

        self.data_queue = Queue()
        self.data_event = threading.Event()

        try:
            self.trackir = TrackIRWrapper(self.root.wm_frame())
        except Exception as e:
            print("Restart TrackIR", e)
            return

        self.data_collector = DataCollector(
            self.trackir, self.data_queue, self.data_event)
        self.data_collector.start()

        self.update()
        self.root.mainloop()

    def update(self):
        if self.data_event.is_set():
            while not self.data_queue.empty():
                timestamp, data = self.data_queue.get()

                current_time = timestamp - self.start_time
                self.times.append(current_time)
                self.pitch_data.append(data.pitch)
                self.yaw_data.append(data.yaw)

                current_yaw = self.yaw_data[-1]
                current_pitch = self.pitch_data[-1]

                if self.yaw_left[0] <= current_yaw <= self.yaw_left[1]:
                    if self.yaw_current_range != 'range1':
                        self.yaw_current_range = 'range1'
                        self.yaw_in_range_time = current_time
                        if self.yaw_image_displayed:
                            self.yaw_image_label.config(image='')
                            self.yaw_image_displayed = False
                    else:
                        if current_time - self.yaw_in_range_time >= 2.0:
                            if not self.yaw_image_displayed:
                                self.yaw_image_label.config(image=self.img_cw)
                                self.yaw_image_displayed = True
                elif self.yaw_right[0] <= current_yaw <= self.yaw_right[1]:
                    if self.yaw_current_range != 'range2':
                        self.yaw_current_range = 'range2'
                        self.yaw_in_range_time = current_time
                        if self.yaw_image_displayed:
                            self.yaw_image_label.config(image='')
                            self.yaw_image_displayed = False
                    else:
                        if current_time - self.yaw_in_range_time >= 2.0:
                            if not self.yaw_image_displayed:
                                self.yaw_image_label.config(image=self.img_ccw)
                                self.yaw_image_displayed = True
                else:
                    self.yaw_current_range = None
                    self.yaw_in_range_time = None
                    if self.yaw_image_displayed:
                        self.yaw_image_label.config(image='')
                        self.yaw_image_displayed = False

                if self.pitch_down[0] <= current_pitch <= self.pitch_down[1]:
                    if self.pitch_current_range != 'range1':
                        self.pitch_current_range = 'range1'
                        self.pitch_in_range_time = current_time
                        if self.pitch_image_displayed:
                            self.pitch_image_label.config(image='')
                            self.pitch_image_displayed = False
                    else:
                        if current_time - self.pitch_in_range_time >= 2.0:
                            if not self.pitch_image_displayed:
                                self.pitch_image_label.config(image=self.img_go)
                                self.pitch_image_displayed = True
                elif self.pitch_up[0] <= current_pitch <= self.pitch_up[1]:
                    if self.pitch_current_range != 'range2':
                        self.pitch_current_range = 'range2'
                        self.pitch_in_range_time = current_time
                        if self.pitch_image_displayed:
                            self.pitch_image_label.config(image='')
                            self.pitch_image_displayed = False
                    else:
                        if current_time - self.pitch_in_range_time >= 2.0:
                            if not self.pitch_image_displayed:
                                self.pitch_image_label.config(image=self.img_back)
                                self.pitch_image_displayed = True
                else:
                    self.pitch_current_range = None
                    self.pitch_in_range_time = None
                    if self.pitch_image_displayed:
                        self.pitch_image_label.config(image='')
                        self.pitch_image_displayed = False

            self.data_event.clear()

        self.root.after(int(1000/120), self.update)

    def __del__(self):
        self.data_collector.running = False
        self.data_collector.join()