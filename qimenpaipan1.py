# 优化后的奇门遁甲排盘代码结构（核心流程示例）
from skyfield.api import load
from datetime import  datetime, timezone, timedelta, time

# 初始化天文数据
load.directory = './'
ts = load.timescale()
eph = load('de421.bsp')

# 辅助函数省略，见原代码实现
# 节气名称与黄经度数、月份的对应关系
tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

jieqi_info = [
    (315, 2, '立春'), (330, 2, '雨水'), (345, 3, '惊蛰'), (0, 3, '春分'),
    (15, 4, '清明'), (30, 4, '谷雨'), (45, 5, '立夏'), (60, 5, '小满'),
    (75, 6, '芒种'), (90, 6, '夏至'), (105, 7, '小暑'), (120, 7, '大暑'),
    (135, 8, '立秋'), (150, 8, '处暑'), (165, 9, '白露'), (180, 9, '秋分'),
    (195, 10, '寒露'), (210, 10, '霜降'), (225, 11, '立冬'), (240, 11, '小雪'),
    (255, 12, '大雪'), (270, 12, '冬至'), (285, 1, '小寒'), (300, 1, '大寒')
]

# 年干对应正月天干规则
gan_to_start = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    '丙': '庚', '辛': '庚',
    '丁': '壬', '壬': '壬',
    '戊': '甲', '癸': '甲'
}
# 阳遁局数表
yang_ju_mapping = {
        "冬至": {"上元": 1, "中元": 7, "下元": 4},
        "小寒": {"上元": 2, "中元": 8, "下元": 5},
        "大寒": {"上元": 3, "中元": 9, "下元": 6},
        "立春": {"上元": 8, "中元": 5, "下元": 2},
        "雨水": {"上元": 9, "中元": 6, "下元": 3},
        "惊蛰": {"上元": 1, "中元": 7, "下元": 4},
        "春分": {"上元": 3, "中元": 9, "下元": 6},
        "清明": {"上元": 4, "中元": 1, "下元": 7},
        "谷雨": {"上元": 5, "中元": 2, "下元": 8},
        "立夏": {"上元": 4, "中元": 1, "下元": 7},
        "小满": {"上元": 5, "中元": 2, "下元": 8},
        "芒种": {"上元": 6, "中元": 3, "下元": 9}
    }
    
# 阴遁局数表
yin_ju_mapping = {
        "夏至": {"上元": 9, "中元": 3, "下元": 6},
        "小暑": {"上元": 8, "中元": 2, "下元": 5},
        "大暑": {"上元": 7, "中元": 1, "下元": 4},
        "立秋": {"上元": 2, "中元": 5, "下元": 8},
        "处暑": {"上元": 1, "中元": 4, "下元": 7},
        "白露": {"上元": 9, "中元": 3, "下元": 6},
        "秋分": {"上元": 7, "中元": 6, "下元": 5},
        "寒露": {"上元": 6, "中元": 5, "下元": 4},
        "霜降": {"上元": 5, "中元": 4, "下元": 3},
        "立冬": {"上元": 6, "中元": 5, "下元": 4},
        "小雪": {"上元": 5, "中元": 8, "下元": 3},
        "大雪": {"上元": 4, "中元": 3, "下元": 2}
}

PALACE_MAP = {
    1: ("坎", "北"), 8: ("艮", "东北"), 3: ("震", "东"),
    4: ("巽", "东南"), 9: ("离", "南"), 2: ("坤", "西南"),
    7: ("兑", "西"), 6: ("乾", "西北"), 5: ("中", "中央")
}
# 节气名称到索引的映射
jieqi_order = {name: idx for idx, (_, _, name) in enumerate(jieqi_info)}
# 获取输入年份的立春准确时间
def find_lichun(year):
    # 设置搜索范围（2月前后）
    start = ts.utc(year, 2, 1)
    end = ts.utc(year, 2, 15)
    
    # 定义黄经检测函数
    def sun_longitude(t):
        astro = eph['earth'].at(t).observe(eph['sun'])
        lat, lon, _ = astro.ecliptic_latlon()
        return lon.degrees
    # 二分法查找黄经315度的时刻
    t0, t1 = start, end
    for _ in range(20):  # 迭代20次达微秒精度
        tm = ts.tt_jd((t0.tt + t1.tt) / 2)
        if sun_longitude(tm) >= 315:
            t1 = tm
        else:
            t0 = tm
    return t1.utc_datetime()

