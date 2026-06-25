---

<div align="center">
  <strong>🌐 Language / 语言 / 言語:</strong>
  <a href="基于Transformer的目标检测模型综述.md">中文</a> |
  <a href="Transformer-Based_Object_Detection_Models_Overview.md">English</a> |
  <a href="Transformerベース物体検出モデル総説.md">日本語</a>
</div>

---

# Transformerベース物体検出モデル総説

## 目次
1. [はじめに](#はじめに)
2. [DETR (Detection Transformer)](#detr-detection-transformer)
3. [Deformable DETR](#deformable-detr)
4. [DAB-DETR (Dynamic Anchor Boxes DETR)](#dab-detr-dynamic-anchor-boxes-detr)
5. [DN-DETR (Denoising DETR)](#dne-detr-denoising-detr)
6. [Conditional DETR](#conditional-detr)
7. [Co-DETR (Cooperative Hybrid DETR)](#co-detr-cooperative-hybrid-detr)
8. [RT-DETR (Real-Time DETR)](#rt-detr-real-time-detr)
9. [Group DETR](#group-detr)
10. [比較とまとめ](#比較とまとめ)

---

## はじめに

Transformerベースの物体検出モデルは、2020年にDETRが提案されて以来、物体検出分野を根本から変革しました。Faster R-CNN、YOLOなど従来のCNNベースの検出器とは異なり、Transformerベースの検出器は自己注意機構とエンコーダ-デコーダアーキテクチャを活用し、物体検出タスクを集合予測問題として定式化します。

### コアとなる利点
- **エンドツーエンド学習**: アンカー(Anchors)の手動設計、非最大抑制(NMS)などの後処理ステップが不要
- **グローバルな文脈理解**: 自己注意機構が長距離の依存関係を捉えられる
- **柔軟性**: 統一されたアーキテクチャで他のタスク（セグメンテーション、姿勢推定など）に容易に拡張可能

### 主な課題
- **収束が遅い**: 従来のDETRは数百エポックかけて収束する必要がある
- **小さい物体の検出**: 注意機構が小さなサイズの物体を見落とす可能性がある
- **計算コストが高い**: 自己注意の2次複雑性

---

## DETR (Detection Transformer)

### 発表情報
- **論文**: "End-to-End Object Detection with Transformers" (ECCV 2020)
- **機関**: Facebook AI Research (FAIR)
- **著者**: Nicolas Carion, Francisco Massa, Gabriel Synnaeve, Nicolas Usunier, Alexander Kirillov, Sergey Zagoruyko

### 設計思想

DETRは物体検出を直接の集合予測問題として捉え、Transformerのエンコーダ-デコーダアーキテクチャを採用します。核心となるアイデア：

1. **二部マッチング損失**: 予測オブジェクトと正解オブジェクトをハンガリアンアルゴリズムで1対1にマッチング
2. **オブジェクトクエリ(Object Queries)**: 物体の位置とクラスをデコードするための学習可能な埋め込みベクトルの集合
3. **並列デコード**: すべてのオブジェクトを同時に予測し、順次生成を不要にする

### アーキテクチャ

```
入力画像 (H×W×3)
    ↓
CNNバックボーン (ResNet-50/101)
    ↓
特徴マップ (H/32 × W/32 × C)
    ↓
位置エンコーディング (正弦/余弦エンコーディング)
    ↓
[特徴マップ + 位置エンコーディング]
    ↓
Transformerエンコーダ (6層)
    ↓
エンコードされた特徴
    ↓
Transformerデコーダ (6層)
    ↓ (N個のオブジェクトクエリ)
予測集合 (N個の予測ボックス)
    ↓
分類ブランチ + 境界ボックス回帰ブランチ
    ↓
最終検出結果
```

#### 主要コンポーネント

1. **バックボーンネットワーク**: 通常、ResNetやResNeXtを使用して画像特徴を抽出
2. **位置エンコーディング**: 特徴に空間位置情報を注入
   - 固定正弦エンコーディングまたは学習可能エンコーディング
3. **Transformerエンコーダ**:
   - マルチヘッド自己注意機構
   - フィードフォワードニューラルネットワーク
   - 6層のスタック
4. **Transformerデコーダ**:
   - マルチヘッドクロスアテンション（エンコーダ特徴をクエリ）
   - マルチヘッド自己注意（オブジェクトクエリ間の相互作用）
   - フィードフォワードニューラルネットワーク
   - 6層のスタック
5. **予測ヘッド**:
   - 分類ヘッド: クラス確率 + "無オブジェクト"クラスを予測
   - 境界ボックスヘッド: 中心座標、幅、高さを予測

### 特徴

1. **アンカーフリーデザイン**: 事前設定アンカーなしで境界ボックスを直接予測
2. **NMSフリー**: 学習と推論の両方で非最大抑制が不要
3. **集合予測**: 固定数の予測を同時に出力
4. **二部マッチング**: ハンガリアンアルゴリズムによる最適割り当て

### 利点

- ✅ 検出ワークフローを簡素化、ハイパーパラメータ調整を削減
- ✅ 強力なグローバル文脈モデリング能力
- ✅ マルチタスク学習（セグメンテーション、パノプティックセグメンテーション）に拡張可能
- ✅ NMSによる精度損失を回避

### 欠点

- ❌ 収束が遅い（最高性能に500エポック必要）
- ❌ 計算コストが高い（自己注意のO(n²)複雑度）
- ❌ 小さい物体検出の性能が低い
- ❌ 特徴抽出がCNNに依存、純粋なTransformerバックボーンが十分に探索されていない

---

## Deformable DETR

### 発表情報
- **論文**: "Deformable DETR: Deformable Transformers for End-to-End Object Detection" (ICLR 2022)
- **機関**: SenseTime Research, The University of Hong Kong, etc.
- **著者**: Xizhou Zhu, Weijie Su, Lewei Lu, Bin Li, Xiaogang Wang, Jifeng Dai

### 設計思想

元のDETRの収束が遅く、計算コストが高いという課題に対処するため、Deformable DETRは可変形注意機構を導入しました。これは可変形畳み込みに着想を得ています：

1. **スパース注意**: 特徴マップのすべての位置ではなく、少数の重要な位置のみに注目
2. **マルチスケール特徴**: FPNを活用してマルチスケール特徴を抽出、小さい物体検出を強化
3. **可変形注意モジュール**: 標準注意を置換し、計算コストを削減

### アーキテクチャ

```
入力画像
    ↓
ResNetバックボーン
    ↓
マルチスケール特徴 {P3, P4, P5} (1/8, 1/16, 1/32)
    ↓
マルチスケール位置エンコーディング
    ↓
Deformable Transformerエンコーダ
    ↓ (各層で可変形注意を使用)
エンコードされた特徴
    ↓
Deformable Transformerデコーダ
    ↓ (可変形クロスアテンション)
予測結果
```

#### 可変形注意機構

クエリポイントqについて、注意計算はK個のサンプリングポイントを含みます：

```python
# 注意ヘッドlとサンプリング層kについて
参照点 p_{q,l} = MLP(クエリq)
サンプリング点 p_{q,l} + Δm_{q,l,m} (m=1..M)
注意重み A_{q,l,m,k}
集約特徴 = Σ_{m=1..M} Σ_{k=1..4} A_{q,l,m,k} · f_{p_k}(サンプリング点)
```

ここで：
- K=4: マルチスケール層数
- M=4または8: 各層のサンプリング点数
- Δ: オフセット（学習可能）

### 特徴

1. **マルチスケール特徴**: C3-C5層から特徴を抽出
2. **可変形注意**: 少数の重要点のみに注目、複雑度を削減
3. **反復的な改善**: デコーダが段階的に境界ボックスを精緻化

### 利点

- ✅ 10倍速い収束（50エポック vs 500エポック）
- ✅ 計算コストが大幅に削減（O(n²)からO(n×k)へ）
- ✅ 小さい物体検出の性能が大幅に向上
- ✅ 高解像度画像に適している

### 欠点

- ❌ まだ比較的長い学習時間が必要
- ❌ 注意機構の設計がやや複雑
- ❌ ハイパーパラメータに敏感

---

## DAB-DETR (Dynamic Anchor Boxes DETR)

### 発表情報
- **論文**: "DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR" (ICCV 2023)
- **機関**: University of Chinese Academy of Sciences, etc.

### 設計思想

DAB-DETRはオブジェクトクエリの初期化方法を再設計し、オブジェクトクエリを4Dアンカーボックス（中心座標cx, cy, 幅w, 高さh）として表現します：

1. **動的アンカーボックス**: オブジェクトクエリを学習可能なアンカーボックスとして初期化、ランダム埋め込みではありません
2. **段階的な更新**: デコーダが層ごとにアンカーボックスを精緻化
3. **アンベースの位置エンコーディング**: 現在のアンカーボックスに基づいて位置埋め込みを生成

### アーキテクチャ

```
初期化: N個の4Dアンカーボックス (cx, cy, w, h)
    ↓
位置埋め込み生成器 (アンカーボックスに基づく)
    ↓
Transformerデコーダ (6層)
    ↓ (各層でアンカーボックスを更新)
最終アンカーボックス + クラス予測
```

#### アンカーボックス更新機構

各デコーダ層：
1. **回帰ブランチ**: アンカーボックスの残差を予測 (Δcx, Δcy, Δw, Δh)
2. **アンカーボックス更新**: アンカーボックス ← アンカーボックス + 残差
3. **新しい位置埋め込み生成**: 更新されたアンカーボックスに基づく
4. **クロスアテンション**: 新しい位置埋め込みを使用して特徴をクエリ

### 特徴

1. **アンベースのクエリ**: オブジェクトクエリが境界ボックスとして明示的に表現
2. **反復回帰**: 予測ボックスを段階的に精緻化
3. **適応型位置エンコーディング**: 位置エンコーディングがアンカーボックスと共に更新

### 利点

- ✅ DETRより3倍以上速い収束
- ✅ 学習の安定性が向上
- ✅ 物体検出の直感的理解に合致
- ✅ ランダム初期化の不確実性を回避

### 欠点

- ❌ まだアンカーボックス概念に依存、完全なアンカーフリーの利点を失う
- ❌ アンカーボックス初期化戦略の設計が必要
- ❌ 極端なサイズの物体に十分堅牢ではない可能性

---

## DN-DETR (Denoising DETR)

### 発表情報
- **論文**: "DN-DETR: Accelerate DETR Training by Positive Query Anchor" (ICCV 2023)
- **機関**: Peking University

### 設計思想

DN-DETRはコントラスト学習の考えを導入し、学習時に「ノイズ」を追加して収束を加速します：

1. **デノイズ学習**: 正解ボックスにノイズを追加して「妨害」クエリを生成
2. **コントラスト学習**: モデルがノイズボックスと正解ボックスを区別するよう学習
3. **補助損失**: デノイズ損失を追加し、モデルの高速な位置特定を支援

### アーキテクチャ

```
学習フェーズ:
正解境界ボックス (GT boxes)
    ↓
ノイズ追加 (平行移動、スケーリング)
    ↓
ノイズクエリ + 元のオブジェクトクエリ
    ↓
Transformerデコーダ
    ↓
分類損失 (ノイズ/正解の区別) + 検出損失
```

#### ノイズ追加戦略

各正解ボックスGTについて：
1. **平行移動ノイズ**: Δx, Δy ~ N(0, σ²)
2. **スケールノイズ**: Δw, Δh ~ N(0, σ²)
3. **ノイズクエリ生成**: ノイズ追加後のGT + クラスラベル

### 特徴

1. **デノイズタスク**: モデルの学習を支援する補助タスク
2. **コントラスト学習**: ノイズを通じて特徴学習を加速
3. **プラグ可能デザイン**: 他のDETR変種と組み合わせ可能

### 利点

- ✅ 収束速度が大幅に向上（DETRより12倍速い）
- ✅ 複雑なアーキテクチャ変更不要
- ✅ 様々なDETR変種に適用可能
- ✅ 汎化性能が良い

### 欠点

- ❌ 学習の複雑度が増加（ノイズ生成が必要）
- ❌ 推論時にデノイズを使用しないため、学習-推論が不一致
- ❌ ノイズレベルの微調整が必要

---

## Conditional DETR

### 発表情報
- **論文**: "Conditional DETR for Fast Training Convergence" (ICCV 2022)
- **機関**: The University of Hong Kong, etc.

### 設計思想

Conditional DETRは元のDETRの収束が遅い原因を分析しました：オブジェクトクエリ同士が高度に類似しており、注意重みが分散する。解決策：

1. **条件付き空間クエリ**: 各クエリに空間事前分布を追加
2. **内容-空間クロスアテンション**: 内容クエリと空間クエリを分離
3. **高速収束**: 学習エポックを大幅に削減

### アーキテクチャ

```
オブジェクトクエリ (内容埋め込み)
    ↓
空間クエリ (学習可能な空間位置エンコーディング)
    ↓
条件付きクロスアテンション
    ↓ (クエリ = 内容クエリ + 空間クエリ)
Transformerデコーダ
    ↓
予測結果
```

#### 条件付きクロスアテンション

```python
# 標準クロスアテンション
Q = オブジェクトクエリ
K = エンコーダ特徴
V = エンコーダ特徴

# 条件付きクロスアテンション
Q_content = 内容クエリ
Q_spatial = 空間クエリ (異なるクエリが異なる空間事前分布を持つ)
K = エンコーダ特徴
V = エンコーダ特徴

アテンション = softmax(Q_spatial · K^T) · Q_content · V
```

### 特徴

1. **空間事前分布**: 各クエリが異なる空間エンコーディングを持つ
2. **分離された注意**: 内容と空間を分離
3. **軽量な変更**: 追加計算不要

### 利点

- ✅ 6-10倍速い収束
- ✅ 実装がシンプル、計算オーバーヘッドが小さい
- ✅ 検出精度を維持
- ✅ 他のDETR改善と互換

### 欠点

- ❌ まだ多くの学習エポックが必要（~200）
- ❌ 空間事前分布の設計が十分柔軟ではない
- ❌ 密なシーンの最適化が限定的

---

## Co-DETR (Cooperative Hybrid DETR)

### 発表情報
- **論文**: "Co-DETR: Collaboration with Hybrid Detection Heads for Object Detection" (ICCV 2023)
- **機関**: DAMO Academy, Alibaba Group, etc.

### 設計思想

Co-DETRは協調メカニズムを通じて複数の検出ヘッドの利点を組み合わせます：

1. **ハイブリッド検出ヘッド**: 分類認識ボックスヘッド、分類フリーボックスヘッドなどを同時に装備
2. **協調学習**: 異なる検出ヘッドが特徴を共有し、互いに支援
3. **集合マッチング**: 複数のマッチング戦略を組み合わせ

### アーキテクチャ

```
Transformerエンコーダ-デコーダ
    ↓
複数の検出ヘッド (並列):
    - 検出ヘッドA (分類 + 回帰)
    - 検出ヘッドB (回帰のみ)
    - 検出ヘッドC (異なるIoU閾値)
    ↓
協調損失 (重み付き組み合わせ)
```

#### 協調メカニズム

```python
# 検出ヘッド間の知識共有
共有特徴 = デコーダ出力
予測A = 検出ヘッドA(共有特徴)
予測B = 検出ヘッドB(共有特徴)

# 複数のマッチング戦略
マッチ1 = ハンガリアンマッチング (予測A, GT)
マッチ2 = IoUマッチング (予測B, GT)

# 損失融合
総損失 = α·損失A + β·損失B + 協調損失
```

### 特徴

1. **マルチ検出ヘッド**: 複数の検出戦略を統合
2. **協調学習**: 異なるヘッドが相互に促進
3. **柔軟な設定**: ニーズに応じて検出ヘッドの組み合わせを選択可能

### 利点

- ✅ 精度と速度を両立
- ✅ マルチタスク学習が堅牢性を向上
- ✅ 様々なDETR変種に適用可能
- ✅ SOTA性能を達成

### 欠点

- ❌ モデル複雑度が増加
- ❌ 学習に多くのリソースが必要
- ❌ 多くのハイパーパラメータ（重み、マッチング戦略）

---

## RT-DETR (Real-Time DETR)

### 発表情報
- **論文**: "DETRs Beat YOLOs on Real-time Object Detection" (ICCV 2023)
- **機関**: Baidu, Peking University

### 設計思想

RT-DETRはリアルタイム性能を達成した初のTransformerベース物体検出器です：

1. **ハイブリッドエンコーダ**: CNNとTransformerの利点を組み合わせ
2. **効率的デコーダ**: 最適化された注意計算
3. **適応型クエリ選択**: オブジェクトクエリを動的に選択
4. **アンカーフリーデザイン**: エンドツーエンド学習を維持

### アーキテクチャ

```
入力画像
    ↓
ResNetバックボーン (C3-C5)
    ↓
ハイブリッドエンコーダ:
    - CNNエンコーダ層: 局所特徴集約
    - Transformerエンコーダ層: グローバル文脈
    ↓ (マルチスケール特徴)
クエリセレクタ:
    - Top-K特徴をオブジェクトクエリとして選択
    ↓
RT-DETRデコーダ
    ↓
予測結果
```

#### ハイブリッドエンコーダ

```python
# マルチスケール特徴 {P3, P4, P5} について
for level in [P3, P4, P5]:
    # CNNエンコーダ: AIFI (Attention-based Feature Interaction)
    feat_cnn = CNN_encoder(level)

    # Transformerエンコーダ: CCFF (Cross-scale Feature Fusion)
    feat_transformer = Transformer_encoder(feat_cnn)

    # 特徴を融合
    final_feat = fuse(feat_cnn, feat_transformer)
```

#### クエリ選択

```python
# エンコーダ特徴からオブジェクトクエリを選択
class_scores = classification_head(encoder_features)
box_scores = iou_head(encoder_features)
combined_scores = class_scores × box_scores

topk_queries = select_topk(combined_scores, K=300)
```

### 特徴

1. **リアルタイム性能**: 300+ FPSを達成（高解像度画像）
2. **ハイブリッドアーキテクチャ**: CNN+Transformerのベストプラクティス
3. **適応型クエリ**: 最も有望なクエリを動的に選択
4. **マルチスケール**: 異なるサイズの物体に適している

### 利点

- ✅ リアルタイム性能を達成した初のDETR
- ✅ 精度と速度のバランスが優秀
- ✅ NMSなどの後処理不要
- ✅ デプロイが容易、TensorRTなどをサポート

### 欠点

- ❌ エンコーダ-デコーダ設計が複雑
- ❌ ハイパーパラメータの微調整が必要
- ❌ 極端なシーン（超高密度）に課題あり

---

## Group DETR

### 発表情報
- **論文**: "Group DETR: Efficient DETR Training with Grouped One-to-One Assignment" (ECCV 2024)

### 設計思想

Group DETRはグループ化マッチング戦略を通じてDETRの学習不安定性に対処します：

1. **グループ化マッチング**: オブジェクトクエリをグループ化、各グループが独立してマッチング
2. **グループ内競合**: 同一グループ内のクエリが同一オブジェクトを競合
3. **グループ間協調**: 異なるグループが情報を共有

### アーキテクチャ

```
N個のオブジェクトクエリ
    ↓
Gグループに分割（各グループN/G個のクエリ）
    ↓
独立マッチング（各グループでハンガリアンアルゴリズム使用）
    ↓
グループ内コントラスト損失 + グループ間協調損失
    ↓
総損失
```

#### グループ化マッチング

```python
# クエリのグループ化
queries = [q1, q2, ..., qN]
groups = divide(queries, num_groups=G)

# 各グループの独立マッチング
for group in groups:
    predictions = decoder(group)
    assignment = hungarian_match(predictions, GT)
    loss = compute_loss(predictions, GT, assignment)

# グループ間協調
collaboration_loss = group_aware_regularization(groups)
```

### 特徴

1. **グループ化戦略**: 単一マッチングの複雑度を削減
2. **競合-協調**: 探索と活用のバランス
3. **拡張性**: 異なるグループ数をサポート

### 利点

- ✅ 学習がより安定、振動を削減
- ✅ 収束速度が向上
- ✅ 大規模データセットに適している
- ✅ 各グループを並列学習可能

### 欠点

- ❌ 最適なグループ数を決定する必要がある
- ❌ グループ間協調メカニズムが複雑度を増加
- ❌ 実装が比較的複雑

---

## 比較とまとめ

### 性能比較

| モデル | バックボーン | エポック数 | mAP(COCO) | FPS | 学習安定性 |
|--------|--------------|-----------|-----------|-----|-----------|
| DETR | ResNet-50 | 500 | 42.0 | 28 | ★★☆ |
| Deformable DETR | ResNet-50 | 50 | 46.2 | 35 | ★★★ |
| DAB-DETR | ResNet-50 | 150 | 46.8 | 32 | ★★★ |
| DN-DETR | ResNet-50 | 50 | 47.0 | 30 | ★★★★ |
| Conditional DETR | ResNet-50 | 150 | 43.5 | 29 | ★★★ |
| Co-DETR | ResNet-50 | 50 | 49.5 | 28 | ★★★★ |
| RT-DETR | ResNet-50 | 50 | 53.0 | 108 | ★★★★★ |
| Group DETR | ResNet-50 | 100 | 47.2 | 35 | ★★★★ |

### コア技術イノベーション

#### 1. 注意機構の改善
- **DETR**: 標準グローバル注意
- **Deformable DETR**: 可変形スパース注意
- **RT-DETR**: ハイブリッドCNN+Transformer注意

#### 2. オブジェクトクエリ設計
- **DETR**: ランダム学習可能埋め込み
- **DAB-DETR**: 動的アンカーボックス表現
- **Conditional DETR**: 条件付き空間クエリ
- **RT-DETR**: 適応型クエリ選択

#### 3. 学習戦略
- **DETR**: 標準二部マッチング
- **DN-DETR**: デノイズ学習
- **Group DETR**: グループ化マッチング
- **Co-DETR**: マルチヘッド協調

#### 4. 特徴表現
- **DETR**: 単一スケール特徴
- **Deformable DETR**: マルチスケール特徴
- **RT-DETR**: マルチスケール + ハイブリッドエンコーディング

### 利点と欠点の総合分析

#### 速度と精度のトレードオフ

```
高精度 → RT-DETR, Co-DETR, Deformable DETR
    ↓
バランス → DAB-DETR, DN-DETR, Group DETR
    ↓
高速 → RT-DETR, Conditional DETR
```

#### 適用シーン

- **汎用物体検出**: Deformable DETR, RT-DETR
- **リアルタイムアプリケーション**: RT-DETR
- **小さい物体が密集**: Deformable DETR, Co-DETR
- **研究/ベンチマーク**: DETR(ベースライン), DN-DETR
- **リソース制限**: Conditional DETR

### 発展傾向

1. **ハイブリッドアーキテクチャ**: CNN+Transformerが主流に
2. **効率的注意**: スパース注意、可変形注意
3. **適応型クエリ**: 動的な選択と初期化
4. **マルチタスク学習**: 検出、セグメンテーション、追跡の統合
5. **リアルタイム最適化**: TensorRT、ONNXデプロイメント最適化

### 将来の方向性

1. **純粋なTransformerバックボーン**: ViTをバックボーンネットワークとして探索
2. **ビデオ検出**: エンドツーエンドビデオ物体検出
3. **Few-Shot/Zero-Shot**: CLIPなどのマルチモーダルモデルと組み合わせ
4. **自己教師あり学習**: 教師なし事前学習戦略
5. **エッジデプロイメント**: モバイルデバイスでのリアルタイム検出

---

## 参考文献

1. Carion, N., Massa, F., Synnaeve, G., Usunier, N., Kirillov, A., & Zagoruyko, S. (2020). End-to-End Object Detection with Transformers. *ECCV*.

2. Zhu, X., Su, W., Lu, L., Li, B., Wang, X., & Dai, J. (2021). Deformable DETR: Deformable Transformers for End-to-End Object Detection. *ICLR*.

3. Liu, S., Zeng, Z., Ren, T., Li, Z., Zhang, X., Wang, Z., ... & Li, H. (2022). DAB-DETR: Dynamic Anchor Boxes are Better Queries for DETR. *ICCV*.

4. Li, J., Wang, Y., Luo, H., Liu, Y., Li, Z., & Yuan, L. (2022). DN-DETR: Accelerate DETR Training by Positive Query Anchor. *ICCV*.

5. Meng, D., Chen, X., Liu, S., Xie, E., Zeng, Z., Li, J., ... & Sun, P. (2022). Conditional DETR for Fast Training Convergence. *ICCV*.

6. Lv, W., Guo, Y., Wang, J., Zhang, D., & Liu, S. (2023). Co-DETR: Collaboration with Hybrid Detection Heads for Object Detection. *ICCV*.

7. Lv, W., Feng, D., Wu, L., Cao, C., Wang, Z., Wu, D., ... & Liu, S. (2023). DETRs Beat YOLOs on Real-time Object Detection. *ICCV*.

8. Wang, Y., Gu, Y., He, T., & Wang, H. (2024). Group DETR: Efficient DETR Training with Grouped One-to-One Assignment. *ECCV*.

---

<div align="center">
  <strong>🌐 Language / 语言 / 言語:</strong>
  <a href="01_基于Transformer的目标检测模型综述.md">中文</a> |
  <a href="01_Transformer-Based_Object_Detection_Models_Overview.md">English</a> |
  <a href="01_Transformerベース物体検出モデル総説.md">日本語</a>
</div>

<div align="center">
  <strong>🌐 Language / 语言 / 言語:</strong>
  <a href="基于Transformer的目标检测模型综述.md">中文</a> |
  <a href="Transformer-Based_Object_Detection_Models_Overview.md">English</a> |
  <a href="Transformerベース物体検出モデル総説.md">日本語</a>
</div>

---

*ドキュメントバージョン: v1.0*
*作成日: 2026-03-16*
*著者: AI Assistant*
