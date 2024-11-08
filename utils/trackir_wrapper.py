# utils/trackir_wrapper.py

from utils.trackir import TrackIRDLL

class TrackIRWrapper:
    def __init__(self, hwnd):
        self.trackir = TrackIRDLL(hwnd)

    def get_data(self):
        return self.trackir.NP_GetData()
