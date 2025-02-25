from skyfield.api import load, wgs84, utc
from skyfield.framelib import ecliptic_frame
from datetime import datetime, timedelta
import numpy as np
# load.directory = 'https://astro.yseapp.com/'  # 使用国内镜像
load.directory = './'  # 从当前目录加载星历文件
def calculate_solar_longitude(input_time):
    # 加载天文数据（首次运行会自动下载约11MB的de421星历）
    ts = load.timescale()
    planets = load('de421.bsp')  # 加载NASA星历
    
    # 修改时间处理逻辑：先转换为UTC时间，并添加时区信息
    utc_time = (input_time - timedelta(hours=8)).replace(tzinfo=utc)
    t = ts.from_datetime(utc_time)
    
    # 计算太阳的地心位置（ICRS坐标系）
    earth = planets['earth']
    sun = planets['sun']
    astrometric = earth.at(t).observe(sun)
    
    # 转换到黄道坐标系
    ecliptic_pos = astrometric.frame_latlon(ecliptic_frame)
    # 解构元组，获取黄经值
    lon = ecliptic_pos[0]
    lon_deg = lon.degrees  # 黄经（度数）
    
    return lon_deg % 360
# 示例使用（北京时间2025-02-25 14:30）
input_time = datetime(2025, 2, 25, 14, 30)
degrees = calculate_solar_longitude(input_time)

print(f"太阳黄经：{degrees:.6f}°")

