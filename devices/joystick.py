import pygame
from pymycobot import MyCobotSocket
import time

# Pygame 초기화
pygame.init()

# 조이스틱 초기화
pygame.joystick.init()

# 조이스틱이 연결되어 있는지 확인
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("조이스틱이 연결되어 있지 않습니다.")
    exit()
else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("조이스틱 초기화 완료:", joystick.get_name())

# MyCobotSocket 초기화 (로봇 팔의 IP 주소와 포트로 변경하세요)
mc = MyCobotSocket("192.168.0.4", 9000)

# 서버 연결 확인
try:
    mc.connect()
    print("로봇 팔과의 연결이 성공적으로 설정되었습니다.")
except Exception as e:
    print("로봇 팔과의 연결에 실패했습니다:", e)
    exit()

# 초기 좌표 가져오기
coords = mc.get_coords()
print("초기 좌표:", coords)

# 움직임 스케일링 설정 (필요에 따라 조정)
scale_x = 5.0
scale_y = 5.0
scale_z = 5.0
scale_rx = 5.0
scale_ry = 5.0
scale_rz = 5.0

# 조이스틱 데드존 설정
deadzone = 0.1

# 메인 루프 시작
running = True
while running:
    # 이벤트 처리 (Pygame의 응답성을 유지하기 위해 필요)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

    # 조이스틱 축 값 읽기
    pygame.event.pump()
    axis_x = joystick.get_axis(0)  # 왼쪽 스틱 수평
    axis_y = joystick.get_axis(1)  # 왼쪽 스틱 수직
    axis_z = joystick.get_axis(3)  # 오른쪽 스틱 수직

    # 데드존 적용
    if abs(axis_x) < deadzone:
        axis_x = 0.0
    if abs(axis_y) < deadzone:
        axis_y = 0.0
    if abs(axis_z) < deadzone:
        axis_z = 0.0

    # 축 값을 좌표 변화로 매핑
    delta_x = axis_x * scale_x
    delta_y = axis_y * scale_y
    delta_z = axis_z * scale_z

    # 회전 제어를 위한 버튼 읽기
    button_increase_rx = joystick.get_button(4)  # 버튼 번호는 실제 조이스틱에 따라 조정하세요
    button_decrease_rx = joystick.get_button(5)
    button_increase_ry = joystick.get_button(6)
    button_decrease_ry = joystick.get_button(7)
    button_increase_rz = joystick.get_button(8)
    button_decrease_rz = joystick.get_button(9)

    delta_rx = 0.0
    delta_ry = 0.0
    delta_rz = 0.0

    if button_increase_rx:
        delta_rx = scale_rx
    elif button_decrease_rx:
        delta_rx = -scale_rx

    if button_increase_ry:
        delta_ry = scale_ry
    elif button_decrease_ry:
        delta_ry = -scale_ry

    if button_increase_rz:
        delta_rz = scale_rz
    elif button_decrease_rz:
        delta_rz = -scale_rz

    # 현재 좌표 가져오기
    coords = mc.get_coords()
    new_coords = coords.copy()

    # 좌표 변화 적용
    new_coords[0] += delta_x
    new_coords[1] += delta_y
    new_coords[2] += delta_z
    new_coords[3] += delta_rx
    new_coords[4] += delta_ry
    new_coords[5] += delta_rz

    # 로봇의 이동 범위 내로 제한
    new_coords[0] = max(-281.45, min(281.45, new_coords[0]))
    new_coords[1] = max(-281.45, min(281.45, new_coords[1]))
    new_coords[2] = max(-70, min(412.67, new_coords[2]))
    new_coords[3] = max(-180, min(180, new_coords[3]))
    new_coords[4] = max(-180, min(180, new_coords[4]))
    new_coords[5] = max(-180, min(180, new_coords[5]))

    # 새로운 좌표를 로봇에 전송
    speed = 50  # 필요에 따라 조정
    mode = 0    # 0: angular mode, 1: linear mode

    mc.send_coords(new_coords, speed, mode)

    # 잠시 대기 (로봇의 명령 처리 속도에 맞게 조정)
    time.sleep(0.1)

# 종료 처리
pygame.quit()
mc.disconnect()
