"""
奇门遁甲排盘系统 - 优化版本

主要功能：
1. 天文历法计算（立春、节气、太阳黄经等）
2. 干支计算（年月日时干支）
3. 奇门遁甲排盘（置闰法）
4. 地盘、天盘、八门、八神排布

作者：redrockhorse
版本：2.0（优化版）
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Dict, List, Optional
from collections import deque
from skyfield.api import load
import logging

# ============================================================================
# 配置日志
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 常量定义区
# ============================================================================

class AstronomyConfig:
    """天文计算配置"""
    EPHEMERIS_FILE = 'de421.bsp'
    EPHEMERIS_DIR = './'
    LICHUN_DEGREE = 315  # 立春对应的太阳黄经度数
    BINARY_SEARCH_ITERATIONS = 20  # 二分法查找迭代次数


class GanzhiConstants:
    """干支常量"""
    # 十天干
    TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 十二地支
    DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 天干序号映射
    TIANGAN_ORDER = {gan: idx for idx, gan in enumerate(TIANGAN)}
    
    # 地支序号映射
    DIZHI_ORDER = {zhi: idx for idx, zhi in enumerate(DIZHI)}
    
    # 年干对应正月天干规则（五虎遁月）
    YEAR_GAN_TO_MONTH_START = {
        '甲': '丙', '己': '丙',
        '乙': '戊', '庚': '戊',
        '丙': '庚', '辛': '庚',
        '丁': '壬', '壬': '壬',
        '戊': '甲', '癸': '甲'
    }
    
    # 六十甲子基准日期（用于日干支计算）
    BASE_DATE = datetime(2025, 2, 24).date()  # 甲子日
    BASE_YEAR = 4  # 公元4年为甲子年


class JieqiConstants:
    """节气常量"""
    # 节气信息：(太阳黄经度数, 所在月份, 节气名称)
    JIEQI_INFO = [
        (315, 2, '立春'), (330, 2, '雨水'), (345, 3, '惊蛰'), (0, 3, '春分'),
        (15, 4, '清明'), (30, 4, '谷雨'), (45, 5, '立夏'), (60, 5, '小满'),
        (75, 6, '芒种'), (90, 6, '夏至'), (105, 7, '小暑'), (120, 7, '大暑'),
        (135, 8, '立秋'), (150, 8, '处暑'), (165, 9, '白露'), (180, 9, '秋分'),
        (195, 10, '寒露'), (210, 10, '霜降'), (225, 11, '立冬'), (240, 11, '小雪'),
        (255, 12, '大雪'), (270, 12, '冬至'), (285, 1, '小寒'), (300, 1, '大寒')
    ]
    
    # 节气名称到索引的映射
    JIEQI_ORDER = {name: idx for idx, (_, _, name) in enumerate(JIEQI_INFO)}


class QimenConstants:
    """奇门遁甲常量"""
    
    # 九宫方位映射（洛书数序）
    PALACE_MAP = {
        1: ("坎", "北"), 2: ("坤", "西南"), 3: ("震", "东"),
        4: ("巽", "东南"), 5: ("中", "中央"), 6: ("乾", "西北"),
        7: ("兑", "西"), 8: ("艮", "东北"), 9: ("离", "南")
    }
    
    # 宫位对应的原始星
    POS_STAR_MAP = {
        1: "天蓬", 2: "天芮", 3: "天冲", 4: "天辅",
        5: "天禽", 6: "天心", 7: "天柱", 8: "天任", 9: "天英"
    }
    
    # 九星原始宫位映射
    STAR_ORIGIN_POS = {
        "天蓬": 1, "天芮": 2, "天冲": 3, "天辅": 4,
        "天禽": 5, "天心": 6, "天柱": 7, "天任": 8, "天英": 9
    }
    
    # 九星顺序数组（用于旋转排布）
    STAR_ORIGIN_ARRAY = ["天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"]
    
    # 三奇六仪顺序
    QIYI_ORDER = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    
    # 六甲旬首对应的宫位
    XUNSHOU_POSITION = {
        "甲子": 1, "甲戌": 2, "甲申": 8,
        "甲午": 9, "甲辰": 4, "甲寅": 3
    }
    
    # 旬首六仪映射
    XUNSHOU_LIUYI = {
        "甲子": "戊", "甲戌": "己", "甲申": "庚",
        "甲午": "辛", "甲辰": "壬", "甲寅": "癸"
    }
    
    # 八门顺序
    MEN_ORDER = ["休", "生", "伤", "杜", "景", "死", "惊", "开"]
    
    # 八神顺序（阳遁）
    SHEN_ORDER_YANG = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
    
    # 八神顺序（阴遁）
    SHEN_ORDER_YIN = ["值符", "九天", "九地", "玄武", "白虎", "六合", "太阴", "腾蛇"]
    
    # 时支与宫位映射
    SHIZHI_POSITION = {
        "子": 1, "丑": 8, "寅": 8, "卯": 3, "辰": 4, "巳": 4,
        "午": 9, "未": 2, "申": 2, "酉": 7, "戌": 6, "亥": 6
    }
    
    # 阳遁局数表
    YANG_JU_MAPPING = {
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
    YIN_JU_MAPPING = {
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
    
    # 九宫遍历顺序（不含中宫）
    PALACE_TRAVERSE_ORDER = [1, 8, 3, 4, 9, 2, 7, 6]
    
    # 置闰符头对应关系
    ZHIRUN_FUTOU = {'甲子', '甲午', '己卯', '己酉'}
    
    # 十天干墓库对应地支及奇门宫位
    # 天干入墓：天盘干落在其墓库对应宫位即为入墓
    TIANGAN_MUKU = {
        '甲': {'地支': '未', '宫位': 2},   # 坤二宫
        '乙': {'地支': '戌', '宫位': 6},   # 乾六宫
        '丙': {'地支': '戌', '宫位': 6},   # 乾六宫
        '丁': {'地支': '丑', '宫位': 8},   # 艮八宫
        '戊': {'地支': '戌', '宫位': 6},   # 乾六宫
        '己': {'地支': '丑', '宫位': 8},   # 艮八宫
        '庚': {'地支': '丑', '宫位': 8},   # 艮八宫
        '辛': {'地支': '辰', '宫位': 4},   # 巽四宫
        '壬': {'地支': '辰', '宫位': 4},   # 巽四宫
        '癸': {'地支': '未', '宫位': 2},   # 坤二宫
    }
    
    # 六仪击刑的宫位对应
    # 六仪击刑：天盘六仪落在其击刑宫位即为击刑
    LIUYI_JIXING = {
        '戊': {'旬首': '甲子戊', '击刑宫位': 3, '刑理': '子刑卯', '地支关系': '子（戊）加震（卯）'},   # 震三宫
        '己': {'旬首': '甲戌己', '击刑宫位': 2, '刑理': '戌刑未', '地支关系': '戌（己）加坤（未）'},   # 坤二宫
        '庚': {'旬首': '甲申庚', '击刑宫位': 8, '刑理': '申刑寅', '地支关系': '申（庚）加艮（寅）'},   # 艮八宫
        '辛': {'旬首': '甲午辛', '击刑宫位': 9, '刑理': '午午自刑', '地支关系': '午（辛）加离（午）'},   # 离九宫
        '壬': {'旬首': '甲辰壬', '击刑宫位': 4, '刑理': '辰辰自刑', '地支关系': '辰（壬）加巽（辰）'},   # 巽四宫
        '癸': {'旬首': '甲寅癸', '击刑宫位': 4, '刑理': '寅刑巳', '地支关系': '寅（癸）加巽（巳）'},   # 巽四宫
    }
    
    # 马星：根据时支确定马星地支及所落宫位
    # 时支 -> (马星地支, 宫位)
    MAXING = {
        '申': ('寅', 8), '子': ('寅', 8), '辰': ('寅', 8),   # 艮八宫
        '亥': ('巳', 4), '卯': ('巳', 4), '未': ('巳', 4),   # 巽四宫
        '寅': ('申', 2), '午': ('申', 2), '戌': ('申', 2),   # 坤二宫
        '巳': ('亥', 6), '酉': ('亥', 6), '丑': ('亥', 6),   # 乾六宫
    }
    
    # 门迫：门与宫位五行相克
    # (门, 宫位) -> 门迫描述
    MEN_PO = {
        ('伤', 2): '木门落土宫', ('伤', 8): '木门落土宫',
        ('杜', 2): '木门落土宫', ('杜', 8): '木门落土宫',
        ('惊', 3): '金门落木宫', ('惊', 4): '金门落木宫',
        ('开', 3): '金门落木宫', ('开', 4): '金门落木宫',
        ('景', 6): '火门落金宫', ('景', 7): '火门落金宫',
        ('休', 9): '水门落火宫',
        ('生', 1): '土门落水宫', ('死', 1): '土门落水宫',
    }


# ============================================================================
# 天文计算模块
# ============================================================================

# 初始化天文数据
load.directory = AstronomyConfig.EPHEMERIS_DIR
ts = load.timescale()
eph = load(AstronomyConfig.EPHEMERIS_FILE)


class AstronomyCalculator:
    """天文计算类"""
    
    @staticmethod
    def get_sun_longitude(t) -> float:
        """
        获取太阳黄经
        
        Args:
            t: skyfield时间对象
            
        Returns:
            float: 太阳黄经度数
        """
        astro = eph['earth'].at(t).observe(eph['sun'])
        lat, lon, _ = astro.ecliptic_latlon()
        return lon.degrees
    
    @staticmethod
    def find_lichun(year: int) -> datetime:
        """
        计算指定年份的立春准确时间
        
        Args:
            year: 年份
            
        Returns:
            datetime: 立春时间（UTC）
        """
        start = ts.utc(year, 2, 1)
        end = ts.utc(year, 2, 15)
        
        t0, t1 = start, end
        for _ in range(AstronomyConfig.BINARY_SEARCH_ITERATIONS):
            tm = ts.tt_jd((t0.tt + t1.tt) / 2)
            if AstronomyCalculator.get_sun_longitude(tm) >= AstronomyConfig.LICHUN_DEGREE:
                t1 = tm
            else:
                t0 = tm
        
        return t1.utc_datetime()
    
    @staticmethod
    def get_jieqi_time(year: int, target_degree: int) -> datetime:
        """
        计算指定年份特定黄经度数对应的节气时间
        
        Args:
            year: 年份
            target_degree: 目标黄经度数
            
        Returns:
            datetime: 节气时间（UTC）
        """
        # 根据黄经度数确定对应的月份
        month = 1
        for degree, m, _ in JieqiConstants.JIEQI_INFO:
            if degree == target_degree:
                month = m
                break
        
        # 设置搜索范围
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
        
        start = ts.utc(start_year, start_month, 1)
        end = ts.utc(end_year, end_month, 1)
        
        # 二分法查找
        t0, t1 = start, end
        for _ in range(AstronomyConfig.BINARY_SEARCH_ITERATIONS):
            tm = ts.tt_jd((t0.tt + t1.tt) / 2)
            if AstronomyCalculator.get_sun_longitude(tm) % 360 >= target_degree % 360:
                t1 = tm
            else:
                t0 = tm
        
        return t1.utc_datetime()
    
    @staticmethod
    def get_solstices(year: int) -> Tuple[datetime, datetime]:
        """
        获取指定年份的夏至和冬至时间
        
        Args:
            year: 年份
            
        Returns:
            tuple: (夏至时间, 冬至时间)
        """
        summer_solstice = None
        winter_solstice = None
        
        for degree, _, name in JieqiConstants.JIEQI_INFO:
            if name == '夏至':
                summer_solstice = AstronomyCalculator.get_jieqi_time(year, degree)
            elif name == '冬至':
                winter_solstice = AstronomyCalculator.get_jieqi_time(year, degree)
            
            if summer_solstice and winter_solstice:
                break
        
        return summer_solstice, winter_solstice


# ============================================================================
# 干支计算模块
# ============================================================================

class GanzhiCalculator:
    """干支计算类"""
    
    @staticmethod
    def get_year_ganzhi(input_datetime: datetime) -> str:
        """
        获取年干支（以立春为界）
        
        Args:
            input_datetime: 输入时间
            
        Returns:
            str: 年干支，如"甲子"
        """
        year = input_datetime.year
        lichun_current = AstronomyCalculator.find_lichun(year)
        
        # 判断输入日期是否在当前年立春之后
        calc_year = year if input_datetime >= lichun_current else year - 1
        
        # 计算干支索引
        idx = (calc_year - GanzhiConstants.BASE_YEAR) % 60
        gan_idx = idx % 10
        zhi_idx = idx % 12
        
        return GanzhiConstants.TIANGAN[gan_idx] + GanzhiConstants.DIZHI[zhi_idx]
    
    @staticmethod
    def find_jieqi(input_dt: datetime, forward: bool = True) -> Optional[Tuple[datetime, str]]:
        """
        找到输入时间对应的节气
        
        Args:
            input_dt: 输入时间
            forward: True表示向前找（找小于等于输入时间的最近节气），
                    False表示向后找（找大于输入时间的最近节气）
                    
        Returns:
            tuple: (节气时间, 节气名称) 或 None
        """
        # 生成前后两年所有节气时间
        jieqi_events = []
        for y in [input_dt.year - 1, input_dt.year, input_dt.year + 1]:
            for degree, _, name in JieqiConstants.JIEQI_INFO:
                jt = AstronomyCalculator.get_jieqi_time(y, degree)
                jieqi_events.append((jt, name))
        
        # 按时间排序
        jieqi_events.sort(key=lambda x: x[0])
        
        if forward:
            # 向前找：找到最后一个小于等于输入时间的节气
            for i in range(len(jieqi_events) - 1, -1, -1):
                if jieqi_events[i][0] <= input_dt:
                    return jieqi_events[i]
        else:
            # 向后找：找到第一个大于输入时间的节气
            for event in jieqi_events:
                if event[0] > input_dt:
                    return event
        
        return None
    
    @staticmethod
    def get_month_ganzhi(input_dt: datetime) -> str:
        """
        获取月干支（以节气为界）
        
        Args:
            input_dt: 输入时间
            
        Returns:
            str: 月干支，如"丙寅"
        """
        # 获取年干
        year_gan = GanzhiCalculator.get_year_ganzhi(input_dt)[0]
        
        # 获取对应节气及索引
        jieqi_result = GanzhiCalculator.find_jieqi(input_dt)
        if not jieqi_result:
            raise ValueError("无法确定节气")
        
        _, jieqi_name = jieqi_result
        idx = JieqiConstants.JIEQI_ORDER[jieqi_name]
        month_num = idx // 2  # 0-11对应正月到腊月
        
        # 根据年干确定正月天干（五虎遁月）
        start_gan = GanzhiConstants.YEAR_GAN_TO_MONTH_START[year_gan]
        gan_idx = (GanzhiConstants.TIANGAN.index(start_gan) + month_num) % 10
        zhi_idx = (month_num + 2) % 12  # 正月建寅
        
        return GanzhiConstants.TIANGAN[gan_idx] + GanzhiConstants.DIZHI[zhi_idx]
    
    @staticmethod
    def get_day_hour_ganzhi(input_str: str) -> Tuple[str, str]:
        """
        获取日时干支
        
        Args:
            input_str: 时间字符串，格式："YYYY-MM-DD HH:MM:SS"
            
        Returns:
            tuple: (日干支, 时干支)
        """
        dt = datetime.strptime(input_str, "%Y-%m-%d %H:%M:%S")
        
        # ===== 日干支计算 =====
        # 23点后算下一天
        adjusted_date = dt.date() + timedelta(days=1) if dt.hour >= 23 else dt.date()
        
        # 计算与基准日的天数差
        days_diff = (adjusted_date - GanzhiConstants.BASE_DATE).days
        ganzhi_index = days_diff % 60
        
        ri_gan = GanzhiConstants.TIANGAN[ganzhi_index % 10]
        ri_zhi = GanzhiConstants.DIZHI[ganzhi_index % 12]
        ri_gz = f"{ri_gan}{ri_zhi}"
        
        # ===== 时干支计算 =====
        h = dt.hour
        if h == 23:
            h = 24  # 便于计算时辰索引
        
        zhi_index = (h + 1) // 2 % 12
        shi_zhi = GanzhiConstants.DIZHI[zhi_index]
        
        # 根据日干确定时干起始（五鼠遁日）
        ri_gan_idx = GanzhiConstants.TIANGAN.index(ri_gan)
        if ri_gan_idx in [0, 5]:      # 甲/己日
            start = 0
        elif ri_gan_idx in [1, 6]:    # 乙/庚日
            start = 2
        elif ri_gan_idx in [2, 7]:    # 丙/辛日
            start = 4
        elif ri_gan_idx in [3, 8]:    # 丁/壬日
            start = 6
        else:                          # 戊/癸日
            start = 8
        
        shi_gan = GanzhiConstants.TIANGAN[(start + zhi_index) % 10]
        shi_gz = f"{shi_gan}{shi_zhi}"
        
        return ri_gz, shi_gz
    
    @staticmethod
    def calculate_xunshou(hour_gz: str) -> str:
        """
        计算旬首
        
        Args:
            hour_gz: 时干支
            
        Returns:
            str: 旬首干支
        """
        gan, zhi = hour_gz[0], hour_gz[1]
        gan_idx = GanzhiConstants.TIANGAN_ORDER[gan]
        zhi_idx = GanzhiConstants.DIZHI_ORDER[zhi]
        
        delta = (zhi_idx - gan_idx) % 12
        
        xunshou_map = {
            0: "甲子", 10: "甲戌", 8: "甲申",
            6: "甲午", 4: "甲辰", 2: "甲寅"
        }
        
        return xunshou_map[delta]


# ============================================================================
# 符头计算模块
# ============================================================================

class FutouCalculator:
    """符头计算类"""
    
    @staticmethod
    def get_futou_details(day_ganzhi: str, method: str = '置闰') -> Dict:
        """
        根据日干支和定局方法计算符头、三元及距离天数
        
        Args:
            day_ganzhi: 日干支，如"甲子"
            method: 定局方法，"置闰" 或 "拆补"
            
        Returns:
            dict: 包含符头、三元、距离天数等信息
        """
        # 生成干支表（60甲子）
        ganzhi = [
            f"{GanzhiConstants.TIANGAN[i % 10]}{GanzhiConstants.DIZHI[i % 12]}"
            for i in range(60)
        ]
        ganzhi_map = {gz: i for i, gz in enumerate(ganzhi)}
        
        # 校验输入合法性
        if day_ganzhi not in ganzhi_map:
            raise ValueError(f"无效的日干支: {day_ganzhi}")
        
        current_idx = ganzhi_map[day_ganzhi]
        
        # 逆向查找符头
        futou, days_ago = None, 0
        zhi_type = ''
        step_day = 0
        
        for steps in range(60):
            check_idx = (current_idx - steps) % 60
            check_gz = ganzhi[check_idx]
            
            # 置闰法：仅匹配甲子、甲午、己卯、己酉
            if method == '置闰' and check_gz in QimenConstants.ZHIRUN_FUTOU:
                futou = check_gz
                days_ago = steps
                step_day = days_ago % 5 + 1
                
                # 确定三元
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
            if method == '拆补' and check_gz[0] in {'甲', '己'}:
                futou = check_gz
                days_ago = steps
                # 确定三元
                zhi_type_map = {
                    '子': '上元', '午': '上元', '卯': '上元', '酉': '上元',
                    '寅': '中元', '申': '中元', '巳': '中元', '亥': '中元',
                    '辰': '下元', '戌': '下元', '丑': '下元', '未': '下元'
                }
                zhi_type = zhi_type_map[futou[1]]
                break
        
        return {
            '符头': futou,
            '上中下元': zhi_type,
            '符头差日': days_ago,
            '某元第几天': step_day
        }


# ============================================================================
# 奇门遁甲排盘主类
# ============================================================================

class QiMenDunjiaPan:
    """奇门遁甲排盘主类"""
    
    def __init__(self, input_datetime_str: str):
        """
        初始化排盘
        
        Args:
            input_datetime_str: 输入时间字符串，格式："YYYY-MM-DD HH:MM:SS"
        """
        self.input_dt = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        self.input_utc = self.input_dt.replace(tzinfo=timezone.utc)
        
        # 初始化九宫数据结构
        self.palaces = {
            num: {
                'earth': None,   # 地盘天干
                'sky': None,     # 天盘天干
                'door': None,    # 八门
                'star': None,    # 九星
                'shen': None     # 八神
            }
            for num in QimenConstants.PALACE_MAP
        }
        
        # 干支信息
        self.year_gz = None
        self.month_gz = None
        self.day_gz = None
        self.hour_gz = None
        
        # 符头相关
        self.futou_date = None
        self.period = None
        self.curr_jieqi = None
        self.curr_yuan = None
        
        # 局数和阴阳遁
        self.ju_number = None
        self.is_yang = None
        
        # 旬首相关
        self.xunshou_ganzhi = None
        self.xunshou_original_pos = None
        
        # 值使门位置
        self.zhishi_pos = None
        self.zhishi_men = None
        
        # 地盘天干数组（用于天盘旋转）
        self.dipan_tiangan_array = []
    
    # ========================================================================
    # 主流程方法
    # ========================================================================
    
    def calculate_ganzhi(self):
        """计算干支"""
        self.year_gz = GanzhiCalculator.get_year_ganzhi(self.input_utc)
        self.month_gz = GanzhiCalculator.get_month_ganzhi(self.input_utc)
        self.day_gz, self.hour_gz = GanzhiCalculator.get_day_hour_ganzhi(
            self.input_dt.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        logger.info(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")
    
    def calculate_futou(self):
        """计算符头日期"""
        futou_info = FutouCalculator.get_futou_details(self.day_gz)
        futou_days_diff = futou_info['符头差日']
        
        self.futou_date = datetime.combine(
            self.input_dt.date() - timedelta(days=futou_days_diff),
            self.input_dt.time(),
            tzinfo=self.input_dt.tzinfo if self.input_dt.tzinfo else None
        )
        
        logger.info(f"符头日期: {self.futou_date}")
    
    def get_futou_jieqi(self):
        """获取符头所在的节气，确定阴阳遁和局数"""
        # 获取夏至和冬至时间
        summer_solstice, winter_solstice = AstronomyCalculator.get_solstices(
            self.futou_date.year
        )
        
        # 确保时区一致性
        futou_date_naive = self.futou_date.replace(tzinfo=None)
        summer_solstice_naive = summer_solstice.replace(tzinfo=None)
        winter_solstice_naive = winter_solstice.replace(tzinfo=None)
        
        # 判断符头日期在夏至和冬至的相对位置
        if futou_date_naive < summer_solstice_naive:
            # 如果在夏至前，使用前一年的冬至
            _, prev_winter = AstronomyCalculator.get_solstices(self.futou_date.year - 1)
            prev_winter_naive = prev_winter.replace(tzinfo=None)
            period = "夏至前"
            self.period = '冬至'
            effective_jieqi = prev_winter_naive
        elif futou_date_naive < winter_solstice_naive:
            period = "夏至后冬至前"
            self.period = '夏至'
            effective_jieqi = summer_solstice_naive
        else:
            period = "冬至后"
            self.period = '冬至'
            effective_jieqi = winter_solstice_naive
        
        logger.info(f"符头日期 {self.futou_date} 在{period}")
        
        # 计算参考节气日期的日干支
        effective_day_ganzhi, _ = GanzhiCalculator.get_day_hour_ganzhi(
            effective_jieqi.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 获取符头信息
        futou_info = FutouCalculator.get_futou_details(effective_day_ganzhi)
        futou_days_diff = futou_info['符头差日']
        
        # 计算符头日期
        effective_futou_date = datetime.combine(
            effective_jieqi.date() - timedelta(days=futou_days_diff),
            effective_jieqi.time(),
            tzinfo=effective_jieqi.tzinfo
        )
        
        logger.info(f"参考节气: {self.period}, 时间: {effective_jieqi}")
        logger.info(f"参考符头日期: {effective_futou_date}")
        
        # 判断是否需要置闰
        if futou_info['符头差日'] > 9:
            logger.info("触发置闰")
            if self.period == '冬至':
                self.period = '大雪'
            elif self.period == '夏至':
                self.period = '芒种'
        
        # 计算输入日期与符头日期的差值（只比较日期部分，使用00:00:00）
        input_date_00 = self.input_dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        futou_date_00 = effective_futou_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        input_futou_diff = (input_date_00 - futou_date_00).days
        logger.info(f"输入日期（原始）: {self.input_dt.replace(tzinfo=None)}")
        logger.info(f"输入日期（计算用）: {input_date_00}")
        logger.info(f"符头日期（原始）: {effective_futou_date.replace(tzinfo=None)}")
        logger.info(f"符头日期（计算用）: {futou_date_00}")
        
        # 计算当前节气和三元
        quotient, remainder = divmod(input_futou_diff, 15)
        logger.info(f"输入日期与符头相差 {input_futou_diff} 天")
        logger.info(f"除以15: 整数部分={quotient}, 余数部分={remainder}")
        
        # 在节气列表中找到起始节气的索引
        start_index = None
        for i, (_, _, name) in enumerate(JieqiConstants.JIEQI_INFO):
            if name == self.period:
                start_index = i
                break
        
        if start_index is not None:
            # 计算目标节气的索引（考虑循环）
            target_index = (start_index + quotient) % len(JieqiConstants.JIEQI_INFO)
            _, _, target_name = JieqiConstants.JIEQI_INFO[target_index]
            
            self.curr_jieqi = target_name
            
            # 确定三元
            quotient_yuan, _ = divmod(remainder, 5)
            yuan_map = {0: '上元', 1: '中元', 2: '下元'}
            self.curr_yuan = yuan_map.get(quotient_yuan, '上元')
            
            logger.info(f"当前节气: {self.curr_jieqi}, 三元: {self.curr_yuan}")
            
            # 确定阴阳遁和局数
            if self.curr_jieqi in QimenConstants.YANG_JU_MAPPING:
                self.is_yang = True
                self.ju_number = QimenConstants.YANG_JU_MAPPING[self.curr_jieqi][self.curr_yuan]
                logger.info(f"阳遁 {self.ju_number} 局")
            elif self.curr_jieqi in QimenConstants.YIN_JU_MAPPING:
                self.is_yang = False
                self.ju_number = QimenConstants.YIN_JU_MAPPING[self.curr_jieqi][self.curr_yuan]
                logger.info(f"阴遁 {self.ju_number} 局")
            else:
                raise ValueError(f"未找到对应的局数映射：节气={self.curr_jieqi}，元={self.curr_yuan}")
        else:
            raise ValueError(f"未找到起始节气：{self.period}")
    
    def arrange_earth_plate(self):
        """排布地盘（三奇六仪）"""
        # 确定戊的起始宫位
        start_pos = self.ju_number
        
        # 生成九宫遍历路径
        positions = []
        current = start_pos
        for _ in range(9):
            positions.append(current)
            # 阳遁顺行，阴遁逆行
            current = current % 9 + 1 if self.is_yang else (current - 2) % 9 + 1
        
        # 填充天干（六仪→三奇循环）
        for i, pos in enumerate(positions):
            if i < 6:
                self.palaces[pos]['earth'] = QimenConstants.QIYI_ORDER[i]
            else:
                self.palaces[pos]['earth'] = QimenConstants.QIYI_ORDER[6 + (i - 6) % 3]
        
        # 保存地盘天干数组（用于天盘旋转）
        self.dipan_tiangan_array = [
            self.palaces[pos]['earth'] 
            for pos in QimenConstants.PALACE_TRAVERSE_ORDER
        ]
        
        logger.info("地盘排布完成")
    
    def arrange_sky_plate(self):
        """排布天盘和九星"""
        shigan = self.hour_gz[0]
        positions = QimenConstants.PALACE_TRAVERSE_ORDER + [5]
        
        # 计算旬首
        self.xunshou_ganzhi = GanzhiCalculator.calculate_xunshou(self.hour_gz)
        
        # 获取旬首对应的地盘宫位
        xunshou_liuyi = QimenConstants.XUNSHOU_LIUYI[self.xunshou_ganzhi]
        xunshou_original_pos = self._find_earth_pos(xunshou_liuyi)
        
        # 中宫寄2宫（坤宫）
        xunshou_original_pos = 2 if xunshou_original_pos == 5 else xunshou_original_pos
        self.xunshou_original_pos = xunshou_original_pos
        
        logger.info(f"旬首: {self.xunshou_ganzhi}, 原始宫位: {xunshou_original_pos}")
        
        # 获取时干宫位
        target_pos = self._get_shigan_position(shigan)
        # 如果是中宫5，寄到坤宫2
        target_pos = 2 if target_pos == 5 else target_pos
        logger.info(f"时干: {shigan}, 宫位: {target_pos}")
        
        # 计算旋转步数
        rotation_steps = (
            positions.index(target_pos) - 
            positions.index(xunshou_original_pos)
        )
        logger.info(f"旋转步数: {rotation_steps}")
        
        # 旋转九星和三奇六仪
        stars_rotated = deque(QimenConstants.STAR_ORIGIN_ARRAY)
        stars_rotated.rotate(rotation_steps)
        
        qiyi_rotated = deque(self.dipan_tiangan_array)
        qiyi_rotated.rotate(rotation_steps)
        
        # 写入天盘数据（不含中宫）
        for i, pos in enumerate(QimenConstants.PALACE_TRAVERSE_ORDER):
            self.palaces[pos]['sky'] = qiyi_rotated[i]
            self.palaces[pos]['star'] = stars_rotated[i]
        
        # 中宫数据
        self.palaces[5]['sky'] = self.palaces[5]['earth']
        self.palaces[5]['star'] = '天禽'
        
        # 天芮星所在宫的天盘干需加5宫天盘干（天禽随天芮）
        for pos in QimenConstants.PALACE_TRAVERSE_ORDER:
            if self.palaces[pos]['star'] == '天芮':
                sky_self = self.palaces[pos]['sky']
                sky_5 = self.palaces[5]['sky']
                self.palaces[pos]['sky'] = f"{sky_self}/{sky_5}" if sky_5 != sky_self else sky_self
                break
        
        logger.info("天盘和九星排布完成")
    
    def arrange_doors(self):
        """排布八门"""
        positions = QimenConstants.PALACE_TRAVERSE_ORDER + [5]
        
        # 生成完整的六十甲子列表
        sixty_jiazi = [
            f"{GanzhiConstants.TIANGAN[i % 10]}{GanzhiConstants.DIZHI[i % 12]}"
            for i in range(60)
        ]
        
        xunshou_index = sixty_jiazi.index(self.xunshou_ganzhi)
        current_index = sixty_jiazi.index(self.hour_gz)
        xunshou_diff = current_index - xunshou_index
        
        logger.info(f"距离旬首: {xunshou_diff} 个时辰")
        
        # 计算值使门的新宫位
        xunshou_ganzhi_earth_pos = self._find_earth_pos(
            QimenConstants.XUNSHOU_LIUYI[self.xunshou_ganzhi]
        )
        
        if self.is_yang:
            self.zhishi_pos = (xunshou_ganzhi_earth_pos + xunshou_diff) % 9
        else:
            self.zhishi_pos = (xunshou_ganzhi_earth_pos - xunshou_diff + 9) % 9
        
        self.zhishi_pos = 9 if self.zhishi_pos == 0 else self.zhishi_pos
        self.zhishi_pos = 2 if self.zhishi_pos == 5 else self.zhishi_pos
        
        logger.info(f"值使门位置: {self.zhishi_pos}")
        
        # 确定值使门名称
        men_pos = positions.index(self.xunshou_original_pos)
        self.zhishi_men = QimenConstants.MEN_ORDER[men_pos]
        logger.info(f"值使门: {self.zhishi_men}")
        
        # 计算旋转步数
        men_pos_diff = (
            positions.index(self.zhishi_pos) - 
            positions.index(self.xunshou_original_pos)
        )
        
        # 旋转八门
        men_order = deque(QimenConstants.MEN_ORDER)
        men_order.rotate(men_pos_diff)
        
        # 填充八门（不含中宫）
        for pos, men in zip(QimenConstants.PALACE_TRAVERSE_ORDER, men_order):
            self.palaces[pos]['door'] = men
        
        logger.info("八门排布完成")
    
    def arrange_shen(self):
        """排布八神"""
        positions = QimenConstants.PALACE_TRAVERSE_ORDER
        
        # 根据阴阳遁选择八神顺序
        shen_order = (
            QimenConstants.SHEN_ORDER_YANG if self.is_yang 
            else QimenConstants.SHEN_ORDER_YIN
        )
        
        # 获取时干所在宫位（八神值符所在宫位）
        shigan_pos = self._find_earth_pos(self.hour_gz[0])
        shigan_pos = 2 if shigan_pos == 5 else shigan_pos
        
        # 计算旋转步数
        shigan_pos_index = positions.index(shigan_pos)
        
        # 旋转八神
        shen_order_deque = deque(shen_order)
        shen_order_deque.rotate(shigan_pos_index)
        
        # 填充八神
        for pos, shen in zip(positions, shen_order_deque):
            self.palaces[pos]['shen'] = shen
        
        logger.info("八神排布完成")
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def _get_earth_display(self, pos: int) -> str:
        """
        获取地盘干的显示值。2宫需显示寄宫关系（中宫寄坤宫）：
        - 2宫：2宫地盘干 + 5宫地盘干
        """
        raw = self.palaces[pos]['earth']
        if pos == 2:
            other = self.palaces[5]['earth']
            return f"{raw}/{other}" if other and other != raw else raw
        return raw
    
    def _find_earth_pos(self, target_gan: str) -> int:
        """
        找到地盘天干对应的宫位
        
        Args:
            target_gan: 目标天干
            
        Returns:
            int: 对应的宫位号
        """
        for pos, data in self.palaces.items():
            if data['earth'] == target_gan:
                return pos
        return 5  # 默认返回中宫
    
    def _get_shigan_position(self, shigan: str) -> int:
        """
        根据时干在宫位字典中查找对应的宫位
        
        Args:
            shigan: 时干
            
        Returns:
            int: 对应的宫位号
        """
        for palace_num, palace_data in self.palaces.items():
            if palace_data['earth'] == shigan:
                return palace_num
        return 5  # 默认返回中宫
    
    def get_rumu_palaces(self) -> List[Dict]:
        """
        计算哪些宫位的天盘干入墓
        
        天盘干入墓：天盘干落在其墓库对应宫位即为入墓
        例如：甲墓在未(坤二宫)，若天盘甲在2宫则入墓
        
        Returns:
            list: 入墓信息列表，每项为 {'宫位': int, '天盘干': str, '墓库地支': str, '宫名': str}
        """
        rumu_list = []
        for pos, data in self.palaces.items():
            sky_raw = data['sky']
            if not sky_raw:
                continue
            # 天芮所在宫可能为 "戊/己" 格式，需分开判断
            for gan in sky_raw.split('/'):
                gan = gan.strip()
                if gan and gan in QimenConstants.TIANGAN_MUKU:
                    muku_info = QimenConstants.TIANGAN_MUKU[gan]
                    if muku_info['宫位'] == pos:
                        palace_name, _ = QimenConstants.PALACE_MAP[pos]
                        rumu_list.append({
                            '宫位': pos,
                            '天盘干': gan,
                            '墓库地支': muku_info['地支'],
                            '宫名': palace_name
                        })
        return rumu_list
    
    def get_liuyi_jixing(self) -> List[Dict]:
        """
        计算哪些宫位的天盘六仪击刑
        
        六仪击刑：天盘六仪（戊己庚辛壬癸）落在其击刑宫位即为击刑
        例如：戊（甲子戊）击刑宫位在震三宫，若天盘戊在3宫则击刑
        
        Returns:
            list: 击刑信息列表，每项为 {'宫位': int, '六仪': str, '旬首': str, '刑理': str, '地支关系': str, '宫名': str}
        """
        jixing_list = []
        for pos, data in self.palaces.items():
            sky_raw = data['sky']
            if not sky_raw:
                continue
            for gan in sky_raw.split('/'):
                gan = gan.strip()
                if gan and gan in QimenConstants.LIUYI_JIXING:
                    jx_info = QimenConstants.LIUYI_JIXING[gan]
                    if jx_info['击刑宫位'] == pos:
                        palace_name, _ = QimenConstants.PALACE_MAP[pos]
                        jixing_list.append({
                            '宫位': pos,
                            '六仪': gan,
                            '旬首': jx_info['旬首'],
                            '刑理': jx_info['刑理'],
                            '地支关系': jx_info['地支关系'],
                            '宫名': palace_name
                        })
        return jixing_list
    
    def get_men_po(self) -> List[Dict]:
        """
        计算哪些宫位门迫
        
        门迫：门与宫位五行相克
        伤门、杜门（木）落坤二宫、艮八宫（土）→ 门迫
        惊门、开门（金）落震三宫、巽四宫（木）→ 门迫
        景门（火）落乾六宫、兑七宫（金）→ 门迫
        休门（水）落离九宫（火）→ 门迫
        生门、死门（土）落坎一宫（水）→ 门迫
        
        Returns:
            list: 门迫信息列表，每项为 {'宫位': int, '门': str, '宫名': str, '描述': str}
        """
        men_po_list = []
        for pos, data in self.palaces.items():
            men = data.get('door')
            if not men:
                continue
            key = (men, pos)
            if key in QimenConstants.MEN_PO:
                palace_name, _ = QimenConstants.PALACE_MAP[pos]
                men_po_list.append({
                    '宫位': pos,
                    '门': men,
                    '宫名': palace_name,
                    '描述': QimenConstants.MEN_PO[key]
                })
        return men_po_list
    
    def get_maxing_palace(self) -> Optional[Dict]:
        """
        计算马星所落宫位
        
        根据时支确定马星地支及奇门宫位：
        申、子、辰 → 寅 → 艮八宫
        亥、卯、未 → 巳 → 巽四宫
        寅、午、戌 → 申 → 坤二宫
        巳、酉、丑 → 亥 → 乾六宫
        
        Returns:
            dict: {'时支': str, '马星地支': str, '宫位': int, '宫名': str} 或 None
        """
        shi_zhi = self.hour_gz[1]  # 时支
        if shi_zhi not in QimenConstants.MAXING:
            return None
        maxing_zhi, pos = QimenConstants.MAXING[shi_zhi]
        palace_name, _ = QimenConstants.PALACE_MAP[pos]
        return {
            '时支': shi_zhi,
            '马星地支': maxing_zhi,
            '宫位': pos,
            '宫名': palace_name
        }
    
    def print_result(self):
        """打印排盘结果"""
        print("\n" + "=" * 60)
        print("奇门遁甲排盘结果")
        print("=" * 60)
        print(f"输入时间: {self.input_dt}")
        print(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")
        print(f"节气: {self.curr_jieqi} {self.curr_yuan}")
        print(f"局数: {'阳遁' if self.is_yang else '阴遁'}{self.ju_number}局")
        print(f"旬首: {self.xunshou_ganzhi}")
        print(f"值使门: {self.zhishi_men}")
        rumu_list = self.get_rumu_palaces()
        if rumu_list:
            rumu_str = ', '.join(f"{r['宫名']}宫{r['天盘干']}(墓在{r['墓库地支']})" for r in rumu_list)
            print(f"天盘干入墓: {rumu_str}")
        else:
            print("天盘干入墓: 无")
        jixing_list = self.get_liuyi_jixing()
        if jixing_list:
            jixing_str = ', '.join(f"{r['宫名']}宫{r['六仪']}({r['刑理']})" for r in jixing_list)
            print(f"六仪击刑: {jixing_str}")
        else:
            print("六仪击刑: 无")
        men_po_list = self.get_men_po()
        if men_po_list:
            men_po_str = ', '.join(f"{r['宫名']}宫{r['门']}门({r['描述']})" for r in men_po_list)
            print(f"门迫: {men_po_str}")
        else:
            print("门迫: 无")
        maxing_info = self.get_maxing_palace()
        if maxing_info:
            print(f"马星: {maxing_info['宫名']}宫(马星地支{maxing_info['马星地支']}，时支{maxing_info['时支']})")
        else:
            print("马星: 无")
        print("=" * 60)
        print("\n九宫排盘:")
        print("-" * 60)
        
        for pos in QimenConstants.PALACE_TRAVERSE_ORDER + [5]:
            palace_name, direction = QimenConstants.PALACE_MAP[pos]
            data = self.palaces[pos]
            earth_display = self._get_earth_display(pos)
            print(f"{pos}宫 {palace_name}({direction}):")
            print(f"  地盘: {earth_display}")
            print(f"  天盘: {data['sky']}")
            print(f"  九星: {data['star']}")
            print(f"  八门: {data['door']}")
            print(f"  八神: {data['shen']}")
            print()
        
        print("=" * 60)
    
    def get_result_dict(self) -> Dict:
        """
        获取排盘结果字典
        
        Returns:
            dict: 包含所有排盘信息的字典
        """
        # 构建包含显示值的宫位数据（2宫、5宫的地盘干使用寄宫显示）
        palaces_export = {}
        for pos, data in self.palaces.items():
            palace_copy = dict(data)
            palace_copy['earth'] = self._get_earth_display(pos)
            palaces_export[pos] = palace_copy
        
        rumu_list = self.get_rumu_palaces()
        jixing_list = self.get_liuyi_jixing()
        men_po_list = self.get_men_po()
        maxing_info = self.get_maxing_palace()
        return {
            'input_time': self.input_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'ganzhi': {
                'year': self.year_gz,
                'month': self.month_gz,
                'day': self.day_gz,
                'hour': self.hour_gz
            },
            'jieqi': self.curr_jieqi,
            'yuan': self.curr_yuan,
            'ju_type': '阳遁' if self.is_yang else '阴遁',
            'ju_number': self.ju_number,
            'xunshou': self.xunshou_ganzhi,
            'zhishi_men': self.zhishi_men,
            'tianpan_rumu': rumu_list,  # 天盘干入墓的宫位列表
            'liuyi_jixing': jixing_list,  # 六仪击刑的宫位列表
            'men_po': men_po_list,  # 门迫的宫位列表
            'maxing': maxing_info,  # 马星所落宫位
            'palaces': palaces_export
        }
    
    def run(self) -> Dict:
        """
        执行完整的排盘流程
        
        Returns:
            dict: 排盘结果字典
        """
        try:
            self.calculate_ganzhi()
            self.calculate_futou()
            self.get_futou_jieqi()
            self.arrange_earth_plate()
            self.arrange_sky_plate()
            self.arrange_doors()
            self.arrange_shen()
            
            logger.info("排盘完成")
            return self.get_result_dict()
        
        except Exception as e:
            logger.error(f"排盘失败: {str(e)}")
            raise


# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == '__main__':
    # 测试用例
    test_cases = [
        "2024-11-19 20:00:00",
        "2025-02-28 18:30:00",
        "2024-06-07 16:30:00",
        "2025-03-13 04:00:00",
        # "2025-04-15 18:18:01"
        # "2025-10-23 03:00:00"
        "2026-02-12 22:00:00"
    ]
    
    # 选择测试用例
    datetime_str = test_cases[4]
    
    # 创建排盘对象并运行
    qimen = QiMenDunjiaPan(datetime_str)
    result = qimen.run()
    
    # 打印结果
    qimen.print_result()

