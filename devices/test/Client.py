# demo
from pymycobot import MyCobot280Socket
import time

# Port 9000 is used by default
mc = MyCobot280Socket("192.168.0.3",9000)

res = mc.get_angles()
print(res)

mc.send_angles([0,100,0,80,90,0],50)
print('a')
mc.send_angles([10,0,0,30,0,0],40)
time.sleep(3)
print('b')
mc.send_angles([30,10,0,60,0,70],80)

mc.send_angles([0,0,0,0,0,0],50)
print('c')