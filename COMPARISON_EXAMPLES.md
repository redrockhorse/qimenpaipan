# 代码优化对比示例

本文档展示优化前后的具体代码对比，帮助理解优化思路。

## 示例1：常量定义

### ❌ 优化前（分散、无组织）

```python
tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 文件中间某处
TIANGAN_ORDER = {gan: idx for idx, gan in enumerate(tiangan)}
DIZHI_ORDER = {zhi: idx for idx, zhi in enumerate(dizhi)}

# 文件后面某处
gan_to_start = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    # ...
}
```

### ✅ 优化后（集中管理、清晰命名）

```python
class GanzhiConstants:
    """干支常量 - 集中管理所有干支相关常量"""
    
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
```

**改进点：**
- ✅ 使用类组织相关常量
- ✅ 添加详细注释说明用途
- ✅ 命名空间避免全局污染
- ✅ 易于IDE代码提示

---

## 示例2：函数文档

### ❌ 优化前（文档不完整）

```python
def get_jieqi_time(year, target_degree):
    """ 计算指定年份特定黄经度数对应的节气时间 """
    for degree, month, _ in jieqi_info:
        if degree == target_degree:
            break
    
    start_year = year
    start_month = month - 1
    if start_month < 1:
        start_month = 12
        start_year -= 1
    # ... 更多代码
```

**问题：**
- ❌ 没有参数类型说明
- ❌ 没有返回值类型说明
- ❌ 没有使用类型提示
- ❌ 不知道参数的含义和范围

### ✅ 优化后（完整文档 + 类型提示）

```python
@staticmethod
def get_jieqi_time(year: int, target_degree: int) -> datetime:
    """
    计算指定年份特定黄经度数对应的节气时间
    
    使用二分法在指定年份中查找太阳黄经达到目标度数的准确时刻。
    精度可达秒级，适用于所有24节气的计算。
    
    Args:
        year: 年份（公历）
        target_degree: 目标黄经度数（0-360），例如：
            - 315度：立春
            - 0度：春分
            - 90度：夏至
            - 180度：秋分
            - 270度：冬至
            
    Returns:
        datetime: 节气时间（UTC时区）
        
    Example:
        >>> # 计算2025年立春时间
        >>> lichun = AstronomyCalculator.get_jieqi_time(2025, 315)
        >>> print(lichun)
        2025-02-03 16:10:45.123456+00:00
    """
    # 根据黄经度数确定对应的月份
    month = 1
    for degree, m, _ in JieqiConstants.JIEQI_INFO:
        if degree == target_degree:
            month = m
            break
    
    # 设置搜索范围（前后各扩展一个月）
    start_year = year
    start_month = month - 1
    if start_month < 1:
        start_month = 12
        start_year -= 1
    
    # ... 更多代码
```

**改进点：**
- ✅ 添加类型提示 `year: int`, `-> datetime`
- ✅ 详细说明函数功能
- ✅ 说明每个参数的含义和范围
- ✅ 说明返回值的类型和含义
- ✅ 提供使用示例

---

## 示例3：日志输出

### ❌ 优化前（print到处都是）

```python
def calculate_ganzhi(self):
    """计算干支"""
    self.year_gz = get_year_ganzhi(self.input_utc)
    self.month_gz = get_yue_ganzhi(self.input_utc)
    self.day_gz, self.hour_gz = get_day_houre_ganzhi(self.input_dt.strftime('%Y-%m-%d %H:%M:%S'))
    print(self.year_gz,self.month_gz,self.day_gz, self.hour_gz)

def get_futou_jieqi(self):
    print(get_solstices(self.futou_date.year))
    print(f"符头日期 {self.futou_date} 在{period}")
    print(f"参考节气时间: {effective_jieqi}")
    print(f"参考节气日干支: {effective_day_ganzhi}")
    print(f"符头信息: {futou_info}")
    print(f"符头日期: {effective_futou_date}")
    print('置闰')
    print(f"输入日期与符头相差{input_futou_diff}天")
    print(f"除以15的结果：整数部分={quotient}，余数部分={remainder}")
    print(f"从{self.period}开始，向后第{quotient}个节气是：{target_name}")
    print(f"阳遁{self.ju_number}局")
```

**问题：**
- ❌ 无法控制日志级别
- ❌ 无法关闭调试信息
- ❌ 日志格式不统一
- ❌ 生产环境会输出大量无用信息
- ❌ 无法输出到文件

### ✅ 优化后（使用logging模块）

