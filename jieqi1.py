from skyfield.api import load, Topos
from skyfield.units import Angle

# 初始化天文数据
load.directory = './'  # 从当前目录加载星历文件
ts = load.timescale()
eph = load('de421.bsp')

def get_solar_longitude(year, month, day, hour=0, minute=0, second=0):
    # 创建时间对象
    t = ts.utc(year, month, day, hour, minute, second)
    
    # 获取天体位置
    sun = eph['sun']
    earth = eph['earth']
    astrometric = earth.at(t).observe(sun)
    
    # 转换黄道坐标系
    lat, lon, _ = astrometric.ecliptic_latlon(t)
    return lon.degrees

# 示例：计算2024年冬至时刻（北京时间2024-12-21 17:20）
longitude = get_solar_longitude(2025, 2, 24, 17, 20)
print(f"太阳黄经：{longitude:.6f}°")
