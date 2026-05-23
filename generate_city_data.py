"""
生成城市路况驾驶模拟数据 (1.5分钟 = 3600帧)
- 频繁启停 (模拟红绿灯)
- 急转弯 (路口)
- 路面坡度变化
- 速度范围 0~60 km/h
"""
import csv
import numpy as np
from scipy.interpolate import CubicSpline

np.random.seed(123)  # 不同种子产生不同数据特征

dt = 0.025
n = 3600  # 1.5分钟 @ 40fps
t = np.arange(n) * dt

# ============================================================
# 城市驾驶速度曲线: 频繁加速减速，多次启停
# ============================================================
# 设计多个短速度脉冲 (km/h → m/s 转换)
t_brk = np.array([
    0, 4, 8, 12, 16,        # 0~16s: 起步→加速→减速→停止 (第一个红绿灯)
    20, 22, 28, 32, 36,      # 16~36s: 启动→加速→巡航→减速→停止
    40, 44, 50, 54, 58,      # 36~58s: 启动→加速→过弯减速→出弯加速→停止
    62, 66, 72, 76, 80,      # 58~80s: 启动→加速→巡航→减速→停(让行)
    84, 86, 92, 96,          # 80~96s: 启动→加速→巡航→减速
    100, 104, 108, 112, 116, # 96~116s: 启动→加速→减速→慢行→停止
    120, 124, 130, 135, 140, # 116~140s: 启动→加速→减速慢行→入库停车
    145, 150                 # 140~150s: 最终停止
])
# 速度值 m/s (城市道路: 最高约 55 km/h ≈ 15.3 m/s)
v_brk = np.array([
    0, 0, 8, 5, 0,           # 0~16s
    0, 6, 12, 8, 0,          # 16~36s
    0, 7, 5, 10, 0,          # 36~58s
    0, 9, 14, 7, 0,          # 58~80s
    0, 5, 10, 0,             # 80~96s
    0, 7, 12, 4, 0,          # 96~116s
    0, 6, 10, 3, 0,          # 116~140s
    0, 0                     # 140~150s
])

cs_v = CubicSpline(t_brk, v_brk, bc_type=((1, 0.0), (1, 0.0)))
speed = cs_v(t)
speed = np.maximum(speed, 0)

# ============================================================
# 纵向加速度
# ============================================================
ax_body = np.gradient(speed, dt)

# ============================================================
# 偏航角: 多次急转弯 (路口转向)
# ============================================================
yaw_t = np.array([
    0, 12, 16,           # 直行
    20, 24, 28, 32,      # 第一个路口: 左转然后回正
    36, 40, 44, 48,      # 右转 (急弯)
    50, 55, 58,          # 回正直行
    62, 68, 72, 76,      # S形变道
    80, 84, 88,          # 直行
    92, 96,              # 小幅右转
    100, 106, 110,       # 左转
    116, 122, 128,       # 右转 (入库)
    135, 150
])
yaw_v = np.array([
    0, 0, 0,              # 直行
    0, 0.6, 0.8, 0.2,     # 左转 ~45°, 回正
    0.2, -0.5, -0.7, -0.2,# 右转 ~-40°, 回正
    0, 0, 0,              # 直行
    0, 0.3, -0.2, 0,      # S形
    0, 0, 0,              # 直行
    0, 0.2,               # 小幅右转
    0.2, 0.6, 0.4,        # 左转 ~35°
    0.4, -0.5, -0.3,      # 右转 (入库)
    0, 0
])  # rad

cs_yaw = CubicSpline(yaw_t, yaw_v, bc_type=((1, 0.0), (1, 0.0)))
yaw = cs_yaw(t)
yaw = np.clip(yaw, -1.0, 1.0)

# ============================================================
# 世界坐标位置
# ============================================================
pos_x = np.zeros(n)
pos_y = np.zeros(n)
for i in range(1, n):
    pos_x[i] = pos_x[i-1] + speed[i-1] * np.cos(yaw[i-1]) * dt
    pos_y[i] = pos_y[i-1] + speed[i-1] * np.sin(yaw[i-1]) * dt

# ============================================================
# 车身坐标系速度/加速度
# ============================================================
vx_body = speed
yaw_rate = np.gradient(yaw, dt)
# 用平滑函数计算侧向速度，避免sign()突变产生尖峰
vy_body = np.zeros(n)
for i in range(n):
    if speed[i] > 0.5 and abs(yaw_rate[i]) > 0.001:
        # tanh实现平滑过渡，时间常数20帧(0.5s)
        slip_angle = 0.03 * np.tanh(yaw_rate[i] * 30)
        vy_body[i] = speed[i] * slip_angle

