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
        self.start_time = time.time()
        self.pitch_data = []
        self.yaw_data = []
        
        # 범위 지정
        self.yaw_left = (15, 25)
        self.yaw_right = (-30, -20)
        self.pitch_down = (5, 15)
        self.pitch_up = (-15, -5)

        # 게이지 관련 변수
        self.yaw_gauge_time = 0.0
        self.pitch_gauge_time = 0.0
        self.max_gauge_time = 4.0  # 최대 4초

        # 현재 범위 상태
        self.yaw_current_range = None
        self.yaw_in_range_start = None
        self.pitch_current_range = None
        self.pitch_in_range_start = None

        # 이미지 표시 정보(별도 창)
        self.image_popup = None

        # 동작명 매핑
        self.action_text_map = {
            'yaw_left': "CW Rotate",
            'yaw_right': "CCW Rotate",
            'pitch_down': "Forward",
            'pitch_up': "Backward"
        }

        # 이미지 불러오기
        self.img_cw = Image.open('images/cw.png')
        self.img_ccw = Image.open('images/ccw.png')
        self.img_go = Image.open('images/go.png')
        self.img_back = Image.open('images/back.png')

        # HUD용 Tk 윈도우 초기화
        self.root = tk.Tk()
        self.root.title("Head Motion HUD")
        self.root.overrideredirect(True)  # 테두리 제거
        self.root.attributes("-topmost", True)  # 항상 위
        self.root.configure(bg='magenta')
        self.root.attributes("-transparentcolor", "magenta")  
        self.root.geometry("400x300+10+10")

        # HUD용 Canvas
        self.canvas = tk.Canvas(self.root, width=400, height=300, bg='white', highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # TrackIR setup
        self.data_queue = Queue()
        self.data_event = threading.Event()

        try:
            self.trackir = TrackIRWrapper(self.root.wm_frame())
        except Exception as e:
            print("Restart TrackIR", e)
            return

        self.data_collector = DataCollector(self.trackir, self.data_queue, self.data_event)
        self.data_collector.start()

        self.update()
        self.root.mainloop()

    def draw_ui(self, current_pitch, current_yaw, current_time):
        self.canvas.delete("all")

        yaw_min, yaw_max = -45, 45
        pitch_min, pitch_max = -30, 30

        w = 400
        h = 300

        # 레이아웃 정의: 넘버라인 → 게이지 → 넘버라인 → 게이지
        yaw_line_y = 60
        yaw_gauge_y = 100
        pitch_line_y = 160
        pitch_gauge_y = 200

        # 게이지 길이/위치
        gauge_max_width = 200
        gauge_height = 15
        gauge_x_start = 150
        gauge_x_end = gauge_x_start + gauge_max_width

        def map_yaw(val):
            return 20 + (val - yaw_min)/(yaw_max - yaw_min)*(w-40)

        def map_pitch(val):
            return 20 + (val - pitch_min)/(pitch_max - pitch_min)*(w-40)

        # Yaw number line
        self.canvas.create_line(20, yaw_line_y, w-20, yaw_line_y, fill='black')
        self.canvas.create_line(map_yaw(self.yaw_left[0]), yaw_line_y, map_yaw(self.yaw_left[1]), yaw_line_y, width=5, fill='green')
        self.canvas.create_line(map_yaw(self.yaw_right[0]), yaw_line_y, map_yaw(self.yaw_right[1]), yaw_line_y, width=5, fill='blue')

        current_yaw_x = map_yaw(self.yaw_data[-1])
        self.canvas.create_oval(current_yaw_x-5, yaw_line_y-5, current_yaw_x+5, yaw_line_y+5, fill='red')
        # Yaw 값 표시
        self.canvas.create_text(current_yaw_x, yaw_line_y - 15, text=f"{self.yaw_data[-1]:.2f}", fill='black', font=("Arial", 10))

        # Yaw 게이지
        yaw_gauge_ratio = min(self.yaw_gauge_time / self.max_gauge_time, 1.0)
        self.canvas.create_rectangle(gauge_x_start, yaw_gauge_y, gauge_x_end, yaw_gauge_y+gauge_height, outline='black')
        self.canvas.create_rectangle(gauge_x_start, yaw_gauge_y, gauge_x_start+gauge_max_width*yaw_gauge_ratio, yaw_gauge_y+gauge_height, fill='green')
        if self.yaw_current_range is not None and self.yaw_gauge_time > 0:
            action_text = self.action_text_map.get(self.yaw_current_range, "")
            self.canvas.create_text(gauge_x_start - 10, yaw_gauge_y + gauge_height/2, text=action_text, fill='black', font=("Arial", 10), anchor='e')

        # Pitch number line
        self.canvas.create_line(20, pitch_line_y, w-20, pitch_line_y, fill='black')
        self.canvas.create_line(map_pitch(self.pitch_down[0]), pitch_line_y, map_pitch(self.pitch_down[1]), pitch_line_y, width=5, fill='orange')
        self.canvas.create_line(map_pitch(self.pitch_up[0]), pitch_line_y, map_pitch(self.pitch_up[1]), pitch_line_y, width=5, fill='purple')

        current_pitch_x = map_pitch(self.pitch_data[-1])
        self.canvas.create_oval(current_pitch_x-5, pitch_line_y-5, current_pitch_x+5, pitch_line_y+5, fill='red')
        self.canvas.create_text(current_pitch_x, pitch_line_y + 15, text=f"{self.pitch_data[-1]:.2f}", fill='black', font=("Arial", 10))

        # Pitch 게이지
        pitch_gauge_ratio = min(self.pitch_gauge_time / self.max_gauge_time, 1.0)
        self.canvas.create_rectangle(gauge_x_start, pitch_gauge_y, gauge_x_end, pitch_gauge_y+gauge_height, outline='black')
        self.canvas.create_rectangle(gauge_x_start, pitch_gauge_y, gauge_x_start+gauge_max_width*pitch_gauge_ratio, pitch_gauge_y+gauge_height, fill='green')
        if self.pitch_current_range is not None and self.pitch_gauge_time > 0:
            action_text = self.action_text_map.get(self.pitch_current_range, "")
            self.canvas.create_text(gauge_x_start - 10, pitch_gauge_y + gauge_height/2, text=action_text, fill='black', font=("Arial", 10), anchor='e')

    def handle_range_logic(self, current_val, current_time, range_def, current_range_state, in_range_start_time):
        if range_def[0] <= current_val <= range_def[1]:
            if current_range_state is None:
                return ('in', current_time)
            else:
                return ('in', in_range_start_time)
        else:
            return (None, None)

    def update_gauge_and_image(self, current_time, in_range_start, current_range, gauge_time):
        if current_range is not None and in_range_start is not None:
            duration_in_range = current_time - in_range_start
            if duration_in_range >= 1.0:
                new_gauge_time = gauge_time + (1/120)
                if new_gauge_time > self.max_gauge_time:
                    new_gauge_time = self.max_gauge_time
                return new_gauge_time
            else:
                return gauge_time
        else:
            return gauge_time

    def prepare_image(self, gauge_time, base_img):
        ratio = gauge_time / self.max_gauge_time
        if ratio <= 0:
            return None
        w, h = base_img.size
        new_w = int(w * (0.3 + 0.7*ratio))
        new_h = int(h * (0.3 + 0.7*ratio))
        resized_img = base_img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized_img)
        return tk_img

    def show_popup_images(self, images):
        # images: list of tk images (PhotoImage)
        if len(images) == 0:
            return

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        total_width = sum(img.width() for img in images) + (len(images)-1)*20
        max_height = max(img.height() for img in images)
        
        x_pos = (screen_w - total_width)//2
        y_pos = (screen_h - max_height)//2

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.geometry(f"{total_width}x{max_height}+{x_pos}+{y_pos}")

        popup_canvas = tk.Canvas(popup, width=total_width, height=max_height, bg='white', highlightthickness=0)
        popup_canvas.pack(fill="both", expand=True)

        cur_x = 0
        for img in images:
            popup_canvas.create_image(cur_x + img.width()//2, max_height//2, image=img, anchor='center')
            cur_x += img.width() + 20

        # 이미지가 GC되지 않도록 popup에 참조 저장
        popup.images = images

        # 1초 뒤에 창 닫기
        popup.after(1000, popup.destroy)


    def update(self):
        if self.data_event.is_set():
            images_to_popup = []  # 이번 cycle에 범위 이탈로 표시할 이미지들
            while not self.data_queue.empty():
                timestamp, data = self.data_queue.get()
                current_time = timestamp - self.start_time
                current_yaw = data.yaw
                current_pitch = data.pitch

                self.yaw_data.append(current_yaw)
                self.pitch_data.append(current_pitch)

                # yaw range logic
                state_left, start_left = self.handle_range_logic(current_yaw, current_time, self.yaw_left, 
                                                                 self.yaw_current_range if self.yaw_current_range=='yaw_left' else None, 
                                                                 self.yaw_in_range_start if self.yaw_current_range=='yaw_left' else None)
                state_right, start_right = self.handle_range_logic(current_yaw, current_time, self.yaw_right, 
                                                                   self.yaw_current_range if self.yaw_current_range=='yaw_right' else None,
                                                                   self.yaw_in_range_start if self.yaw_current_range=='yaw_right' else None)

                if state_left == 'in':
                    self.yaw_current_range = 'yaw_left'
                    self.yaw_in_range_start = start_left
                elif state_right == 'in':
                    self.yaw_current_range = 'yaw_right'
                    self.yaw_in_range_start = start_right
                else:
                    # 범위 밖
                    if self.yaw_current_range == 'yaw_left':
                        tk_img = self.prepare_image(self.yaw_gauge_time, self.img_cw)
                        if tk_img:
                            images_to_popup.append(tk_img)
                    elif self.yaw_current_range == 'yaw_right':
                        tk_img = self.prepare_image(self.yaw_gauge_time, self.img_ccw)
                        if tk_img:
                            images_to_popup.append(tk_img)

                    self.yaw_current_range = None
                    self.yaw_in_range_start = None
                    self.yaw_gauge_time = 0.0

                # pitch range logic
                state_down, start_down = self.handle_range_logic(current_pitch, current_time, self.pitch_down,
                                                                 self.pitch_current_range if self.pitch_current_range=='pitch_down' else None,
                                                                 self.pitch_in_range_start if self.pitch_current_range=='pitch_down' else None)
                state_up, start_up = self.handle_range_logic(current_pitch, current_time, self.pitch_up,
                                                             self.pitch_current_range if self.pitch_current_range=='pitch_up' else None,
                                                             self.pitch_in_range_start if self.pitch_current_range=='pitch_up' else None)

                if state_down == 'in':
                    self.pitch_current_range = 'pitch_down'
                    self.pitch_in_range_start = start_down
                elif state_up == 'in':
                    self.pitch_current_range = 'pitch_up'
                    self.pitch_in_range_start = start_up
                else:
                    # 범위 밖
                    if self.pitch_current_range == 'pitch_down':
                        tk_img = self.prepare_image(self.pitch_gauge_time, self.img_go)
                        if tk_img:
                            images_to_popup.append(tk_img)
                    elif self.pitch_current_range == 'pitch_up':
                        tk_img = self.prepare_image(self.pitch_gauge_time, self.img_back)
                        if tk_img:
                            images_to_popup.append(tk_img)

                    self.pitch_current_range = None
                    self.pitch_in_range_start = None
                    self.pitch_gauge_time = 0.0

                # 게이지 업데이트
                self.yaw_gauge_time = self.update_gauge_and_image(current_time, self.yaw_in_range_start, self.yaw_current_range, self.yaw_gauge_time)
                self.pitch_gauge_time = self.update_gauge_and_image(current_time, self.pitch_in_range_start, self.pitch_current_range, self.pitch_gauge_time)

                # UI 업데이트
                self.draw_ui(current_pitch, current_yaw, current_time)

            # 만약 이번 사이클에 이미지 표시 대상이 있다면 popup 창 띄우기
            if images_to_popup:
                self.show_popup_images(images_to_popup)

            self.data_event.clear()

        self.root.after(int(1000/120), self.update)

    def __del__(self):
        self.data_collector.running = False
        self.data_collector.join()