```python
import logging

logger = logging.getLogger(__name__)

def calculate_ganzhi(self):
    """计算干支"""
    self.year_gz = GanzhiCalculator.get_year_ganzhi(self.input_utc)
    self.month_gz = GanzhiCalculator.get_month_ganzhi(self.input_utc)
    self.day_gz, self.hour_gz = GanzhiCalculator.get_day_hour_ganzhi(
        self.input_dt.strftime('%Y-%m-%d %H:%M:%S')
    )
    logger.info(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")

def get_futou_jieqi(self):
    """获取符头所在的节气，确定阴阳遁和局数"""
    # 获取夏至和冬至时间
    summer_solstice, winter_solstice = AstronomyCalculator.get_solstices(
        self.futou_date.year
    )
    
    logger.info(f"符头日期 {self.futou_date} 在{period}")
    logger.info(f"参考节气: {self.period}, 时间: {effective_jieqi}")
    logger.info(f"参考符头日期: {effective_futou_date}")
    
    if futou_info['符头差日'] > 9:
        logger.info("触发置闰")
        # ...
    
    logger.info(f"输入日期与符头相差 {input_futou_diff} 天")
    logger.info(f"除以15: 整数部分={quotient}, 余数部分={remainder}")
    logger.info(f"当前节气: {self.curr_jieqi}, 三元: {self.curr_yuan}")
    logger.info(f"阳遁 {self.ju_number} 局")
```

**改进点：**
- ✅ 统一使用logger
- ✅ 可以控制日志级别（DEBUG/INFO/WARNING/ERROR）
- ✅ 可以输出到文件
- ✅ 格式统一，包含时间戳
- ✅ 生产环境可以只显示警告和错误

**使用示例：**
```python
# 开发环境：显示详细日志
logging.basicConfig(level=logging.INFO)

# 生产环境：只显示警告
logging.basicConfig(level=logging.WARNING)

# 输出到文件
logging.basicConfig(
    level=logging.INFO,
    filename='qimen.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## 示例4：方法组织

### ❌ 优化前（独立函数，难以组织）

```python
# 文件顶部
def find_lichun(year):
    start = ts.utc(year, 2, 1)
    end = ts.utc(year, 2, 15)
    # ...

def get_jieqi_time(year, target_degree):
    # ...

def get_solstices(year: int) -> tuple[datetime, datetime]:
    # ...

# 使用时
lichun = find_lichun(2025)
jieqi = get_jieqi_time(2025, 315)
summer, winter = get_solstices(2025)
```

**问题：**
- ❌ 函数分散，难以管理
- ❌ 命名可能冲突
- ❌ 无法表达函数之间的关系

### ✅ 优化后（按功能分组到类）

```python
class AstronomyCalculator:
    """天文计算类 - 集中所有天文相关计算"""
    
    @staticmethod
    def get_sun_longitude(t) -> float:
        """获取太阳黄经"""
        # ...
    
    @staticmethod
    def find_lichun(year: int) -> datetime:
        """计算指定年份的立春准确时间"""
        # ...
    
    @staticmethod
    def get_jieqi_time(year: int, target_degree: int) -> datetime:
        """计算指定年份特定黄经度数对应的节气时间"""
        # ...
    
    @staticmethod
    def get_solstices(year: int) -> Tuple[datetime, datetime]:
        """获取指定年份的夏至和冬至时间"""
        # ...

# 使用时（清晰表达这些都是天文计算）
lichun = AstronomyCalculator.find_lichun(2025)
jieqi = AstronomyCalculator.get_jieqi_time(2025, 315)
summer, winter = AstronomyCalculator.get_solstices(2025)
```

**改进点：**
- ✅ 功能分组清晰
- ✅ 命名空间独立
- ✅ 易于查找和维护
- ✅ 表达了函数之间的关系

---

## 示例5：错误处理

### ❌ 优化前（缺少错误处理）

```python
def run(self):
    self.calculate_ganzhi()
    self.calculate_futou()
    self.get_futou_jieqi()
    self.arrange_earth_plate()
    self.arrange_sky_plate()
    self.arrange_doors()
    self.arrange_shen()
    print(self.palaces)
```

**问题：**
- ❌ 没有错误处理
- ❌ 出错时难以定位问题
- ❌ 无法优雅地处理异常

### ✅ 优化后（统一错误处理）

```python
def run(self) -> Dict:
    """
    执行完整的排盘流程
    
    Returns:
        dict: 排盘结果字典
        
    Raises:
        ValueError: 当输入参数无效时
        RuntimeError: 当排盘计算失败时
    """
    try:
        logger.info("开始排盘...")
        
        self.calculate_ganzhi()
        self.calculate_futou()
        self.get_futou_jieqi()
        self.arrange_earth_plate()
        self.arrange_sky_plate()
        self.arrange_doors()
        self.arrange_shen()
        
        logger.info("排盘完成")
        return self.get_result_dict()
    
    except ValueError as e:
        logger.error(f"输入参数错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"排盘失败: {str(e)}")
        raise RuntimeError(f"排盘计算出错: {str(e)}") from e
```

**改进点：**
- ✅ 统一的错误处理
- ✅ 详细的错误日志
- ✅ 区分不同类型的异常
- ✅ 提供有用的错误信息

---

## 示例6：返回值设计

### ❌ 优化前（只能print，无法获取结果）

```python
def run(self):
    # ... 执行计算
    print(self.palaces)  # 只打印，无法获取数据

# 使用时
qimen = QiMenDunjiaPan("2025-04-15 16:18:01")
qimen.run()
# 无法获取结果用于后续处理
```

### ✅ 优化后（返回结构化数据 + 提供打印方法）

```python
def run(self) -> Dict:
    """执行完整的排盘流程，返回结构化结果"""
    # ... 执行计算
    return self.get_result_dict()

def get_result_dict(self) -> Dict:
    """获取排盘结果字典"""
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
        'palaces': self.palaces
    }

