# Two-Stage Object Detection Algorithms Overview

<div style="position: fixed; top: 10px; right: 10px; z-index: 1000; background: #f5f5f5; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 14px;">
  <strong>Language Switch:</strong>
  <a href="两阶段目标检测算法综述.md">🇨🇳 中文</a> | 
  <a href="二段階オブジェクト検出アルゴリズム総説.md">🇯🇵 日本語</a> | 
  <a href="Two-Stage Object Detection Algorithms Overview.md" style="font-weight: bold; color: #007bff;">🇺🇸 English</a>
</div>

<br>
<br>

## Table of Contents
- [1. Overview of Two-Stage Object Detection Algorithms](#1-overview-of-two-stage-object-detection-algorithms)
- [2. R-CNN (Regions with CNN features)](#2-r-cnn-regions-with-cnn-features)
- [3. SPP Net (Spatial Pyramid Pooling Network)](#3-spp-net-spatial-pyramid-pooling-network)
- [4. Fast R-CNN](#4-fast-r-cnn)
- [5. Faster R-CNN](#5-faster-r-cnn)
- [6. Algorithm Comparison and Summary](#6-algorithm-comparison-and-summary)

---

## 1. Overview of Two-Stage Object Detection Algorithms

### 1.1 What is Two-Stage Object Detection?

Two-Stage object detection algorithms complete object detection tasks through two stages:

**First Stage**: Region Proposal Generation
- Extract regions from original images that may contain target objects
- Also known as Region Proposal Network (RPN) or Selective Search

**Second Stage**: Classification and Localization of Candidate Regions
- Extract features from each candidate region
- Object classification (what object it is)
- Bounding box regression (accurately locate object position)

### 1.2 Characteristics of Two-Stage Algorithms

**Advantages**:
- High detection accuracy, especially for small object detection
- Region proposal stage provides good prior information
- Accurate localization

**Disadvantages**:
- Slow inference speed
- High computational resource consumption
- Difficult to meet real-time requirements

### 1.3 Typical Application Scenarios
- Applications where accuracy is prioritized over speed
- Medical image diagnosis
- Satellite image analysis
- Backend validation in autonomous driving

---

## 2. R-CNN (Regions with CNN features)

### 2.1 Algorithm Concept

R-CNN is a pioneering work that introduced deep learning to the field of object detection, proposed by Ross Girshick et al. in 2014. Its core idea is:

1. **Region Extraction**: Use Selective Search algorithm to extract approximately 2000 candidate regions from images
2. **Feature Extraction**: Resize each candidate region to a fixed size (227×227) and extract features through Convolutional Neural Network (CNN)
3. **Classification and Regression**:
   - Use SVM to classify each region
   - Use linear regressor to refine bounding boxes

### 2.2 Model Architecture

```
Input Image (arbitrary size)
    ↓
Selective Search
    ↓
~2000 Candidate Regions
    ↓
Image Resize (227×227)
    ↓
CNN Feature Extraction (AlexNet/VGG)
    ↓
Feature Vector (4096-d)
    ↓
┌─────────────┬─────────────┐
│   SVM       │ Bounding Box│
│  Classification│  Regression │
└─────────────┴─────────────┘
```

### 2.3 Training Process

**Step 1: Pre-train CNN**
- Pre-train CNN on ImageNet (e.g., AlexNet)

**Step 2: Fine-tune CNN**
- Fine-tune CNN using object detection dataset, replace last layer with N+1 classes (N object classes + background)

**Step 3: Train SVM**
- Extract CNN features from each candidate region
- Train independent SVM classifier for each class

**Step 4: Train Bounding Box Regressor**
- Train linear regression model to refine candidate box positions

### 2.4 Main Advantages

1. **Pioneering Contribution**
   - First successful application of CNN to object detection
   - Significantly improved detection accuracy (mAP from ~30% to 53%)

2. **High Detection Accuracy**
   - CNN-extracted features have powerful representation capability
   - Selective Search generates high-quality candidate regions

3. **High Flexibility**
   - Can replace different CNN backbone networks
   - Applicable to different datasets

### 2.5 Main Disadvantages

1. **Extremely Slow Speed**
   - Processing one image takes approximately 47 seconds (on GPU)
   - Reason: Need to perform CNN forward propagation independently for each candidate region

2. **Complex Training Process**
   - Multi-stage training (CNN fine-tuning, SVM training, regressor training)
   - Need to save large amount of intermediate features
   - Difficult to optimize training process

3. **Redundant Computation Problem**
   - Large amount of overlap exists between candidate regions
   - Same regions are computed multiple times for CNN features

4. **Fixed Size Limitation**
   - Candidate regions need to be resized to fixed size
   - May cause image distortion or information loss

5. **High Memory Usage**
   - Need to store large amount of intermediate results
   - Feature cache occupies large disk space

### 2.6 Performance Metrics
- **mAP (VOC 2010)**: 53.3%
- **Inference Time**: ~47 seconds/image (GPU)
- **Backbone**: AlexNet/VGG-16

---

## 3. SPP Net (Spatial Pyramid Pooling Network)

### 3.1 Algorithm Concept

SPP Net was proposed by He Kaiming et al. in 2015, with core innovation of introducing **Spatial Pyramid Pooling layer**.

Key Problems Solved:
- R-CNN requires input images to be fixed size
- Image resizing causes distortion or information loss
- Large amount of redundant computation

Core Idea:
1. Perform only one complete CNN forward propagation on the entire image
2. Use SPP layer to convert feature maps of different sizes into fixed-length feature vectors
3. Extract features corresponding to candidate regions from feature maps

### 3.2 SPP Layer Principle

Spatial Pyramid Pooling layer can convert input feature maps of arbitrary size into fixed-size output.

```
Feature Map (W × H × C)
    ↓
┌─────────────┬─────────────┬─────────────┐
│  1×1 bin    │  2×2 bins   │  4×4 bins   │
│ (max pooling)│ (max pooling)│ (max pooling)│
└─────────────┴─────────────┴─────────────┘
    ↓           ↓           ↓
  1×C        4×C         16×C
    ↓           ↓           ↓
    └───────────┴───────────┘
            ↓
    Concatenate: 1×C + 4×C + 16×C = 21×C
            ↓
      Fixed Dimension Feature Vector
```

Example: For VGG-16's 512-channel output, using 1×1, 2×2, 4×4 pyramids
- Output dimension: 1×512 + 4×512 + 16×512 = 21×512 = 10752 dimensions

### 3.3 Model Architecture

```
Input Image (arbitrary size)
    ↓
CNN Convolutional Layers (complete forward propagation once)
    ↓
Feature Map (arbitrary size)
    ↓
┌─────────────────────────┐
│   Selective Search generates│
│       candidate boxes    │
└─────────────────────────┘
    ↓
Extract candidate regions from feature map
    ↓
┌─────────────────────────┐
│      SPP Layer          │
│   (pyramid pooling)     │
└─────────────────────────┘
    ↓
Fixed Dimension Feature Vector
    ↓
┌─────────────┬─────────────┐
│   SVM       │ Bounding Box│
│ Classification│  Regression │
└─────────────┴─────────────┘
```

### 3.4 Main Advantages

1. **Significantly Improved Speed**
   - Only one CNN forward propagation needed for entire image
   - 24-102 times faster than R-CNN

2. **Accepts Arbitrary Input Size**
   - No need to resize image to fixed size
   - Maintains original image aspect ratio and details

3. **Solves Redundant Computation Problem**
   - CNN features computed only once
   - Candidate regions extracted from feature map, avoiding redundant computation

4. **Consistent Receptive Field**
   - SPP layer can generate multi-scale feature representations
   - Captures spatial information at different scales

### 3.5 Main Disadvantages

1. **Training Still Multi-Stage**
   - Cannot be trained end-to-end
   - Complex training process

2. **Limited Feature Extraction**
   - Still extracts features from last convolutional layer
   - Doesn't fully utilize multi-layer features

3. **Dependent on Candidate Region Quality**
   - Still relies on Selective Search
   - Slow candidate region generation

### 3.6 Performance Metrics
- **mAP (VOC 2007)**: 59.2%
- **Inference Time**: ~0.5-2 seconds/image
- **Speed Improvement**: 24-102× faster than R-CNN

---

## 4. Fast R-CNN

### 4.1 Algorithm Concept

Fast R-CNN was proposed by Ross Girshick in 2015, as a major improvement to R-CNN. Main innovations:

1. **Shared Convolutional Features**: Only one CNN forward propagation for entire image
2. **RoI Pooling Layer**: Map candidate regions of different sizes to fixed-size feature maps
3. **Multi-task Loss**: Simultaneously optimize classification and bounding box regression, enabling end-to-end training
4. **Unified Training**: No longer need to train SVM separately

### 4.2 RoI Pooling Principle

RoI (Region of Interest) Pooling maps RoI features of arbitrary size to fixed size (e.g., 7×7).

```
RoI: (x, y, w, h)
Corresponding region on feature map: (x', y', w', h')
    ↓
Divide into k×k sub-regions (usually k=7)
    ↓
Take max value for each sub-region
    ↓
Output: k×k×C (7×7×C)
```

Difference from SPP:
- SPP uses multi-scale pyramid pooling
- RoI Pooling uses single-scale pooling (e.g., 7×7)
- RoI Pooling designed specifically for object detection, more efficient

### 4.3 Model Architecture

```
Input Image (arbitrary size)
    ↓
CNN Convolutional Layers (complete forward propagation once)
    ↓
Feature Map
    ↓
Selective Search generates candidate regions (~2000)
    ↓
Map RoIs to feature map
    ↓
RoI Pooling (unified to 7×7×C)
    ↓
Flatten + Fully Connected Layers
    ↓
┌─────────────┬─────────────┐
│  Classification│ Bounding Box│
│   Scores   │  Regression │
│ (N+1 classes)│ (4N params) │
└─────────────┴─────────────┘
```

### 4.4 Multi-task Loss Function

Fast R-CNN uses joint loss function to simultaneously optimize classification and localization:

```
L(p, u, t^u, v) = L_cls(p, u) + λ[u ≥ 1]L_loc(t^u, v)
```

Where:
- `p`: Predicted classification probability distribution (softmax output)
- `u`: Ground truth class label
- `t^u`: Predicted bounding box offset for class u
- `v`: Ground truth bounding box offset
- `λ`: Balance parameter (usually λ=1)
- `[u ≥ 1]`: Indicator function (no localization loss for background)

**Classification Loss** (cross-entropy):
```
L_cls(p, u) = -log(p_u)
```

**Localization Loss** (Smooth L1 loss):
```
L_loc(t^u, v) = Σ smooth_L1(t_i^u - v_i)

smooth_L1(x) = {
    0.5x²           if |x| < 1
    |x| - 0.5       otherwise
}
```

### 4.5 Training Process

**Single-Stage End-to-End Training**:
1. Use SGD to optimize entire network
2. Mini-batch training (2 images per batch, 128 RoIs)
3. Hierarchical sampling strategy: 32 positive samples + 96 negative samples

**Positive/Negative Sample Definition**:
- **Positive Samples**: IoU ≥ 0.5
- **Negative Samples**: 0.1 ≤ IoU < 0.5

### 4.6 Main Advantages

1. **Significantly Improved Training Speed**
   - Single-stage training, no need to pre-train SVM
   - Can use SGD for end-to-end optimization
   - 9× faster training than R-CNN

2. **Improved Inference Speed**
   - 213× faster testing than R-CNN
   - Also improved over SPP Net

3. **Higher Accuracy**
   - Joint optimization with multi-task loss
   - Higher accuracy than R-CNN and SPP Net

4. **Unified Framework**
   - No need to save features to disk
   - Simple training and inference pipeline

5. **Better Feature Utilization**
   - RoI Pooling more effective than warping
   - Preserves spatial information

### 4.7 Main Disadvantages

1. **Candidate Region Generation Still Bottleneck**
   - Still relies on Selective Search
   - Generating ~2000 candidate regions takes 2-3 seconds
   - Accounts for majority of total inference time

2. **Non-Real-Time Detection**
   - Total inference time ~0.3-0.5 seconds/image
   - Difficult to meet real-time application requirements

3. **Training Still Dependent on Pre-generated Candidate Regions**
   - Need to pre-generate candidate regions
   - Adds pre-processing step

### 4.8 Performance Metrics
- **mAP (VOC 2007)**: 66.9% (VGG-16)
- **mAP (VOC 2012)**: 68.4% (VGG-16)
- **Inference Time**: ~0.3 seconds/image (GPU, excluding candidate region generation)
- **Training Time**: ~9.5 hours (VOC 2007+2012, VGG-16)

---

## 5. Faster R-CNN

### 5.1 Algorithm Concept

Faster R-CNN was proposed by Shaoqing Ren et al. in 2015, a milestone in two-stage detection algorithms. Core innovations:

1. **Region Proposal Network (RPN)**: Replace Selective Search with neural network
2. **Shared Convolutional Features**: RPN and Fast R-CNN share CNN convolutional layers
3. **Near Real-Time Detection Speed**: Significantly improve speed while maintaining high accuracy

Key Breakthrough: **Fully integrate candidate region generation into neural network, achieving true end-to-end detection.**

### 5.2 RPN (Region Proposal Network)

#### 5.2.1 RPN Architecture

RPN is a fully convolutional network that generates candidate regions directly on convolutional feature maps.

```
Convolutional Feature Map (W × H × 512, VGG-16)
    ↓
3×3 Convolution (512 channels)
    ↓
┌─────────────────┬─────────────────┐
│  1×1 Conv (2k)  │  1×1 Conv (4k)  │
│ (object/non-object)│ (box regression)│
└─────────────────┴─────────────────┘
      ↓               ↓
   Classification    Offsets
      Scores
      ↓               ↓
   ~2k anchors per location
```

Where `k` is the number of preset anchors per location (usually k=9).

#### 5.2.2 Anchor Mechanism

Each feature map location has k preset anchors of different scales and aspect ratios:

```
k = 9 anchors
  - 3 scales: 128², 256², 512²
  - 3 aspect ratios: 1:1, 1:2, 2:1
```

Generated at each location:
- **objectness score**: Predict whether anchor is object or background (2×9 outputs)
- **box regression offset**: Predict offset from anchor to ground truth box (4×9 outputs)

#### 5.2.3 RPN Loss Function

```
L({pi}, {ti}) = (1/N_cls) Σ L_cls(pi, pi*) + λ(1/N_reg) Σ pi* L_reg(ti, ti*)
```

Where:
- `pi`: Predicted probability that anchor i is object
- `ti`: Predicted bounding box offset for anchor i
- `pi*`: Ground truth label (1 for positive sample, 0 for negative sample)
- `ti*`: Ground truth bounding box offset
- `N_cls`, `N_reg`: Normalization parameters (mini-batch size and anchor count)
- `λ`: Balance parameter (usually λ=10)

**Positive/Negative Sample Definition**:
- **Positive Samples**: 
  - Highest IoU with ground truth box
  - Or IoU > 0.7 with any ground truth box
- **Negative Samples**: IoU < 0.1 with all ground truth boxes

### 5.3 Model Architecture

```
Input Image
    ↓
CNN Convolutional Layers (shared)
    ↓
Convolutional Feature Map
    ↓
┌──────────────────┬──────────────────┐
│      RPN         │                  │
│ (candidate region│                  │
│   generation)    │                  │
└──────────────────┴──────────────────┘
         ↓
   RoI Proposals
    ↓
RoI Pooling
    ↓
Fully Connected Layers
    ↓
┌─────────────┬─────────────┐
│  Classification│ Bounding Box│
│   Scores   │  Regression │
└─────────────┴─────────────┘
```

### 5.4 Training Strategy

#### 5.4.1 Four-Step Alternating Training

Since RPN and Fast R-CNN share convolutional layers, alternating training is needed:

**Step 1**: Train RPN
- Train RPN from scratch
- Use ImageNet pre-trained CNN

**Step 2**: Train Fast R-CNN with RPN-generated training data
- Fix shared convolutional layers
- Train Fast R-CNN with candidate regions generated by RPN

**Step 3**: Fine-tune RPN
- Initialize shared convolutional layers with Fast R-CNN parameters
- Fix RPN-specific layers, fine-tune shared convolutional layers

**Step 4**: Fine-tune Fast R-CNN
- Fix shared convolutional layers
- Fine-tune Fast R-CNN-specific layers

#### 5.4.2 Approximate Joint Training

More efficient method: Merge RPN and Fast R-CNN into one network with unified multi-task loss.

```
L = L_rpn + L_fast_rcnn
```

### 5.5 Main Advantages

1. **Significantly Improved Speed**
   - Candidate region generation reduced from 2 seconds to 0.01 seconds
   - Total inference time ~0.2 seconds/image (VGG-16)
   - Achieves near real-time (5 fps)

2. **Maintained or Improved Accuracy**
   - Higher mAP than Fast R-CNN
   - Shared features enhance model representation capability

3. **True End-to-End Training**
   - Candidate region generation fully learnable
   - Unified optimization objective

4. **Reduced Computation through Parameter Sharing**
   - RPN and detection network share convolutional features
   - Significantly reduces computational complexity

5. **High Scalability**
   - Applicable to different backbone networks
   - Extensible to other vision tasks

### 5.6 Main Disadvantages

1. **Still Not Real-Time**
   - ~5 fps on VGG-16
   - Not fast enough for real-time applications (e.g., video surveillance)

2. **High Computational Resource Requirements**
   - Need large memory to store intermediate features
   - High hardware requirements

3. **Limited Small Object Detection**
   - Deep layer features lose small object information
   - Need multi-scale feature fusion

4. **Sensitive to Anchor Design**
   - Need to adjust anchor scales and aspect ratios for datasets
   - Inappropriate anchors affect performance

### 5.7 Performance Metrics
- **mAP (VOC 2007)**: 78.8% (ResNet-101)
- **mAP (VOC 2012)**: 75.9% (ResNet-101)
- **Inference Time**: 
  - VGG-16: ~0.2 seconds/image (5 fps)
  - ResNet-101: ~0.14 seconds/image (7 fps)
- **RPN Time**: ~10 ms/image

---

## 6. Algorithm Comparison and Summary

### 6.1 Development Timeline

```
2014: R-CNN
    ↓ (Too slow, redundant computation)
2015: SPP Net (arbitrary input size, feature sharing)
    ↓ (Multi-stage training)
2015: Fast R-CNN (RoI Pooling, end-to-end training)
    ↓ (Candidate regions still bottleneck)
2015: Faster R-CNN (RPN neural network, near real-time)
```

### 6.2 Performance Comparison

| Algorithm | mAP (VOC 07) | Inference Time | Candidate Region Generation | Training Mode | Speed vs R-CNN |
|-----------|--------------|----------------|----------------------------|---------------|----------------|
| R-CNN | 53.3% | ~47 seconds | Selective Search | Multi-stage | 1× |
| SPP Net | 59.2% | ~0.5-2 seconds | Selective Search | Multi-stage | 24-102× |
| Fast R-CNN | 66.9% | ~0.3 seconds | Selective Search | Single-stage | 213× |
| Faster R-CNN | 78.8% | ~0.2 seconds | RPN (neural network) | End-to-end | ~235× |

### 6.3 Core Technology Evolution

| Technical Aspect | R-CNN | SPP Net | Fast R-CNN | Faster R-CNN |
|------------------|-------|---------|------------|--------------|
| Candidate Region Generation | Selective Search | Selective Search | Selective Search | RPN (neural network) |
| Feature Sharing | ❌ Each RoI computed independently | ✅ Computed once for entire image | ✅ Computed once for entire image | ✅ Computed once for entire image |
| Pooling Method | Warping | SPP (multi-scale) | RoI Pooling (single-scale) | RoI Pooling |
| Fixed Input Size | ✅ Needs resize | ❌ Arbitrary size | ❌ Arbitrary size | ❌ Arbitrary size |
| Training Mode | Multi-stage (CNN+SVM+regression) | Multi-stage | Single-stage (multi-task loss) | End-to-end |
| Classifier | SVM | SVM | Softmax | Softmax |

### 6.4 Summary of Advantages and Disadvantages

#### R-CNN
**Advantages**:
- Pioneering work, first successful CNN application to object detection
- Significantly higher accuracy than traditional methods

**Disadvantages**:
- Extremely slow (47 seconds/image)
- Redundant computation, resource waste
- Complex training, multi-stage

#### SPP Net
**Advantages**:
- Accepts arbitrary input size
- Significant speed improvement (24-102×)
- Solves redundant computation problem

**Disadvantages**:
- Still multi-stage training
- Doesn't fully exploit features

#### Fast R-CNN
**Advantages**:
- End-to-end training, unified framework
- Multi-task loss, higher accuracy
- Significantly improved training and inference speed

**Disadvantages**:
- Candidate region generation still bottleneck
- Not real-time

#### Faster R-CNN
**Advantages**:
- RPN uses neural network for candidate region generation
- True end-to-end training
- Near real-time (5-7 fps)
- Highest accuracy

**Disadvantages**:
- Still not real-time
- High computational resource requirements
- Sensitive to anchor design

### 6.5 Key Technical Innovations

1. **Feature Sharing**
   - Common feature of SPP Net, Fast R-CNN, Faster R-CNN
   - Compute features once for entire image, avoid redundant computation

2. **Pooling Layer Design**
   - SPP: Multi-scale pyramid pooling
   - RoI Pooling: Fixed-size pooling, designed specifically for detection

3. **End-to-End Training**
   - Fast R-CNN introduced multi-task loss
   - Faster R-CNN achieved complete end-to-end

4. **Candidate Region Generation**
   - R-CNN/SPP/Fast: Selective Search (traditional algorithm)
   - Faster: RPN (learnable neural network)

### 6.6 Practical Application Recommendations

**Choose R-CNN when**:
- Almost never (only as learning reference)

**Choose Fast R-CNN when**:
- Limited hardware resources
- Low real-time requirements
- Need high accuracy

**Choose Faster R-CNN when**:
- General object detection tasks
- Accuracy prioritized, near real-time acceptable
- Sufficient hardware resources (GPU recommended)
- Need end-to-end training

### 6.7 Subsequent Developments

After Faster R-CNN, two-stage detection algorithms continued to evolve:

- **Mask R-CNN** (2017): Added instance segmentation branch to Faster R-CNN
- **Cascade R-CNN** (2018): Cascaded structure to progressively improve IoU threshold
- **FPN (Feature Pyramid Network)** (2017): Multi-scale feature fusion
- **Various improved versions**: Backbone optimization, attention mechanisms, etc.

### 6.8 Comparison with One-Stage Algorithms

| Comparison Dimension | Two-Stage (Faster R-CNN) | One-Stage (YOLO, SSD) |
|---------------------|--------------------------|----------------------|
| Accuracy | Higher | Slightly Lower |
| Speed | Slower (5-10 fps) | Faster (30-60+ fps) |
| Small Object Detection | Better | Poorer |
| Training Difficulty | Higher | Lower |
| Real-Time | Difficult to achieve | Easy to achieve |

---

## 7. References

1. **R-CNN**: Girshick, R., et al. "Rich feature hierarchies for accurate object detection and semantic segmentation." CVPR 2014.

2. **SPP Net**: He, K., et al. "Spatial pyramid pooling in deep convolutional networks for visual recognition." TPAMI 2015.

3. **Fast R-CNN**: Girshick, R. "Fast R-CNN." ICCV 2015.

4. **Faster R-CNN**: Ren, S., et al. "Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks." NIPS 2015.

---

## Appendix: Key Terms

- **IoU (Intersection over Union)**: Intersection over Union, measures overlap between two boxes
- **mAP (mean Average Precision)**: Mean Average Precision, main evaluation metric for object detection
- **RoI (Region of Interest)**: Region of Interest
- **Anchor**: Preset candidate boxes, used to initialize detection boxes
- **Selective Search**: Traditional candidate region generation algorithm
- **Backbone**: Backbone network, CNN for feature extraction (e.g., VGG, ResNet)
- **Ground Truth**: True annotation data
- **Positive/Negative Sample**: Positive/Negative sample
