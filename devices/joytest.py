import keyboard as key
import time
from pymycobot import MyCobot280Socket


mc = MyCobot280Socket("192.168.0.4",9000)
mc.set_fresh_mode(1)


mc.send_angles([0,-112,82,30,0,0],80)


time.sleep(3)

pos = mc.get_coords()

scale_move = 3.0
scale_rotate = 180.0

speed = 30
mode = 0

running = True

while running:
    cur_pos = mc.get_coords()
    #cur_ang = mc.get_angles()
    print('cur pos = ', cur_pos)
    #print('cur ang = ', cur_ang)
    

    if key.read_key() == None :
        print('Waiting...')
    elif key.read_key() == 'up' :
        pos[0] = pos[0] + 10
        print('forward')
    elif key.read_key() == 'down' :
        pos[0] = pos[0] - 10
        print('backward')
    elif key.read_key() == 'left' :
        pos[4] = pos[4] - 30
        print('counterclockwise')
    elif key.read_key() == 'right' :
        pos[4] = pos[4] + 30
        print('clockwise')
    
    print('target =', pos)

    mc.send_coords(pos, speed, mode)

    time.sleep(0.1)


mc.disconnect()
