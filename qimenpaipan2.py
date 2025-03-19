# 奇门遁甲排盘
from datetime import  datetime, timezone, timedelta
from skyfield.api import load, Topos
from skyfield.units import Angle
import bisect
from collections import deque
# 初始化天文数据
load.directory = './'  # 从当前目录加载星历文件
ts = load.timescale()
eph = load('de421.bsp')
tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
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
qiyi_order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]  
# ================== 基础数据定义 ==================
# 九宫方位映射（洛书数序）
# ================== 修正后的基础数据 ==================
PALACE_MAP = {
    1: ("坎", "北"), 8: ("艮", "东北"), 3: ("震", "东"),
    4: ("巽", "东南"), 9: ("离", "南"), 2: ("坤", "西南"),
    7: ("兑", "西"), 6: ("乾", "西北"), 5: ("中", "中央")
}

# 宫位对应的原始星（中宫天禽的特殊处理）
POS_STAR_MAP = {
    1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅",
    5: "天禽", 6: "天心", 7: "天柱", 8: "天任", 9: "天英"
}
# 六甲旬首对应的宫位
XUNSHOU_POSITION = {
    "甲子": 1, "甲戌": 2, "甲申": 8,
    "甲午": 9, "甲辰": 4, "甲寅": 3
}
# 天干地支序号映射（补充到类中）
TIANGAN_ORDER = {"甲":0, "乙":1, "丙":2, "丁":3, "戊":4, 
                "己":5, "庚":6, "辛":7, "壬":8, "癸":9}
DIZHI_ORDER = {"子":0, "丑":1, "寅":2, "卯":3, "辰":4, "巳":5,
              "午":6, "未":7, "申":8, "酉":9, "戌":10, "亥":11}

