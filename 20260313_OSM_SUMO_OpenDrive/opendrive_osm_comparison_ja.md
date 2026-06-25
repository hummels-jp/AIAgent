# OpenDrive vs OpenStreetMap 詳細比較

## 一、基本フォーマット

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| Headerバージョン | revMinor=4/5 | - |
| 座標システム | UTM/地理座標 | WGS84 |
| 数値フォーマット | 小数/科学記法 | 小数 |

**説明**：
- OpenDrive はより厳密なバージョン管理を使用し、revMinor でサブバージョンを区別
- OpenDrive は複数の座標システムをサポート（局部UTMやグローバル地理座標）
- OpenStreetMap はWGS84 経緯度座標システムで統一

## 二、コンテンツ要素

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 車線幅 | 3.20-3.75m | 3.75m |
| 車線マーキング | 詳細あり | 基本あり |
| 速度情報 | あり | あり |
| rule属性 | あり | - |
| surface要素 | あり | - |

**説明**：
- **車線幅**：OpenDriveは各車線で幅を独立設定可能（3.20-3.75m）、OSMは通常デフォルト3.75m
- **車線マーキング**：OpenDriveは詳細なマーキングタイプ（実線、破線、二重線など）をサポート、OSMは基本的マーキングのみ
- **速度情報**：両方サポート、OpenDriveは車線レベルで細分化、OSMは通常道路単位
- **rule属性**：OpenDriveは詳細な通行規則属性あり、OSMは欠如
- **surface要素**：OpenDriveは路面素材を詳細記録、OSMは情報が限定的

## 三、道路幾何

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| Reference line | 〇 | - |
| 曲率（line/arc/clothoid） | 〇 | - |
| 道路長 | 〇 | - |
| 標高（elevation） | 〇 | - |
| 横断勾配 | 〇 | - |
| 横断形状 | 〇 | - |

**詳細説明**：

1. **Reference line（参照線）**
   - **OpenDrive**：各道路に明確な参照線があり、幾何記述の基礎
   - **OSM**：参照線の概念なし、ノードとwayで経路記述

2. **曲率**
   - **OpenDrive**：3種類の正確な幾何タイプをサポート
     - Line：直線セグメント
     - Arc：円弧
     - Clothoid（クロソイド）：曲率が線形に変化する遷移曲線、滑らかな接続用
   - **OSM**：直線セグメントのみで曲線を近似、精度が低い

3. **道路長**
   - **OpenDrive**：各道路セグメントの長さを正確に計算・保存
   - **OSM**：長さはノード座標から導出、直接保存しない

4. **標高（elevation）**
   - **OpenDrive**：3D標高情報をサポート、上り下りを記述可能
   - **OSM**：高度情報は欠如または外部データソースが必要

5. **横断勾配（superelevation）**
   - **OpenDrive**：道路の横断勾配、カントを記録
   - **OSM**：この種の情報は含まれない

6. **横断形状**
   - **OpenDrive**：道路横断面を詳細記述（路肩、側溝など）
   - **OSM**：基本的に記述しない

## 四、レーン構造

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| レーンID | 〇 システム一意ID | 〇 wayとrelationで間接表現 |
| レーン幅 | 〇 正確な数値、可変 | △ lanesとwidthタグで推定 |
| レーンタイプ | 〇 詳細分類（driving, sidewalk, shoulder等） | △ 部分サポート（lanes:psv等） |
| レーン接続 | 〇 明確なpredecessor/successor関係 | 〇 turn:lanes等タグ |
| 速度制限 | 〇 正確な数値、レーンレベル | 〇 maxspeedタグ |
| アクセス制限 | 〇 詳細ルール（vehicle, pedestrian等） | 〇 accessタグ |

**詳細説明**：
- **レーンID**：OpenDriveは各レーンに一意IDを割り当て、正確な参照が可能；OSMは道路wayとレーン関係で間接表現
- **レーン幅**：OpenDriveは道路に沿って変化するレーン幅をサポート；OSMは通常全体的道路幅のみ
- **レーンタイプ**：OpenDriveは10+種類のレーンタイプをサポート；OSMはタイプが限定的

## 五、区画線

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 実線/破線 | 〇 詳細タイプ（solid, broken, double等） | △ 部分サポート |
| 色/幅/車線変更 | 〇 色と幅をサポート、車線変更ルール明確 | ✗ サポートなし |
| パターン/複合線 | 〇 複雑なパターンサポート | ✗ サポートなし |

**詳細説明**：
- OpenDriveの`<roadMark>`要素は以下をサポート：
  - タイプ：solid, broken, solid_solid, solid_broken, broken_solid, broken_broken
  - 色：standard, blue, green, red, white, yellow, orange
  - 幅：正確な数値
  - 車線変更ルール：explicitマーク
- OSMは主に`turn:lanes`等のタグで間接表現、詳細な幾何・視覚情報が欠如

