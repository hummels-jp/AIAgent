# netconvert 命令使用说明

## 已执行的命令

### 1. 筛选指定道路类型的SUMO网络

```bash
netconvert --osm-files kawasaki.osm --output-file kawasaki_filtered.net.xml --keep-edges.by-type highway.primary,highway.secondary,highway.tertiary,highway.residential
```

**参数说明：**
- `--osm-files kawasaki.osm` - 输入的OSM文件
- `--output-file kawasaki_filtered.net.xml` - 输出的SUMO网络文件
- `--keep-edges.by-type highway.primary,highway.secondary,highway.tertiary,highway.residential` - 只保留指定的道路类型

### 2. 生成完整的SUMO网络（作为对比）

```bash
netconvert --osm-files kawasaki.osm --output-file kawasaki_full.net.xml
```

## 文件对比

| 文件 | 大小 | 说明 |
|------|------|------|
| kawasaki_full.net.xml | 1,142,966 bytes | 完整的网络（包含所有道路类型） |
| kawasaki_filtered.net.xml | 324,746 bytes | 筛选后的网络（仅4种道路类型） |
| **压缩比** | **71.6%** | 文件大小减少了约71.6% |

## 常用的筛选参数

### 按道路类型筛选

#### 只保留指定类型
```bash
netconvert --osm-files input.osm --output-file output.net.xml --keep-edges.by-type highway.primary,highway.secondary,highway.tertiary,highway.residential
```

#### 删除指定类型
```bash
netconvert --osm-files input.osm --output-file output.net.xml --remove-edges.by-type highway.footway,highway.path,highway.track,highway.cycleway,highway.steps
```

### 按其他条件筛选

#### 按速度筛选（只保留速度大于等于30km/h的路段）
```bash
netconvert --osm-files input.osm --output-file output.net.xml --keep-edges.min-speed 8.33
```

#### 按车辆类型筛选（只保留允许汽车通行的路段）
```bash
netconvert --osm-files input.osm --output-file output.net.xml --keep-edges.by-vclass passenger
```

#### 删除孤立路段
```bash
netconvert --osm-files input.osm --output-file output.net.xml --remove-edges.isolated
```

#### 按边界筛选
```bash
netconvert --osm-files input.osm --output-file output.net.xml --keep-edges.in-geo-boundary 35.0,139.0,35.5,139.5
```

### 组合使用多种筛选条件

```bash
netconvert --osm-files input.osm --output-file output.net.xml \
  --keep-edges.by-type highway.primary,highway.secondary,highway.tertiary,highway.residential \
  --keep-edges.min-speed 5.55 \
  --remove-edges.isolated
```

## 常见道路类型

### 适合保留的道路类型（车辆仿真）
- `highway.motorway` - 高速公路
- `highway.motorway_link` - 高速公路连接线
- `highway.trunk` - 主干道
- `highway.primary` - 主要道路
- `highway.secondary` - 次要道路
- `highway.tertiary` - 三级道路
- `highway.residential` - 住宅区道路
- `highway.unclassified` - 未分类道路

### 通常删除的道路类型
- `highway.footway` - 人行道
- `highway.path` - 小径
- `highway.track` - 土路
- `highway.cycleway` - 自行车道
- `highway.pedestrian` - 步行街
- `highway.steps` - 台阶

## 注意事项

1. **连通性检查**：筛选后检查路网连通性，避免孤立的断点
2. **边界效应**：删除某些道路可能导致边界连接问题
3. **性能优化**：筛选后的网络文件更小，仿真速度更快
4. **适用场景**：根据仿真目标选择合适的道路类型组合

## 验证生成的网络

使用 SUMO-GUI 查看生成的网络：
```bash
sumo-gui kawasaki_filtered.net.xml
```

或使用 netedit 编辑网络：
```bash
netedit kawasaki_filtered.net.xml
```
