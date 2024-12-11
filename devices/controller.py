import time
from pymycobot import MyCobot280Socket


mc = MyCobot280Socket("192.168.0.4",9000)
mc.set_fresh_mode(1)


mc.send_angles([0,-112,82,30,0,0],20)

time.sleep(0.5)

mc.send_angles([0,0,0,0,0,0],20)
