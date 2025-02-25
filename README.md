# 奇门遁甲排盘系统 (Qi Men Dun Jia Calculator)

这是一个基于Python实现的奇门遁甲排盘系统。本系统主要实现了置闰法排盘的基础功能。

## 主要功能

qimenpaipan.py 是系统的主要入口文件，提供以下核心功能：

- 计算年月日时的干支
- 计算节气
- 确定符头和三元
- 支持置闰法排盘

## 使用方法

1. 确保安装了必要的依赖：

2. 下载天文数据文件：
- 将 'de421.bsp' 文件放在程序运行目录下

3. 基本使用示例：
```

## 输出信息

系统会返回包含以下信息的字典：
- 输入时间
- 年月日时干支
- 当前节气及其时间
- 符头信息
- 三元
- 符头距今天数
- 符头日期

## 文件说明

- `qimenpaipan.py`: 主程序入口文件，包含核心计算逻辑
- 其他 *.py 文件: 用于测试的辅助文件

## 注意事项

1. 运行前请确保已安装所有依赖包
2. 确保天文数据文件 'de421.bsp' 位于正确位置
3. 时间输入格式必须严格遵循 "YYYY-MM-DD HH:MM:SS" 的格式

## 参考资料

本项目参考了传统奇门遁甲的置闰法排盘方法，结合现代天文历法进行实现。

## License

MIT License

Copyright (c) 2024 [redrockhorse]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.