az_body = np.random.normal(0, 0.03, n)
# 侧向加速度: 侧滑导数 + 向心加速度
ay_body = np.gradient(vy_body, dt)
for i in range(n):
    if speed[i] > 0.5:
        ay_body[i] += speed[i] * yaw_rate[i]

# 路面坡度 (城市道路有坡度变化)
road_slope = np.zeros(n)
for i in range(n):
    if 25 < t[i] < 45:
        road_slope[i] = 0.03 * np.sin((t[i] - 25) * 0.15)  # 上坡+下坡
    elif 70 < t[i] < 100:
        road_slope[i] = -0.02 * np.sin((t[i] - 70) * 0.1)  # 下坡

# Z方向受坡度影响
pos_z = np.cumsum(speed * road_slope * dt)
vz_body = np.gradient(pos_z, dt)
az_body += np.gradient(vz_body, dt)

# ============================================================
# 姿态角: Roll(侧倾) + Pitch(俯仰+坡道)
# ============================================================
roll = np.zeros(n)
for i in range(n):
    if speed[i] > 0.5:
        roll[i] = -0.06 * yaw[i] * min(speed[i] / 15, 1.5)  # 城市转弯更急侧倾更大
pitch = -0.015 * ax_body + road_slope * 0.5  # 加速俯仰 + 坡道补偿
roll = np.clip(roll, -0.15, 0.15)
pitch = np.clip(pitch, -0.12, 0.12)

# ============================================================
# 角速度/角加速度
# ============================================================
ang_vel_x = np.gradient(roll, dt)
ang_vel_y = np.gradient(pitch, dt)
ang_vel_z = yaw_rate
ang_acc_x = np.gradient(ang_vel_x, dt)
ang_acc_y = np.gradient(ang_vel_y, dt)
ang_acc_z = np.gradient(ang_vel_z, dt)

# ============================================================
# 控制输入
# ============================================================
throttle = np.zeros(n)
brake = np.zeros(n)
steering = np.zeros(n)