# 获取年干支
def get_year_ganzhi(input_datetime):
    year = input_datetime.year
    # 获取当前年和前一年的立春时间
    lichun_current = find_lichun(year)
    # 判断输入日期是否在当前年立春之后
    if input_datetime >= lichun_current:
        calc_year = year
    else:
        calc_year = year - 1
    # 天干地支表
    idx = (calc_year - 4) % 60
    return tiangan[idx % 10] + dizhi[idx % 12]

# 根据输入的时间找到对应的节气
def find_jieqi(input_dt, forward: bool = True):
    """ 找到输入时间对应的节气及索引
    Args:
        input_dt: 输入时间
        forward: True表示向前找(找小于等于输入时间的最近节气)，
                False表示向后找(找大于输入时间的最近节气)
    Returns:
        (节气时间, 节气名称)
    """
    # 生成前后两年所有节气时间
    jieqi_events = []
    for y in [input_dt.year - 1, input_dt.year]:
        for degree, _, name in jieqi_info:
            jt = get_jieqi_time(y, degree)
            jieqi_events.append((jt, name))
    
    # 按时间排序
    jieqi_events.sort(key=lambda x: x[0])
    
    if forward:
        # 向前找：找到最后一个小于等于输入时间的节气
        for i in range(len(jieqi_events)-1, -1, -1):
            if jieqi_events[i][0] <= input_dt:
                return jieqi_events[i]
    else:
        # 向后找：找到第一个大于输入时间的节气
        for event in jieqi_events:
            if event[0] > input_dt:
                return event
                
    return None

def get_jieqi_time(year, target_degree):
    """ 计算指定年份特定黄经度数对应的节气时间 """
    # 根据黄经度数确定对应的月份
    for degree, month, _ in jieqi_info:
        if degree == target_degree:
            break
    
    # 修正月份范围设置
    start_year = year
    start_month = month - 1
    if start_month < 1:
        start_month = 12
        start_year -= 1
    
    end_year = year
    end_month = month + 1
    if end_month > 12:
        end_month = 1
        end_year += 1
    
    # 创建时间范围（前后各扩展一个月）
    start = ts.utc(start_year, start_month, 1)
    end = ts.utc(end_year, end_month, 1)

    # 二分法查找
    def sun_longitude(t):
        astro = eph['earth'].at(t).observe(eph['sun'])
        return astro.ecliptic_latlon()[1].degrees % 360

    t0, t1 = start, end
    for _ in range(20):
        tm = ts.tt_jd((t0.tt + t1.tt) / 2)
        if sun_longitude(tm) >= target_degree % 360:
            t1 = tm
        else:
            t0 = tm
    return t1.utc_datetime()

# 获取月干支
def get_yue_ganzhi(input_dt):
    """ 计算月干支 """
    # 获取年干
    year_gan = get_year_ganzhi(input_dt)[0]
    
    # 获取对应节气及索引
    jieqi_time, jieqi_name = find_jieqi(input_dt)
    # print(jieqi_time, jieqi_name)
    idx = jieqi_order[jieqi_name]
    month_num = idx // 2  # 0-11对应正月到腊月
    start_gan = gan_to_start[year_gan]
    gan_idx = (tiangan.index(start_gan) + month_num) % 10
    zhi_idx = (month_num + 2) % 12  # 正月寅=2
    
    return tiangan[gan_idx] + dizhi[zhi_idx]

# 获取日时干支
def get_day_houre_ganzhi(input_str):
    # 解析输入时间 [[5]]
    dt = datetime.strptime(input_str, "%Y-%m-%d %H:%M:%S")
    
    # 调整日期：23点后算下一天 [[1]]
    if dt.hour >= 23:
        adjusted_date = dt.date() + timedelta(days=1)
    else:
        adjusted_date = dt.date()
    
    # ------------ 日干支计算 ------------
    # 基准日需按实际情况调整！示例基准：2025-02-24为甲子日
    base_date = datetime(2025, 2, 24).date()
    days_diff = (adjusted_date - base_date).days
    ganzhi_index = days_diff % 60  # 干支60一轮回
    
    ri_gan = gan[ganzhi_index % 10]
    ri_zhi = zhi[ganzhi_index % 12]
    ri_gz = f"{ri_gan}{ri_zhi}"
    
    # ------------ 时干支计算 ------------
    h = dt.hour
    # 确定时支（23点属于次日子时）
    if h == 23:
        h = 24  # 便于计算时辰索引
    zhi_index = (h + 1) // 2 % 12  # 时支索引 [[3]]
    shi_zhi = zhi[zhi_index]
    
    # 根据日干确定时干起始（甲己日甲子，乙庚日丙子...）
    ri_gan_idx = gan.index(ri_gan)
    if ri_gan_idx in [0, 5]:   start = 0  # 甲/己
    elif ri_gan_idx in [1,6]:  start = 2  # 乙/庚→丙
    elif ri_gan_idx in [2,7]:  start = 4  # 丙/辛→戊
    elif ri_gan_idx in [3,8]:  start = 6  # 丁/壬→庚
    else:                      start = 8  # 戊/癸→壬
    
    shi_gan = gan[(start + zhi_index) % 10]
    shi_gz = f"{shi_gan}{shi_zhi}"
    
    return ri_gz, shi_gz

