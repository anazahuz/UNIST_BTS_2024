# app/app.py

import time
import tkinter as tk
import csv
import datetime
import os
import threading
from queue import Queue

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.trackir_wrapper import TrackIRWrapper

class DataCollector(threading.Thread):
    def __init__(self, trackir, data_queue, data_event):
        super().__init__()
        self.trackir = trackir
        self.data_queue = data_queue
        self.data_event = data_event
        self.recording = False
        self.csvwriter = None
        self.csvfile = None  # 파일 객체 저장
        self.running = True

    def run(self):
        while self.running:
            data = self.trackir.get_data()
            self.data_queue.put((time.time(), data))
            self.data_event.set()  # 새로운 데이터가 있음을 알림

            if self.recording and self.csvwriter and self.csvfile:
                self.csvwriter.writerow(
                    [data.frame, data.roll, data.pitch, data.yaw, data.x, data.y, data.z])

                # 파일 버퍼를 즉시 기록
                self.csvfile.flush()

            time.sleep(1/120)  # 120Hz로 데이터 수집

class App:
    def __init__(self):
        # Initialize variables
        self.recording = False
        self.csvwriter = None
        self.csvfile = None

        # Data storage
        self.times = []
        self.start_time = time.time()
        self.roll_data = []
        self.pitch_data = []
        self.yaw_data = []
        self.x_data = []
        self.y_data = []
        self.z_data = []

        self.max_time = 10  # seconds
        self.data_points = 1200  # 120 Hz * 10 seconds

        # Data save folder
        self.save_folder = 'data/rawdata'
        os.makedirs(self.save_folder, exist_ok=True)

        # Create tkinter app
        self.root = tk.Tk()
        self.root.title("Real-time Data Plot")

        # Add a frame for buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        # Create 'Start Recording' button
        self.start_button = tk.Button(
            self.button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Create 'Stop Recording' button
        self.stop_button = tk.Button(
            self.button_frame, text="Stop Recording", command=self.stop_recording)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_button.config(state=tk.DISABLED)

        # Initialize plotting
        self.fig, self.axes = plt.subplots(6, 1, figsize=(8, 12))
        plt.subplots_adjust(hspace=0.5)

        # Create canvas and pack it
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Initialize plots
        self.initialize_plots()

        # Create data queue and event
        self.data_queue = Queue()
        self.data_event = threading.Event()

        # Create TrackIR instance
        try:
            self.trackir = TrackIRWrapper(self.root.wm_frame())
        except Exception as e:
            print("Restart TrackIR", e)
            return

        # Start data collector thread
        self.data_collector = DataCollector(
            self.trackir, self.data_queue, self.data_event)
        self.data_collector.start()

        # Start the update loop
        self.update_plot()

        # Start the tkinter main loop
        self.root.mainloop()

    def initialize_plots(self):
        # Initialize plots similar to your original code
        labels = ['Roll', 'Pitch', 'Yaw', 'X', 'Y', 'Z']
        data_limits = [(-100, 100), (-100, 100), (-100, 100),
                       (-200, 200), (-200, 200), (-200, 200)]
        self.lines = []

        for i, ax in enumerate(self.axes):
            line, = ax.plot([], [], label=labels[i])
            ax.set_ylabel(labels[i])
            ax.set_xlim(0, self.max_time)
            ax.set_ylim(data_limits[i])
            ax.grid(True)
            self.lines.append(line)
        self.axes[-1].set_xlabel('Time (s)')

    def start_recording(self, event=None):
        if not self.recording:
            # Create file
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'raw_data_{timestamp}.csv'
            filepath = os.path.join(self.save_folder, filename)
            self.csvfile = open(filepath, 'w', newline='')

            # Write header
            self.csvwriter = csv.writer(self.csvfile)
            self.csvwriter.writerow(
                ['Frame', 'Roll', 'Pitch', 'Yaw', 'X', 'Y', 'Z'])

            # Pass csvwriter and csvfile to data collector
            self.data_collector.csvwriter = self.csvwriter
            self.data_collector.csvfile = self.csvfile  # csvfile 전달
            self.data_collector.recording = True

            self.recording = True
            print('Start Recording...')

            # Update button states
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            print('Already Recording...')

    def stop_recording(self, event=None):
        if self.recording:
            self.recording = False
            self.data_collector.recording = False
            self.csvfile.close()
            self.csvwriter = None
            self.csvfile = None
            self.data_collector.csvwriter = None
            self.data_collector.csvfile = None  # csvfile 초기화
            print('Stop Recording')

            # Update button states
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
        else:
            print('Not Recording Now')

    def update_plot(self):
        # Wait for new data
        if self.data_event.is_set():
            # Get data from queue
            while not self.data_queue.empty():
                timestamp, data = self.data_queue.get()

                # Append data
                current_time = timestamp - self.start_time
                self.times.append(current_time)
                self.roll_data.append(data.roll)
                self.pitch_data.append(data.pitch)
                self.yaw_data.append(data.yaw)
                self.x_data.append(data.x)
                self.y_data.append(data.y)
                self.z_data.append(data.z)

                # Keep only the last data_points
                if len(self.times) > self.data_points:
                    self.times = self.times[-self.data_points:]
                    self.roll_data = self.roll_data[-self.data_points:]
                    self.pitch_data = self.pitch_data[-self.data_points:]
                    self.yaw_data = self.yaw_data[-self.data_points:]
                    self.x_data = self.x_data[-self.data_points:]
                    self.y_data = self.y_data[-self.data_points:]
                    self.z_data = self.z_data[-self.data_points:]

            # Update plots
            data_list = [self.roll_data, self.pitch_data, self.yaw_data,
                         self.x_data, self.y_data, self.z_data]
            for i, line in enumerate(self.lines):
                line.set_data(self.times, data_list[i])

            # Adjust xlim
            xmin = max(0, self.times[-1] - self.max_time)
            xmax = self.times[-1]
            for ax in self.axes:
                ax.set_xlim(xmin, xmax)

            # Redraw canvas
            self.canvas.draw()

            # Clear event
            self.data_event.clear()

        # Schedule the next update
        self.root.after(int(1000/120), self.update_plot)  # 그래프는 60Hz로 업데이트

    def __del__(self):
        # Stop data collector thread
        self.data_collector.running = False
        self.data_collector.join()