def print_result(self):
    """打印格式化的排盘结果"""
    print("\n" + "=" * 60)
    print("奇门遁甲排盘结果")
    print("=" * 60)
    print(f"输入时间: {self.input_dt}")
    print(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")
    # ... 更多格式化输出

# 使用方式1：获取数据
qimen = QiMenDunjiaPan("2025-04-15 16:18:01")
result = qimen.run()
print(result['ganzhi']['year'])  # 获取年干支

# 使用方式2：打印结果
qimen.print_result()

# 使用方式3：保存到JSON
import json
with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

**改进点：**
- ✅ 返回结构化数据
- ✅ 数据和展示分离
- ✅ 易于集成到其他系统
- ✅ 便于单元测试
- ✅ 支持多种输出方式

---

## 示例7：魔术数字优化

### ❌ 优化前（到处都是魔术数字）

```python
def arrange_earth_plate(self):
    qiyi_order = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]  
    start_pos = self.ju_number 
    
    positions = []
    current = start_pos
    for _ in range(9):  # 9是什么？
        positions.append(current)
        current = current % 9 + 1 if self.is_yang else (current - 2) % 9 + 1
    
    for i, pos in enumerate(positions):
        self.palaces[pos]['earth'] = qiyi_order[i % 6] if i <6 else qiyi_order[6 + (i-6)%3]
    
    dipan_tiangan_array = []
    for pos in [1,8,3,4,9,2,7,6]:  # 这些数字代表什么？
        dipan_tiangan_array.append(self.palaces[pos]['earth'])
```

**问题：**
- ❌ 9、6、3等魔术数字不知道含义
- ❌ [1,8,3,4,9,2,7,6] 不知道是什么顺序
- ❌ 难以理解和维护

### ✅ 优化后（使用命名常量）

```python
class QimenConstants:
    # 三奇六仪顺序
    QIYI_ORDER = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    
    # 九宫遍历顺序（不含中宫5）
    PALACE_TRAVERSE_ORDER = [1, 8, 3, 4, 9, 2, 7, 6]
    
    # 六仪数量
    LIUYI_COUNT = 6
    
    # 三奇数量
    SANQI_COUNT = 3
    
    # 宫位总数
    PALACE_COUNT = 9

def arrange_earth_plate(self):
    """排布地盘（三奇六仪）"""
    # 确定戊的起始宫位
    start_pos = self.ju_number
    
    # 生成九宫遍历路径
    positions = []
    current = start_pos
    for _ in range(QimenConstants.PALACE_COUNT):
        positions.append(current)
        # 阳遁顺行，阴遁逆行
        if self.is_yang:
            current = current % QimenConstants.PALACE_COUNT + 1
        else:
            current = (current - 2) % QimenConstants.PALACE_COUNT + 1
    
    # 填充天干（六仪→三奇循环）
    for i, pos in enumerate(positions):
        if i < QimenConstants.LIUYI_COUNT:
            # 六仪
            self.palaces[pos]['earth'] = QimenConstants.QIYI_ORDER[i]
        else:
            # 三奇（循环使用）
            idx = QimenConstants.LIUYI_COUNT + (i - QimenConstants.LIUYI_COUNT) % QimenConstants.SANQI_COUNT
            self.palaces[pos]['earth'] = QimenConstants.QIYI_ORDER[idx]
    
    # 保存地盘天干数组（用于天盘旋转）
    self.dipan_tiangan_array = [
        self.palaces[pos]['earth'] 
        for pos in QimenConstants.PALACE_TRAVERSE_ORDER
    ]
```

**改进点：**
- ✅ 用常量替代魔术数字
- ✅ 名称清晰表达含义
- ✅ 易于理解和维护
- ✅ 修改常量时不会遗漏

---

## 总结

通过这些对比示例可以看出，优化后的代码在以下方面有显著提升：

1. **组织性** - 代码结构清晰，易于导航
2. **可读性** - 命名规范，注释完善
3. **可维护性** - 模块化设计，易于修改
4. **专业性** - 符合Python最佳实践
5. **可扩展性** - 易于添加新功能
6. **可测试性** - 便于编写单元测试
7. **可调试性** - 日志系统完善
8. **可集成性** - 返回结构化数据

这些改进使代码更加**工程化**和**生产就绪**，适合团队协作和长期维护。

