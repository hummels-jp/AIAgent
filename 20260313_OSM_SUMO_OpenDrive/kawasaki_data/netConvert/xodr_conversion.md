# OpenDRIVE 转换说明

## 已执行的转换命令

### 1. 左侧通行的 OpenDRIVE 文件（日本标准）

```bash
netconvert --sumo-net-file kawasaki_filtered.net.xml --opendrive-output kawasaki_filtered.xodr --lefthand
```

**参数说明：**
- `--sumo-net-file kawasaki_filtered.net.xml` - 输入的SUMO网络文件
- `--opendrive-output kawasaki_filtered.xodr` - 输出的OpenDRIVE文件
- `--lefthand` - 设置为左侧通行（适用于日本、英国等国家）

### 2. 右侧通行的 OpenDRIVE 文件（默认）

```bash
netconvert --sumo-net-file kawasaki_filtered.net.xml --opendrive-output kawasaki_filtered_righthand.xodr
```

**说明：** 不加 `--lefthand` 参数时，默认为右侧通行（适用于中国、美国等国家）

## 生成文件对比

| 文件 | 大小 | 通行方向 | 说明 |
|------|------|----------|------|
| kawasaki_filtered.xodr | 944,182 bytes | 左侧通行 | 日本标准 |
| kawasaki_filtered_righthand.xodr | 949,132 bytes | 右侧通行 | 默认标准 |

## OpenDRIVE 文件关键信息

### 文件头信息
```xml
<header revMajor="1" revMinor="4" name="" version="1.00" date="Fri Mar 13 12:24:27 2026"
        north="1148.27" south="0.00" east="1314.11" west="0.00">
    <geoReference>
        +proj=utm +zone=54 +ellps=WGS84 +datum=WGS84 +units=m +no_defs
    </geoReference>
    <offset x="378166.96" y="3933717.33" z="-0.00" hdg="0"/>
</header>
```

**说明：**
- OpenDRIVE 版本：1.4
- 坐标系：UTM Zone 54N (适用于日本关东地区)
- 地理范围：
  - 北纬：3933717.33 + 1148.27 = 3934865.60 m
  - 南纬：3933717.33 m
  - 东经：378166.96 + 1314.11 = 379481.07 m
  - 西经：378166.96 m

### 左侧通行设置（在注释中）
```xml
<lefthand value="true"/>
```

## 左侧通行 vs 右侧通行

### 左侧通行（Left-hand traffic）
- **适用国家**：日本、英国、澳大利亚、印度等
- **特征**：
  - 车辆靠道路左侧行驶
  - 方向盘在车辆右侧
  - 车道编号从左到右递增
  - 左转需要跨越对向车道（更危险）
  - 右转不需要跨越对向车道

### 右侧通行（Right-hand traffic）
- **适用国家**：中国、美国、欧洲大陆大部分国家等
- **特征**：
  - 车辆靠道路右侧行驶
  - 方向盘在车辆左侧
  - 车道编号从右到左递增
  - 右转需要跨越对向车道
  - 左转不需要跨越对向车道（更危险）

## 转换过程中的警告信息

### 常见警告及处理建议

1. **Minor green exceeds**（绿灯时间过长）
   - 警告：`Minor green from edge '%' to edge '%' exceeds 19.44m/s. Maybe a left-turn lane is missing.`
   - 建议：添加左转专用车道或调整信号灯参数

2. **Speed reduced due to turning radius**（弯道限速）
   - 警告：`Speed of connection reduced due to turning radius`
   - 说明：由于转弯半径限制，自动降低了通过速度
   - 影响：车辆在弯道会自动减速，符合实际物理规律

3. **Could not compute smooth shape**（无法计算平滑曲线）
   - 警告：`Could not compute smooth shape from lane '%' to lane '%'`
   - 建议：使用 `--junctions.scurve-stretch` 参数或增加路口半径

### 优化建议

如果需要减少警告，可以使用以下参数：

```bash
# 增加路口半径以生成更平滑的曲线
netconvert --sumo-net-file kawasaki_filtered.net.xml \
  --opendrive-output kawasaki_filtered_smooth.xodr \
  --lefthand \
  --junctions.scurve-stretch 1.5 \
  --geometry.max-grade.fix true
```

## 验证 OpenDRIVE 文件

### 使用 OpenDRIVE 查看器
可以使用以下工具验证生成的 xodr 文件：
- **CARLA Simulator** - 支持加载 OpenDRIVE 格式
- **Esmini** - 开源的 OpenDRIVE 查看器
- **RoadRunner** - 专业的道路编辑软件
- **VIRES Virtual Test Drive** - 商业仿真软件

### 检查文件结构
使用文本编辑器打开 xodr 文件，检查以下元素：
- `<header>` - 文件头和元数据
- `<road>` - 道路定义
- `<planView>` - 道路几何形状
- `<lanes>` - 车道定义
- `<junction>` - 路口定义

## OpenDRIVE 车道方向说明

### 左侧通行（lefthand=true）
```
      道路方向 ->
┌─────────────┐
│  Lane 1     │  (最左侧，最内车道)
│─────────────│
│  Lane 2     │
│─────────────│
│  Lane 3     │  (最右侧，最外车道)
└─────────────┘
```

### 右侧通行（lefthand=false，默认）
```
      道路方向 ->
┌─────────────┐
│  Lane 1     │  (最右侧，最内车道)
│─────────────│
│  Lane 2     │
│─────────────│
│  Lane 3     │  (最左侧，最外车道)
└─────────────┘
```

## 注意事项

1. **坐标系统**：OpenDRIVE 使用局部笛卡尔坐标系，原点由 `<offset>` 定义
2. **单位**：OpenDRIVE 使用米作为长度单位，弧度作为角度单位
3. **兼容性**：确保目标仿真工具支持 OpenDRIVE 1.4 版本
4. **车道宽度**：默认车道宽度为 3.5m，可根据需要调整
5. **路口处理**：复杂路口可能需要手动调整以符合实际交通规则

## 常用转换参数

```bash
# 基本转换
netconvert --sumo-net-file input.net.xml --opendrive-output output.xodr

# 左侧通行
netconvert --sumo-net-file input.net.xml --opendrive-output output.xodr --lefthand

# 增加路口平滑度
netconvert --sumo-net-file input.net.xml --opendrive-output output.xodr \
  --junctions.scurve-stretch 1.5

# 设置路口半径
netconvert --sumo-net-file input.net.xml --opendrive-output output.xodr \
  --geometry.min-radius.fix true

# 包含道路名称
netconvert --sumo-net-file input.net.xml --opendrive-output output.xodr \
  --output.street-names
```
