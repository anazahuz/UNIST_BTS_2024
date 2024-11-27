from pymycobot import MyCobot280Socket
mc = MyCobot280Socket("192.168.0.4",9000)

mc.send_angles([0,0,0,0,90,0],80)

#mc.send_angles([90,60,120,-90,0,0],100)