for i, time in enumerate(t):
    # Throttle: 频繁启停
    if time < 4:
        throttle[i] = 0
    elif time < 8:
        throttle[i] = 0.3 * (time - 4) / 4
    elif time < 12:
        throttle[i] = 0.35 - 0.1 * (time - 8) / 4
    elif time < 16:
        throttle[i] = 0.05
    elif time < 22:
        throttle[i] = 0.25 * (time - 20) / 2
    elif time < 28:
        throttle[i] = 0.3
    elif time < 32:
        throttle[i] = 0.3 - 0.15 * (time - 28) / 4
    elif time < 36:
        throttle[i] = 0.05
    elif time < 40:
        throttle[i] = 0.3 * (time - 36) / 4
    elif time < 44:
        throttle[i] = 0.25
    elif time < 50:
        throttle[i] = 0.2 + 0.1 * (time - 44) / 6
    elif time < 54:
        throttle[i] = 0.3
    elif time < 58:
        throttle[i] = 0.3 - 0.2 * (time - 54) / 4
    elif time < 62:
        throttle[i] = 0.05
    elif time < 66:
        throttle[i] = 0.3 * (time - 62) / 4
    elif time < 72:
        throttle[i] = 0.35
    elif time < 76:
        throttle[i] = 0.35 - 0.15 * (time - 72) / 4
    elif time < 80:
        throttle[i] = 0.05
    elif time < 84:
        throttle[i] = 0.2 * (time - 80) / 4
    elif time < 86:
        throttle[i] = 0.15
    elif time < 92:
        throttle[i] = 0.25
    elif time < 96:
        throttle[i] = 0.25 - 0.15 * (time - 92) / 4
    elif time < 100:
        throttle[i] = 0.05
    elif time < 104:
        throttle[i] = 0.28 * (time - 100) / 4
    elif time < 108:
        throttle[i] = 0.32
    elif time < 112:
        throttle[i] = 0.32 - 0.12 * (time - 108) / 4
    elif time < 116:
        throttle[i] = 0.08
    elif time < 120:
        throttle[i] = 0.05
    elif time < 124:
        throttle[i] = 0.3 * (time - 120) / 4
    elif time < 130:
        throttle[i] = 0.3 - 0.1 * (time - 124) / 6
    elif time < 135:
        throttle[i] = 0.15 - 0.1 * (time - 130) / 5
    else:
        throttle[i] = 0

    # Brake: 频繁制动
    if 12 <= time < 16:
        brake[i] = 0.3 + 0.1 * (time - 12) / 4
    elif 32 <= time < 36:
        brake[i] = 0.4 + 0.15 * (time - 32) / 4
    elif 54 <= time < 58:
        brake[i] = 0.35 * (time - 54) / 4
    elif 76 <= time < 80:
        brake[i] = 0.45 * (time - 76) / 4
    elif 92 <= time < 96:
        brake[i] = 0.3 * (time - 92) / 4
    elif 112 <= time < 116:
        brake[i] = 0.5 * (time - 112) / 4
    elif 130 <= time < 135:
        brake[i] = 0.2 + 0.3 * (time - 130) / 5
    elif 135 <= time < 140:
        brake[i] = 0.5 + 0.3 * (time - 135) / 5
    elif time >= 140:
        brake[i] = 0.9
    else:
        brake[i] = 0

    # Steering: 急转弯
    if 20 <= time < 24:
        steering[i] = 0.35 * (time - 20) / 4
    elif 24 <= time < 28:
        steering[i] = 0.35
    elif 28 <= time < 32:
        steering[i] = 0.35 * (1 - (time - 28) / 4)
    elif 36 <= time < 40:
        steering[i] = -0.3 * (time - 36) / 4
    elif 40 <= time < 44:
        steering[i] = -0.3
    elif 44 <= time < 48:
        steering[i] = -0.3 * (1 - (time - 44) / 4)
    elif 62 <= time < 66:
        steering[i] = 0.2 * (time - 62) / 4
    elif 66 <= time < 68:
        steering[i] = 0.2
    elif 68 <= time < 72:
        steering[i] = -0.15 * (time - 68) / 4
    elif 84 <= time < 88:
        steering[i] = 0.12 * (time - 84) / 4
    elif 88 <= time < 92:
        steering[i] = 0.12 * (1 - (time - 88) / 4)
    elif 100 <= time < 104:
        steering[i] = 0.25 * (time - 100) / 4
    elif 104 <= time < 106:
        steering[i] = 0.25
    elif 106 <= time < 110:
        steering[i] = 0.25 * (1 - (time - 106) / 4)
    elif 116 <= time < 120:
        steering[i] = -0.28 * (time - 116) / 4
    elif 120 <= time < 124:
        steering[i] = -0.28
    elif 124 <= time < 128:
        steering[i] = -0.28 * (1 - (time - 124) / 4)
    elif 128 <= time < 132:
        steering[i] = 0.1 * (time - 128) / 4
    elif 132 <= time < 135:
        steering[i] = 0.1 * (1 - (time - 132) / 3)
    else:
        steering[i] = 0
    steering[i] += np.random.normal(0, 0.005)

# ============================================================
# 挡位
# ============================================================
gear = np.ones(n, dtype=int)
speed_kmh = speed * 3.6
for i in range(n):
    if speed_kmh[i] < 1:
        gear[i] = 1
    elif speed_kmh[i] < 10:
        gear[i] = 2
    elif speed_kmh[i] < 22:
        gear[i] = 3
    elif speed_kmh[i] < 38:
        gear[i] = 4
    else:
        gear[i] = 5

# ============================================================
# 引擎转速 (城市行驶转速变化更大)
# ============================================================
gear_ratios = {1: 420, 2: 280, 3: 200, 4: 150, 5: 110}
revolution = np.zeros(n)
for i in range(n):
    if speed[i] < 0.2:
        revolution[i] = 800 + np.random.normal(0, 20)
    else:
        gr = gear_ratios[gear[i]]
        base_rpm = 750 + speed_kmh[i] * gr
        acc_boost = max(0, ax_body[i] * 150)
        revolution[i] = base_rpm + acc_boost + np.random.normal(0, 15)
revolution = np.clip(revolution, 650, 6500)

# ============================================================
# SpeedMeter + Mileage
# ============================================================
speed_meter = speed_kmh + np.random.normal(0, 0.2, n)
mileage_start = 23456.7
mileage = mileage_start + np.cumsum(speed * dt) / 1000

# ============================================================
# RoadCurvature / VehicleOffset
# ============================================================
road_curvature = np.zeros(n)
for i in range(n):
    if 20 <= t[i] < 32 and speed[i] > 1:
        progress = (t[i] - 20) / 12
        road_curvature[i] = 0.005 * (1 - abs(progress - 0.5) * 2) * min(speed[i] / 10, 1.5)
    elif 36 <= t[i] < 48 and speed[i] > 1:
        progress = (t[i] - 36) / 12
        road_curvature[i] = -0.006 * (1 - abs(progress - 0.5) * 2)
    elif 100 <= t[i] < 110 and speed[i] > 1:
        progress = (t[i] - 100) / 10
        road_curvature[i] = 0.004 * (1 - abs(progress - 0.5) * 2)