def get_solar_longitude(year, month, day, hour=0, minute=0, second=0):
    """根据输入时间获取太阳黄经度数"""
    # 创建时间对象
    t = ts.utc(year, month, day, hour, minute, second)
    # 获取天体位置
    sun = eph['sun']
    earth = eph['earth']
    astrometric = earth.at(t).observe(sun)
    # 转换黄道坐标系
    lat, lon, _ = astrometric.ecliptic_latlon(t)
    return lon.degrees


def get_futou_details(day_ganzhi, method='置闰'):
    """
    根据日干支和定局方法计算符头、三元及距离天数
    :param day_ganzhi: 日干支，如"甲子"
    :param method: 定局方法，"置闰" 或 "拆补"
    :return: 字典包含符头、三元、距离天数
    """
    # 生成干支表（60甲子）
    
    ganzhi = [f"{gan[i%10]}{zhi[i%12]}" for i in range(60)]
    ganzhi_map = {gz:i for i,gz in enumerate(ganzhi)}

    # 校验输入合法性
    if day_ganzhi not in ganzhi_map:
        raise ValueError("无效的日干支")
    current_idx = ganzhi_map[day_ganzhi]

    # 逆向查找符头
    futou, days_ago = None, 0
    for steps in range(60):
        check_idx = (current_idx - steps) % 60
        check_gz = ganzhi[check_idx]
        zhi_type = ''
        step_day = 0
        # 置闰法：仅匹配甲子、甲午、己卯、己酉 这里定位的是上元第一天
        if method == '置闰' and check_gz in {'甲子','甲午','己卯','己酉'}:
            futou = check_gz
            days_ago = steps
            step_day = days_ago % 5 +1
            if 0 <= days_ago <= 5:
                zhi_type = "上元"
            elif 6 <= days_ago <= 10:
                zhi_type = "中元"
            elif 11 <= days_ago <= 15:
                zhi_type = "下元"
            else:
                zhi_type = "上元"
            break

        # 拆补法：匹配所有甲/己日
        if method == '拆补' and check_gz[0] in {'甲','己'}:
            futou = check_gz
            days_ago = steps
            # 确定三元
            zhi_type = {
                '子':'上元', '午':'上元', '卯':'上元', '酉':'上元',
                '寅':'中元', '申':'中元', '巳':'中元', '亥':'中元',
                '辰':'下元', '戌':'下元', '丑':'下元', '未':'下元'
            }[futou[1]]
            break

    return {'符头': futou, '上中下元': zhi_type, '距离天数': days_ago, '某元第几天': step_day}

class QimenPan:
    def __init__(self, ju_number,is_yang,current_time,shigan):
        self.ju_number = ju_number
        self.is_yang = is_yang
        self.current_time = current_time
        self.shigan = shigan
        # 初始化九宫数据结构（增加天禽星处理）
        self.palaces = {num: {
            'earth': None, 'sky': None, 'door': None, 
            'star': None, 'shen': None
        } for num in PALACE_MAP}
    def arrange_earth_plate(self):
        # 正确顺序：六仪(戊己庚辛壬癸) + 三奇(乙丙丁)
        qiyi_order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]  
        
        # 确定戊的起始宫位（阳遁=局数，阴遁=10-局数）
        start_pos = self.ju_number if self.is_yang else 10 - self.ju_number
        
        # 生成九宫遍历路径（阳遁顺行，阴遁逆行）
        positions = []
        current = start_pos
        for _ in range(9):
            positions.append(current)
            current = current % 9 + 1 if self.is_yang else (current - 2) % 9 + 1
        
        # 填充天干（六仪→三奇循环）  
        for i, pos in enumerate(positions):
            self.palaces[pos]['earth'] = qiyi_order[i % 6] if i <6 else qiyi_order[6 + (i-6)%3]

    def print_pan(self):
        print(self.is_yang)
        print(self.ju_number)