# 旬首六仪映射[[14]]
XUNSHOU_LIUYI = {
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸"
}
# 九星原始宫位映射（依据《奇门遁甲基础》）
STAR_ORIGIN_POS = {
    "天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4, 
    "天禽": 5, "天心": 6, "天柱": 7, "天任": 8, "天英":9
}
STAR_ORIGIN_ARRAY = ["天蓬","天任","天冲","天辅","天英","天芮","天柱","天心"]
MEN_ORDER = ["休","生","伤","杜","景","死","惊","开"]
SHEN_ORDER_YANG = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
SHEN_ORDER_YIN = ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "腾蛇"]
# 地支与宫位映射（时支对应宫位）
SHIZHI_POSITION = {
    "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
    "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6
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
    
    ri_gan = tiangan[ganzhi_index % 10]
    ri_zhi = dizhi[ganzhi_index % 12]
    ri_gz = f"{ri_gan}{ri_zhi}"
    
    # ------------ 时干支计算 ------------
    h = dt.hour
    # 确定时支（23点属于次日子时）
    if h == 23:
        h = 24  # 便于计算时辰索引
    zhi_index = (h + 1) // 2 % 12  # 时支索引 [[3]]
    shi_zhi = dizhi[zhi_index]
    
    # 根据日干确定时干起始（甲己日甲子，乙庚日丙子...）
    ri_gan_idx = tiangan.index(ri_gan)
    if ri_gan_idx in [0, 5]:   start = 0  # 甲/己
    elif ri_gan_idx in [1,6]:  start = 2  # 乙/庚→丙
    elif ri_gan_idx in [2,7]:  start = 4  # 丙/辛→戊
    elif ri_gan_idx in [3,8]:  start = 6  # 丁/壬→庚
    else:                      start = 8  # 戊/癸→壬
    
    shi_gan = tiangan[(start + zhi_index) % 10]
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

def get_solstices(year: int) -> tuple[datetime, datetime]:
    """获取指定年份的夏至和冬至时间
    Args:
        year: 年份
    Returns:
        tuple[datetime, datetime]: (夏至时间, 冬至时间)
    """
    summer_solstice = None
    winter_solstice = None
    for degree, _, name in jieqi_info:
        if name == '夏至':
            summer_solstice = get_jieqi_time(year, degree)
        elif name == '冬至':
            winter_solstice = get_jieqi_time(year, degree)
        # 如果两个至点都找到了就可以退出循环
        if summer_solstice and winter_solstice:
            break
    
    return summer_solstice, winter_solstice

def get_futou_details(day_ganzhi, method='置闰'):
    """
    根据日干支和定局方法计算符头、三元及距离天数
    :param day_ganzhi: 日干支，如"甲子"
    :param method: 定局方法，"置闰" 或 "拆补"
    :return: 字典包含符头、三元、距离天数
    """
    # 生成干支表（60甲子）
    
    ganzhi = [f"{tiangan[i%10]}{dizhi[i%12]}" for i in range(60)]
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

    return {'符头': futou, '上中下元': zhi_type, '符头差日': days_ago, '某元第几天': step_day}

class QiMenDunjiaPan:
    def __init__(self, input_datetime_str):
        self.input_dt = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        self.input_utc = self.input_dt.replace(tzinfo=timezone.utc)
        # 初始化九宫数据结构（增加天禽星处理）
        self.palaces = {num: {
            'earth': None, 'sky': None, 'door': None, 
            'star': None, 'shen': None
        } for num in PALACE_MAP}
    def calculate_ganzhi(self):
        """计算干支"""
        self.year_gz = get_year_ganzhi(self.input_utc)
        self.month_gz = get_yue_ganzhi(self.input_utc)
        self.day_gz, self.hour_gz = get_day_houre_ganzhi(self.input_dt.strftime('%Y-%m-%d %H:%M:%S'))
        print(self.year_gz,self.month_gz,self.day_gz, self.hour_gz)
    
    def calculate_futou(self):
        """计算符头日期"""
        futou_info = get_futou_details(self.day_gz)
        futou_days_diff = futou_info['符头差日']
        futou_date = datetime.combine(
            self.input_dt.date() - timedelta(days=futou_days_diff),
            self.input_dt.time(),
            tzinfo=self.input_dt.tzinfo if self.input_dt.tzinfo else None
        )
        self.futou_date = futou_date
        print(futou_date)
    
    def get_futou_jieqi(self):
        """获取符头所在的节气，夏至或者冬至"""
        print(get_solstices(self.futou_date.year))
        # 获取夏至和冬至时间
        summer_solstice, winter_solstice = get_solstices(self.futou_date.year)

        # 确保时区一致性
        futou_date_naive = self.futou_date.replace(tzinfo=None)
        summer_solstice_naive = summer_solstice.replace(tzinfo=None)
        winter_solstice_naive = winter_solstice.replace(tzinfo=None)

        # 判断符头日期在夏至和冬至的相对位置
        if futou_date_naive < summer_solstice_naive:
            # 如果在夏至前，需要获取前一年的冬至时间
            prev_summer, prev_winter = get_solstices(self.futou_date.year - 1)
            prev_winter_naive = prev_winter.replace(tzinfo=None)
            period = "夏至前"
            self.period = '冬至'
            effective_jieqi = prev_winter_naive  # 使用前一年的冬至
        elif futou_date_naive < winter_solstice_naive:
            period = "夏至后冬至前"
            self.period = '夏至'
            effective_jieqi = summer_solstice_naive  # 使用当年的夏至
        else:
            period = "冬至后"
            self.period = '冬至'
            effective_jieqi = winter_solstice_naive  # 使用当年的冬至
        

        print(f"符头日期 {self.futou_date} 在{period}")
        # 计算参考节气日期的日干支
        effective_day_ganzhi, _ = get_day_houre_ganzhi(effective_jieqi.strftime("%Y-%m-%d %H:%M:%S"))

        # 获取符头信息
        futou_info = get_futou_details(effective_day_ganzhi)

        # 计算符头日期，保持与参考节气相同的时间部分
        futou_days_diff = futou_info['符头差日']
        effective_futou_date = datetime.combine(
            effective_jieqi.date() - timedelta(days=futou_days_diff),
            effective_jieqi.time(),
            tzinfo=effective_jieqi.tzinfo
        )
        print(f"参考节气时间: {effective_jieqi}")
        print(f"参考节气日干支: {effective_day_ganzhi}")
        print(f"符头信息: {futou_info}")
        print(f"符头日期: {effective_futou_date}")
        if futou_info['符头差日'] > 9 :
            print('置闰')
            if self.period == '冬至':
               self.period = '大雪'
            if self.period == '夏至':
                self.period = '芒种'
        self.input_dt - effective_futou_date
        # 计算输入日期与符头日期的差值
        input_futou_diff = (self.input_dt.replace(tzinfo=None) - effective_futou_date.replace(tzinfo=None)).days
        print(f"输入日期与符头相差{input_futou_diff}天")
        # 计算除以15的整数部分和余数部分
        quotient, remainder = divmod(input_futou_diff, 15)
        print(f"输入日期与符头相差{input_futou_diff}天")
        print(f"除以15的结果：整数部分={quotient}，余数部分={remainder}")
        # 在节气列表中找到起始节气的索引
        start_index = None
        for i, (_, _, name) in enumerate(jieqi_info):
            if name == self.period:
                start_index = i
                break

        if start_index is not None:
            # 计算目标节气的索引（考虑循环）
            target_index = (start_index + quotient) % len(jieqi_info)
            # 获取目标节气信息
            target_degree, target_month, target_name = jieqi_info[target_index]
            
            print(f"从{self.period}开始，向后第{quotient}个节气是：{target_name}")
            self.curr_jieqi = target_name # 这里很重要，计算出了当前的真正节气
            quotient_yuan, remainder_yuan= divmod(remainder, 5)
            if quotient_yuan == 0:
                self.curr_yuan = '上元'
            if quotient_yuan == 1:
                self.curr_yuan = '中元'
            if quotient_yuan == 2:
                self.curr_yuan = '下元'
            self.remainder_yuan = remainder_yuan
            print(f"起始节气索引：{start_index}，目标节气索引：{target_index}")
            # 先检查节气是否在阳遁局数表中
            if self.curr_jieqi in yang_ju_mapping:
                self.is_yang = True
                self.ju_number = yang_ju_mapping[self.curr_jieqi][self.curr_yuan]
                print(f"阳遁{self.ju_number}局")
            # 否则检查是否在阴遁局数表中
            elif self.curr_jieqi in yin_ju_mapping:
                self.is_yang = False
                self.ju_number = yin_ju_mapping[self.curr_jieqi][self.curr_yuan]
                print(f"阴遁{self.ju_number}局")
            else:
                print(f"未找到对应的局数映射：节气={self.curr_jieqi}，元={self.curr_yuan}")
        else:
            print(f"未找到起始节气：{self.period}")

    def arrange_earth_plate(self):
        # 正确顺序：六仪(戊己庚辛壬癸) + 三奇(乙丙丁)
        qiyi_order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]  
        
        # 确定戊的起始宫位（阳遁=局数，阴遁=10-局数）
        start_pos = self.ju_number 
        
        # 生成九宫遍历路径（阳遁顺行，阴遁逆行）
        positions = []
        current = start_pos
        for _ in range(9):
            positions.append(current)
            current = current % 9 + 1 if self.is_yang else (current - 2) % 9 + 1
        
        # 填充天干（六仪→三奇循环）  
        for i, pos in enumerate(positions):
            self.palaces[pos]['earth'] = qiyi_order[i % 6] if i <6 else qiyi_order[6 + (i-6)%3]
        dipan_tiangan_array = []
        # 这里是计算外面的那个圈上的地盘天干，一会用它来旋转计算天盘天干
        for pos in [1,8,3,4,9,2,7,6]:
            dipan_tiangan_array.append(self.palaces[pos]['earth'])
        self.dipan_tiangan_array = dipan_tiangan_array


    def arrange_sky_plate(self):
        """天盘和星的排布"""
        # 根据遁局选择宫位顺序
        shigan = self.hour_gz[0]
        positions = [1, 8, 3, 4, 9, 2, 7, 6, 5]
        # positions = [1, 8, 3, 4, 9, 2, 7, 6, 5] if self.is_yang else [9, 2, 7, 6, 1, 8, 3, 4, 5]
        # positions = [1, 2,3,4,5,6,7,8,9] if self.is_yang else [9,8,7,6,5,4,3,2,1]
        # 获取值符星和原始位置
        zhifu_star = self._get_zhifu_star()
        original_pos = self._get_star_original_pos(zhifu_star)
        xunshou_original_pos = self._get_xunshou_original_pos(self.xunshou_ganzhi)
        xunshou_original_pos = 2 if xunshou_original_pos == 5 else xunshou_original_pos
        self.xunshou_original_pos = xunshou_original_pos # 下面排八门会用到这个位置， 这个是地盘的宫位
        print('值符星',zhifu_star, xunshou_original_pos)
         # 获取时干宫位
        target_pos = self._get_shigan_position(shigan)
        print('时干：'+ shigan + ', 宫位:'+ str(target_pos))
        # 计算旋转步数
        rotation_steps = positions.index(target_pos) - positions.index(xunshou_original_pos)
        print('旋转步数' + str(rotation_steps))
        
        # 旋转九星和三奇六仪
        # stars = [self._get_star_by_pos(pos) for pos in positions]
        stars =  STAR_ORIGIN_ARRAY
        stars_rotated = deque(stars)
        stars_rotated.rotate(rotation_steps)
        # stars_rotated.remove(stars[-1])
        
        # qiyi = [self.palaces[pos]['earth'] for pos in positions]
        qiyi =  self.dipan_tiangan_array 
        qiyi_rotated = deque(qiyi)
        qiyi_rotated.rotate(rotation_steps)
        # qiyi_rotated.remove(qiyi[-1])

        # 写入天盘数据
        for i, pos in enumerate(positions[:-1]):
            self.palaces[pos]['sky'] = qiyi_rotated[i]
            self.palaces[pos]['star'] = stars_rotated[i]
        self.palaces[5]['sky'] = self.palaces[5]['earth']
        self.palaces[5]['star'] = '天禽'

    def arrange_doors(self):
        """八门排布"""
        positions = [1, 8, 3, 4, 9, 2, 7, 6, 5]
        # positions_yin = [9, 2, 7, 6, 1, 8, 3, 4, 5]
        # 根据时支计算直使门起始宫（需补充时支到宫位的映射）
        # shizhi_pos = self._get_shizhi_position(self.day_gz)  # 例如：子时对应坎1宫
         # 获取时干宫位
        # shizhi_pos = self._get_shigan_position(self.day_gz) 
        # xunshou_original_pos = self._get_xunshou_original_pos(self.xunshou_ganzhi)
        # 生成完整的六十甲子时辰列表
        sixty_jiazi = []
        for i in range(60):
            g = tiangan[i % 10]
            z = dizhi[i % 12]
            sixty_jiazi.append(g + z)
        xunshou_index = sixty_jiazi.index(self.xunshou_ganzhi)
        current_index = sixty_jiazi.index(self.hour_gz)
        xunshou_diff = current_index - xunshou_index
        print('====================================')
        print('距离旬首过去了：', xunshou_diff)
        # print('旬首干支在第：',self.xunshou_ganzhi,  XUNSHOU_POSITION[self.xunshou_ganzhi],'宫')
        print('旬首干支在第：',self.xunshou_ganzhi,  XUNSHOU_LIUYI[self.xunshou_ganzhi], self._find_earth_pos(XUNSHOU_LIUYI[self.xunshou_ganzhi]),'宫')
        print('====================================')
        # 值使门的原始宫位加上移动的次数
        xunshou_ganzhi_earth_pos = self._find_earth_pos(XUNSHOU_LIUYI[self.xunshou_ganzhi])
        if self.is_yang:
            self.zhishi_pos = 9 if  (xunshou_ganzhi_earth_pos  + xunshou_diff) % 9 == 0 else (xunshou_ganzhi_earth_pos  + xunshou_diff) % 9 
        else:
            self.zhishi_pos = 9 if  (xunshou_ganzhi_earth_pos  - xunshou_diff + 9) % 9 == 0 else (xunshou_ganzhi_earth_pos  - xunshou_diff + 9) % 9 
        print(self.zhishi_pos)
        # 这一条我不确定？如果值使门落5是不是寄2 
        self.zhishi_pos = 2 if self.zhishi_pos == 5 else self.zhishi_pos 
        print('值使门的新宫位：', self.zhishi_pos)

        xunshou_pos =  XUNSHOU_POSITION[self.xunshou_ganzhi]
        xunshou_orgin_index = positions.index(xunshou_pos)

        # self.xunshou_original_pos 这个其实是 值使门 原始宫位的 index?
        men_pos =  5 if self.xunshou_original_pos == 5 else positions.index(self.xunshou_original_pos)
        print(positions[self.xunshou_original_pos],men_pos)
        print('值使门',self.xunshou_original_pos, MEN_ORDER[men_pos])

        # 用新宫位的index 减去 旧宫位的indx
        men_pos_diff = positions.index(self.zhishi_pos) - positions.index(self.xunshou_original_pos)
        # men_pos_diff = men_pos_diff + xunshou_diff  if self.is_yang  else  men_pos_diff + xunshou_diff + 1

        self.zhishi_men = MEN_ORDER[men_pos]
        men_order = deque(MEN_ORDER)
        # 旋转的次数
        # rotation_steps = (dizhi.index(self.hour_gz[1]) + 1) % 8
        rotation_steps = men_pos_diff
        men_order.rotate(rotation_steps)
        # 排除中宫后的八宫顺序（按阳遁顺/阴遁逆）
        positions = positions[:-1]
        for pos, men in zip(positions, men_order):
            self.palaces[pos]['door'] = men
    
    def arrange_shen(self):
        """八神排布"""
        positions = [1, 8, 3, 4, 9, 2, 7, 6]
        shen_order = SHEN_ORDER_YANG if self.is_yang else SHEN_ORDER_YIN
        # 获取时干所在宫位，即为八神值符所在宫位
        shigan_pos = 2 if  self._find_earth_pos(self.hour_gz[0]) == 5  else self._find_earth_pos(self.hour_gz[0])
        shigan_pos_index = positions.index(shigan_pos)
        zhifu_pos_diff = shigan_pos_index
        shen_order_deque = deque(shen_order)
        shen_order_deque.rotate(zhifu_pos_diff)

        # zhifu_pos = self._get_zhifu_position()  # 需补充值符宫位获取逻辑
        # 按阴阳遁确定排列方向
        # positions = self._get_shen_positions(zhifu_pos)
        for pos, shen in zip(positions, shen_order_deque):
            self.palaces[pos]['shen'] = shen
    
    def find_horse_start():
        """找出马星所在"""
        print("马星所在")
    
    def find_kongwang():
        """找出空亡空位"""
        print("找出空亡空位")

    def find_liuyi_jixing():
        """找出六仪击刑"""
    
    def find_rumu():
        """找出天干入墓"""

    def find_menpo():
        """找出门迫"""
    
    
    
    def _get_zhifu_star(self) -> str:
        """根据时干支确定旬首，返回值符星（需先调用_calculate_xunshou）"""
        xunshou_ganzhi = self._calculate_xunshou()  # 例如"甲申"
        self.xunshou_ganzhi = xunshou_ganzhi
        # 这里通过旬首干支计算 旬首对应的地盘天干
        xunshou_liuyi_dipan_tiangan = XUNSHOU_LIUYI[xunshou_ganzhi]
        # 根据地盘天干 找到旬首对应的地盘宫位
        # 使用示例：
        pos = self._find_earth_pos(xunshou_liuyi_dipan_tiangan)
        # 处理中宫情况：当旬首导致值符居中时，天禽随天芮
        if pos == 5:
            return "天禽"
        return POS_STAR_MAP.get(pos, "天芮")

    def _find_earth_pos(self, target_gan: str) -> int:
        """找到地盘天干对应的宫位
        Args:
            target_gan: 目标天干，如 "戊"
        
        Returns:
            int: 对应的宫位号
        """
        for pos, data in self.palaces.items():
            if data['earth'] == target_gan:
                return pos
        return 5  # 如果找不到，返回中宫

    
    
    def _calculate_xunshou(self) -> str:
        """修正后的旬首计算（兼容天干地支0/1起始编号）"""
        # 假设天干地支序号从0开始（甲=0，子=0）
        gan, zhi = self.hour_gz[0], self.hour_gz[1]
        gan_idx = TIANGAN_ORDER[gan]  # "庚"→6
        zhi_idx = DIZHI_ORDER[zhi]    # "申"→8
        
        delta = (zhi_idx - gan_idx) % 12  # (8-6)=2 → 甲寅
        
        # Δ值与旬首映射[[3]]
        xunshou_map = {
            0: "甲子", 10: "甲戌", 8: "甲申", 
            6: "甲午", 4: "甲辰", 2: "甲寅"
        }
        print(self.hour_gz + '时旬首:'+xunshou_map[delta])
        return xunshou_map[delta]
    
    def _get_xunshou_original_pos(self, xunshou):
        """获取旬首的原始位置""" 
        xunshou_liuyi  = XUNSHOU_LIUYI[xunshou]
        # 遍历宫位字典，找到earth值等于时干的宫位号
        for palace_num, palace_data in self.palaces.items():
            if palace_data['earth'] == xunshou_liuyi:
                return palace_num
        # 如果找不到，返回中宫（5）
        return 5

    
    def _get_star_original_pos(self, star_name: str) -> int:
        """根据九星名称返回原始宫位（处理天禽寄宫）"""
        pos = STAR_ORIGIN_POS.get(star_name, 5)
        
        # 天禽星特殊处理：阳遁寄艮8，阴遁寄坤2
        if star_name == "天禽":
            return 8 if self.is_yang else 2
        return pos
    
    def _get_shigan_position(self, shigan: str) -> int:
        """根据时干在宫位字典中查找对应的宫位
        Args:
            shigan: 时干，如 '甲'
        Returns:
            int: 对应的宫位号
        """
        # 遍历宫位字典，找到earth值等于时干的宫位号
        for palace_num, palace_data in self.palaces.items():
            if palace_data['earth'] == shigan:
                return palace_num
        # 如果找不到，返回中宫（5）
        return 5
    
    def _get_star_by_pos(self, pos: int) -> str:
        """根据宫位获取原始星（考虑中宫寄位）"""
        star = POS_STAR_MAP.get(pos, "天禽")
        
        # 中宫天禽的寄宫处理
        if pos == 5:
            star = "天禽" 
        return star
    
    def _get_zhifu_position(self) -> int:
        """获取当前值符所在宫位（旬首时干对应宫位）"""
        # 需先计算旬首（此处需补充旬首计算逻辑）
        xunshou = self._calculate_xunshou()  
        
        # 遍历九宫寻找旬首时干的宫位
        for pos in self.palaces:
            if self.palaces[pos]['earth'] == xunshou:
                return pos
        return 5  # 默认中宫

    def _get_shen_positions(self, zhifu_pos: int) -> list:
        """生成八神排列的宫位顺序（严格分阴阳遁）"""
        # 根据阴阳遁选择基础路径
        if self.is_yang:
            base_order = [1, 8, 3, 4, 9, 2, 7, 6, 5]  # 阳遁顺飞九宫
        else:
            base_order = [9, 2, 7, 6, 1, 8, 3, 4, 5]  # 阴遁逆飞九宫
        
        # 找到值符起始位置索引
        try:
            start_idx = base_order.index(zhifu_pos)
        except ValueError:
            start_idx = 0  # 异常处理
        
        # 生成循环队列并旋转
        q = deque(base_order)
        q.rotate(-start_idx)
        
        # 排除中宫后的八宫
        return [pos for pos in list(q) if pos != 5][:8]

    def _get_shizhi_position(self, shizhi: str) -> int:
        """将时支转换为对应的九宫位置（地支三合局原理）"""
        return SHIZHI_POSITION.get(shizhi, 5)  # 默认返回中宫
    
    def _get_zhishi_men(self) -> str:
        """获取直使门（需结合旬首宫位和阴阳遁）"""
        # 1. 获取旬首对应的六仪
        xunshou_liuyi = self._calculate_xunshou()
        
        # 2. 查找六仪在地盘的宫位
        palace_pos = next((pos for pos in self.palaces 
                        if self.palaces[pos]['earth'] == xunshou_liuyi), 5)
        
        # 3. 处理中宫寄宫
        if palace_pos == 5:
            palace_pos = 8 if self.is_yang else 2
        
        # 4. 宫位到八门的映射（按阳遁宫位顺序）
        pos_to_men = {
            1: "休",   # 坎1宫
            8: "生",   # 艮8宫
            3: "伤",   # 震3宫
            4: "杜",   # 巽4宫
            9: "景",   # 离9宫
            2: "死",   # 坤2宫
            7: "惊",   # 兑7宫
            6: "开"    # 乾6宫
        }
        
        return pos_to_men[palace_pos]


    def run(self):
        self.calculate_ganzhi()
        self.calculate_futou()
        self.get_futou_jieqi()
        self.arrange_earth_plate()
        self.arrange_sky_plate()
        self.arrange_doors()
        self.arrange_shen()
        print(self.palaces)



# 使用示例：
# year = 2024
# summer_dt, winter_dt = get_solstices(year)
# print(f"{year}年夏至：{summer_dt}")
# print(f"{year}年冬至：{winter_dt}")

if __name__ == '__main__':
    # datetime_str = "2024-11-19 20:00:00" #f8
    # datetime_str = "2025-02-28 18:30:00" #t9
    datetime_str = "2024-06-07 16:30:00" #t9
    # datetime_str = "2025-03-13 4:00:00" #t9
    qimen = QiMenDunjiaPan(datetime_str)
    qimen.run()