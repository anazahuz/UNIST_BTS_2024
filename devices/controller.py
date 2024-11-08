from pymycobot import MyCobotSocket

mc = MyCobotSocket("192.168.0.18",9000)

res = mc.get_angles()
print(res)
mc.send_angles([50,0,0,0,0,0],20)