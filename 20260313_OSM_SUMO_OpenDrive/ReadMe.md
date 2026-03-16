https://hummels-jp.github.io/AIAgent/20260313_OSM_SUMO_OpenDrive/compare_result.html

1 对OSM地图中特定类型的道路数据进行变换输出
"highway"  IN ('trunk', 'trunk_link', 'secondary', 'tertiary')

netconvert --osm-files negishi.osm --output-file negishi.net.xml --keep-edges.by-type highway.trunk,highway.trunk_link,highway.secondary,highway.tertiary

2 对生成后得到的OSM数据，进行编辑，得到一个闭合的道路网络，以方便在RoadRunner中生成纹理数据。

3 执行命令，将 OSM 数据转换为 OpenDrive 数据。 默认行进方向为左行
 
netconvert --sumo-net-file negishi.net.xml --opendrive-output negishi.xodr  --lefthand true

4 在RoadRunner中导入OpenDrive数据，生成纹理数据，检查无误后，导出 fbx中间数据格式，以方便在Carla中导入。

5 在 Carla 中执行 make import 命令， 以便将 fbx 数据转换成Carla支持的Scene格式数据。

6 启动Carla 服务器，在 Carla客户端中查看相关场景数据，并执行自动驾驶相关功能。