vehicle_offset = np.zeros(n)
for i in range(1, n):
    vehicle_offset[i] = vehicle_offset[i-1] * 0.995 + np.random.normal(0, 0.008)

# ============================================================
# Parking
# ============================================================
parking = np.zeros(n)
parking[t >= 147] = 1.0

# ============================================================
# 传感器噪声
# ============================================================
loc_x = pos_x + np.random.normal(0, 0.003, n)
loc_y = pos_y + np.random.normal(0, 0.003, n)
loc_z = pos_z + np.random.normal(0, 0.002, n)
ax_body_n = ax_body + np.random.normal(0, 0.01, n)
ay_body_n = ay_body + np.random.normal(0, 0.01, n)
az_body_n = az_body + np.random.normal(0, 0.008, n)

# ============================================================
# 时间戳 (从 14:15:00:000 开始)
# ============================================================
start_ms = 14 * 3600000 + 15 * 60000
timestamps = []
for i in range(n):
    ms = start_ms + i * 25
    h = (ms // 3600000) % 24
    rem = ms % 3600000
    m = rem // 60000
    rem2 = rem % 60000
    s = rem2 // 1000
    remain_ms = rem2 % 1000
    timestamps.append(f"{h:02d}:{m:02d}:{s:02d}:{remain_ms:03d}")

# ============================================================
# 写入 CSV
# ============================================================
headers = [
    '序号', 'TimeStamp',
    'Location_X', 'Location_Y', 'Location_Z',
    'Pitch', 'Yaw', 'Roll',
    'VehicleOffset', 'RoadCurvature', 'RoadSlope',
    'ShaftAcceleration_X', 'ShaftAcceleration_Y', 'ShaftAcceleration_Z',
    'ShaftSpeed_X', 'ShaftSpeed_Y', 'ShaftSpeed_Z',
    'AngularVelocity_X', 'AngularVelocity_Y', 'AngularVelocity_Z',
    'AngularAcceleration_X', 'AngularAcceleration_Y', 'AngularAcceleration_Z',
    'Revolution', 'SpeedMeter', 'Gear', 'Mileage',
    'Steering', 'Throttle', 'Brake', 'Parking'
]

output_path = r'D:\YYClaw\驾驶展示页\city_driving_test_data.csv'

with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for i in range(n):
        writer.writerow([
            i + 1, timestamps[i],
            f"{loc_x[i]:.4f}", f"{loc_y[i]:.4f}", f"{loc_z[i]:.4f}",
            f"{pitch[i]:.5f}", f"{yaw[i]:.5f}", f"{roll[i]:.5f}",
            f"{vehicle_offset[i]:.4f}", f"{road_curvature[i]:.6f}", f"{road_slope[i]:.6f}",
            f"{ax_body_n[i]:.4f}", f"{ay_body_n[i]:.4f}", f"{az_body_n[i]:.4f}",
            f"{vx_body[i]:.4f}", f"{vy_body[i]:.6f}", f"{vz_body[i]:.6f}",
            f"{ang_vel_x[i]:.6f}", f"{ang_vel_y[i]:.6f}", f"{ang_vel_z[i]:.6f}",
            f"{ang_acc_x[i]:.6f}", f"{ang_acc_y[i]:.6f}", f"{ang_acc_z[i]:.6f}",
            f"{revolution[i]:.1f}", f"{speed_meter[i]:.2f}", str(gear[i]),
            f"{mileage[i]:.4f}",
            f"{steering[i]:.4f}", f"{throttle[i]:.4f}", f"{brake[i]:.4f}", f"{parking[i]:.4f}",
        ])

print(f'城市驾驶数据已生成: {output_path}')
print(f'行数: {n} | 时长: {n*dt:.0f}s | 帧率: {1/dt:.0f}fps')
print(f'最高速度: {np.max(speed)*3.6:.1f} km/h')
print(f'最大加速度: {np.max(ax_body):.3f} m/s²')
print(f'最大减速度: {np.min(ax_body):.3f} m/s²')
print(f'最大侧向G: {np.max(np.abs(ay_body)):.3f} m/s²')
print(f'启停次数: {sum(1 for i in range(1,n) if speed[i-1]==0 and speed[i]>0)}')
print(f'行驶里程: {mileage[-1] - mileage_start:.3f} km')
print(f'换挡次数: {np.sum(np.diff(gear) != 0)}')