## 六、交通標識・信号

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 信号機 | 〇 詳細（位置、タイプ、フェーズ） | 〇 highway=traffic_signals |
| 停止標識 | 〇 サポート | 〇 highway=stop |
| 制限速度標識 | 〇 正確な数値と位置 | 〇 maxspeed + traffic_sign |
| 進入禁止 | 〇 サポート | 〇 access=no |
| 車線別制限 | 〇 詳細なレーンレベル制限 | △ 限定サポート |
| 警告標識 | 〇 サポート | △ 部分サポート |

**詳細説明**：
- **信号機**：
  - OpenDrive：`<signal>`要素は位置、タイプ、コントローラー、フェーズ等の完全情報を含む
  - OSM：位置を簡単マーク、フェーズとコントローラー情報なし
- **車線別制限**：
  - OpenDrive：各レーンに独立制限を設定可能
  - OSM：主に`lanes`と`turn:lanes`で間接表現

## 七、道路オブジェクト

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 停止線 | 〇 正確な幾何位置 | ✗ サポートなし |
| 横断歩道 | 〇 詳細な幾何とタイプ | 〇 highway=crossing |
| 路面ペイント | 〇 サポート | ✗ サポートなし |
| ガードレール/ポール | 〇 サポート（guardRail, pole等） | ✗ サポートなし |
| 路肩縁石/建物 | 〇 サポート | ✗ サポートなし |
| 駐車スペース | 〇 サポート | 〇 amenity=parking |
| バリア/トンネル/橋 | 〇 詳細タイプ | 〇 barrier, tunnel, bridge |

**詳細説明**：
- OpenDriveの`<object>`要素は30+種類の道路オブジェクトタイプをサポート
- OSMは主に機能的マークに焦点、正確な幾何記述が欠如

## 八、交差点構造

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 接続道路 | 〇 明確なjunction定義 | 〇 wayで接続 |
| turning relation | 〇 詳細な転回パス | 〇 turn:lanesタグ |
| lane connection | 〇 正確なレーンレベル接続 | △ 限定サポート |

**詳細説明**：
- **junction**：
  - OpenDrive：交差点タイプを明確定義（default, direct, common）、全接続関係を含む
  - OSM：ノードで接続、明確な交差点構造定義なし
- **lane connection**：
  - OpenDrive：`<junction>`内で各レーンの接続関係を明確定義
  - OSM：レーンレベルの接続情報が欠如

## 九、路面特性

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| 摩擦係数 | 〇 サポート | ✗ サポートなし |
| 路面材質 | 〇 surface要素詳細記述 | 〇 surfaceタグ |
| roughness | 〇 サポート | ✗ サポートなし |

**詳細説明**：
- OpenDriveの`<surface>`要素は以下を含む：
  - 摩擦係数（friction）
  - 粗さ（roughness）
  - 材質タイプ
- OSMは単純な`surface`タグのみ（asphalt, concrete等）

## 十、拡張機能

| 要素 | OpenDrive | OpenStreetMap |
|------|-----------|---------------|
| userData | 〇 カスタム拡張データサポート | ✗ サポートなし |

**詳細説明**：
- OpenDriveの`<userData>`はアプリ固有のカスタムデータ追加を許可
- OSMはタグで拡張可能だが、構造化カスタムデータサポートが欠如

## 十一、応用シナリオ

| 応用シナリオ | OpenDrive | OpenStreetMap |
|-------------|-----------|---------------|
| 自動運転シミュレーション | ◎ 非常に適している | △ 多量の補完が必要 |
| 運転シミュレーター | ◎ 非常に適している | ✗ 不適切 |
| ナビゲーションアプリ | △ 使用可能だが重い | ◎ 非常に適している |
| 経路計画 | 〇 適している | ◎ 非常に適している |
| 地図表示 | △ 使用可能 | ◎ 非常に適している |
| 交通分析 | ◎ 非常に適している | 〇 適している |

---

## まとめ対比表

| カテゴリ | OpenDriveの優位性 | OSMの優位性 |
|---------|-------------------|------------|
| **精度** | 高精度幾何、シミュレーションに適 | グローバルカバレッジ、コミュニティ保守 |
| **レーン情報** | 詳細なレーンレベルデータ | 簡潔で使いやすい |
| **3D情報** | 完全な3Dサポート | 軽量な2D |
| **交通施設** | 詳細なオブジェクト記述 | 豊富なPOIデータ |
| **拡張性** | 構造化拡張 | 柔軟なタグシステム |
| **データ取得** | 専門的制作が必要 | 無料オープン |
| **更新頻度** | 遅い | リアルタイム更新 |

**結論**：OpenDriveは高精度シミュレーションと専門アプリに適しており、OpenStreetMapは汎用地図サービスとナビゲーションに適している。両者は補完的に使用でき、変換ツールでそれぞれの優位性を組み合わせることが可能。

---

**Language / 言語**：[🇨🇳 中文](opendrive_osm_comparison.md) | [🇯🇵 日本語](opendrive_osm_comparison_ja.md) | [🇺🇸 English](opendrive_osm_comparison_en.md)
