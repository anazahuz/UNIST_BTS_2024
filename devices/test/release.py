from pymycobot import MyCobot280Socket
mc = MyCobot280Socket("192.168.0.4",9000)

mc.release_all_servos()