class QiMenDunjiaPan:
    def __init__(self, input_datetime_str):
        self.input_dt = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        self.input_utc = self.input_dt.replace(tzinfo=timezone.utc)

    def calculate_ganzhi(self):
        """计算干支"""
        self.year_gz = get_year_ganzhi(self.input_utc)
        self.month_gz = get_yue_ganzhi(self.input_utc)
        self.day_gz, self.hour_gz = get_day_houre_ganzhi(self.input_dt.strftime('%Y-%m-%d %H:%M:%S'))
        print(self.year_gz,self.month_gz,self.day_gz, self.hour_gz)

    def determine_yinyang(self):
        """定性阴阳遁"""
        # jieqi_time, jieqi_name = find_jieqi(self.futou_jieqi_time)
        # self.jieqi_name = jieqi_name
        # self.jieqi_time = jieqi_time
        lon = get_solar_longitude(self.futou_jieqi_time.year, self.futou_jieqi_time.month, self.futou_jieqi_time.day,
                                  self.futou_jieqi_time.hour, self.futou_jieqi_time.minute)
        self.is_yang = lon >= 270 or lon < 90
        # print(jieqi_time, jieqi_name)

    def determine_futou_sanyuan(self):
        """获取符头及上中下元"""
        futou_info = get_futou_details(self.day_gz)
        self.futou = futou_info['符头']
        self.sanyuan = futou_info['上中下元']
        self.futou_days_diff = futou_info['距离天数']
        self.stepday = futou_info['某元第几天']
        # 将 date 转换为 datetime，使用当天零点
        self.futou_date = datetime.combine(
            self.input_dt.date() - timedelta(days=self.futou_days_diff),
            self.input_dt.time(),   # 时间设为 00:00:00
            tzinfo=timezone.utc
        )
        jieqi_time, jieqi_name =  find_jieqi(self.input_utc)
        self.jieqi_time = jieqi_time
        self.jieqi_name = jieqi_name
        print(jieqi_time, jieqi_name)
        print(self.jieqi_time, self.futou_date)
        if self.jieqi_time >= self.futou_date:
            '''如果节气大于符头'''
            self.futou_jieqi_name = self.jieqi_name
            self.futou_jieqi_time = self.jieqi_time
        else: 
            '''这里需要根据符头修正节气, 取符头节气'''
            jieqi_time_f, jieqi_name_f =  find_jieqi(self.futou_date)
            self.futou_jieqi_name = jieqi_name_f
            self.futou_jieqi_time = jieqi_time_f
        '''其实计算阴阳遁取决于符头的节气'''
        self.determine_yinyang()
        print(self.futou, self.sanyuan, self.futou_days_diff, self.futou_date, self.stepday, self.futou_jieqi_time, self.futou_jieqi_name)

    def determine_ju_number(self):
        """获取局数"""
        ju_mapping = yang_ju_mapping if self.is_yang else yin_ju_mapping
        self.ju_number = ju_mapping[self.futou_jieqi_name][self.sanyuan]

    def create_pan(self):
        self.qimen_pan = QimenPan(
            ju_number=self.ju_number,
            is_yang=self.is_yang,
            current_time=self.input_dt,
            shigan=self.hour_gz
        )
        self.qimen_pan.arrange_earth_plate()
        # self.qimen_pan.arrange_heaven_plate()
        # self.qimen_pan.arrange_sky_plate(self.hour_gz)
        # self.qimen_pan.arrange_doors()
        # self.qimen_pan.arrange_shen()

    def run(self):
        self.calculate_ganzhi()
        # self.determine_yinyang()
        self.determine_futou_sanyuan()
        self.determine_ju_number()
        self.create_pan()
        self.qimen_pan.print_pan()


if __name__ == '__main__':
    datetime_str = "2024-11-19 01:30:00" #f8
    # datetime_str = "2025-02-28 01:30:00" #t9
    qimen = QiMenDunjiaPan(datetime_str)
    qimen.run()
