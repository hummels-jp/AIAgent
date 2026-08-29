#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultraman 场景描述 -> 图片生成器

功能：
1. 读取 Ultraman 场景描述中的 AI 绘图提示词（或直接用 prompt）。
2. 调用外部文生图 API 生成图片。
3. 将生成的图片保存到本地。

当前支持三种后端（通过 --backend 或 IMAGE_BACKEND 环境变量切换）：
- "openrouter"    : 调用 OpenRouter 的文生图接口（默认，配置文件：config.json）。
                    支持 OpenRouter 上任意文生图模型，只需修改 config.json 中的 model 字段，
                    例如 qwen/qwen-image-3-pro、google/nano-banana-2 等。
- "google_imagen" : 调用 Google Vertex AI / Google AI Studio 的 Imagen 系列接口
- "generic"       : 调用任意兼容的 HTTP POST 接口

用法示例：
    python scripts/generate_image.py --prompt "Ultraman Tiga fighting Gatanothor" -o tiga.png
    python scripts/generate_image.py --scene scene.txt -o scene.png
    python scripts/generate_image.py --backend google_imagen --prompt "..."
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path

import requests
from requests.exceptions import HTTPError

# ---------------------------------------------------------------------------
# 默认配置（可通过环境变量覆盖）
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.json"

DEFAULT_BACKEND = os.environ.get("IMAGE_BACKEND", "openrouter")
DEFAULT_OUTPUT_DIR = os.environ.get("IMAGE_OUTPUT_DIR", str(SCRIPT_DIR.parent / "outputs"))

# Google Imagen 配置
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID", "")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION", "us-central1")
GOOGLE_IMAGEN_MODEL = os.environ.get("GOOGLE_IMAGEN_MODEL", "imagen-3.0-generate-002")
GOOGLE_ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN", "")  # 或走 gcloud auth

# 通用/自定义接口配置
GENERIC_API_URL = os.environ.get(
    "GENERIC_API_URL",
    "https://api.example.com/v1/images/generate",
)
GENERIC_API_KEY = os.environ.get("GENERIC_API_KEY", "")

# OpenRouter 接口
OPENROUTER_API_URL = os.environ.get(
    "OPENROUTER_API_URL",
    "https://openrouter.ai/api/v1/images/generations",
)


# ---------------------------------------------------------------------------
# 配置文件加载
# ---------------------------------------------------------------------------
def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """加载 config.json 配置文件。"""
    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在：{config_path}\n"
            "请先复制 config.example.json 为 config.json 并填写你的 API Key。"
        )
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def extract_prompt_from_scene(scene_text: str) -> str:
    """
    从 Ultraman 场景描述文本中提取 AI 绘图提示词。
    支持两种格式：
      1. ``` ... ``` 代码块
      2. "AI 绘图提示词：" 之后的文本
    """
    # 优先匹配 ``` 代码块
    code_block_match = re.search(r"```(?:\w*\n)?(.*?)```", scene_text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # 否则匹配 "AI 绘图提示词：" 后的内容（到下一个空行或标题为止）
    label_match = re.search(
        r"AI 绘图提示词[：:]\s*(.*?)(?:\n\n|\n#|---|$)", scene_text, re.DOTALL
    )
    if label_match:
        return label_match.group(1).strip()

    # 兜底：直接返回原文
    return scene_text.strip()


def save_image(data: bytes, output_path: Path) -> Path:
    """将二进制图片数据保存到文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return output_path


def decode_base64_image(b64_string: str) -> bytes:
    """解码 Base64 图片数据，兼容带 data URI 前缀的字符串。"""
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    return base64.b64decode(b64_string)


def fetch_image(url: str) -> bytes:
    """从 URL 下载图片。"""
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.content


# ---------------------------------------------------------------------------
# 后端调用：OpenRouter
# ---------------------------------------------------------------------------
def call_openrouter_api(
    prompt: str,
    config: dict,
    api_url: str = OPENROUTER_API_URL,
    size: str = "1024x1024",
    quality: str = "",
    n: int = 1,
) -> bytes:
    """
    调用 OpenRouter 文生图接口。
    文档：https://openrouter.ai/docs#image-generation

    支持 OpenRouter 上任意文生图模型：只需在 config.json 的 openrouter.model 中修改模型名称。
    不同模型可搭配不同的 size / quality，也可在 config.json 的 openrouter 段落中预置默认值。
    """
    openrouter_cfg = config.get("openrouter", {})
    api_key = openrouter_cfg.get("api_key") or os.environ.get("OPENROUTER_API_KEY", "")
    model = openrouter_cfg.get("model") or os.environ.get("OPENROUTER_MODEL", "qwen/qwen-image-3-pro")
    site_url = openrouter_cfg.get("site_url", "")
    site_name = openrouter_cfg.get("site_name", "Ultraman Scene Generator")

    if not api_key or api_key == "sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        raise ValueError(
            "缺少 OpenRouter API Key。请在 config.json 的 openrouter.api_key 中填写，"
            "或设置 OPENROUTER_API_KEY 环境变量。"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-Title"] = site_name

    payload = {
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size,
    }
    if quality:
        payload["quality"] = quality

    response = requests.post(api_url, headers=headers, json=payload, timeout=300)
    try:
        response.raise_for_status()
    except HTTPError as exc:
        print(f"[OpenRouter API Error] status={response.status_code}", file=sys.stderr)
        print(f"[Response Body] {response.text}", file=sys.stderr)
        raise exc

    result = response.json()
    data_list = result.get("data", [])
    if not data_list:
        raise RuntimeError(f"OpenRouter 返回空结果：{result}")

    image_item = data_list[0]

    # OpenRouter / OpenAI 格式通常返回 url 或 b64_json
    if "url" in image_item and image_item["url"]:
        return fetch_image(image_item["url"])
    if "b64_json" in image_item and image_item["b64_json"]:
        return decode_base64_image(image_item["b64_json"])

    raise RuntimeError(f"无法从 OpenRouter 响应中解析图片：{image_item}")


# ---------------------------------------------------------------------------
# 后端调用：Google Imagen
# ---------------------------------------------------------------------------
def call_google_imagen(
    prompt: str,
    project_id: str = GOOGLE_PROJECT_ID,
    location: str = GOOGLE_LOCATION,
    model_id: str = GOOGLE_IMAGEN_MODEL,
    access_token: str = GOOGLE_ACCESS_TOKEN,
    aspect_ratio: str = "16:9",
    sample_count: int = 1,
) -> bytes:
    """
    调用 Google Vertex AI 的 Imagen 模型生成图片。
    文档：https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images
    """
    if not project_id:
        raise ValueError("缺少 GOOGLE_PROJECT_ID，请设置环境变量。")
    if not access_token:
        raise ValueError("缺少 GOOGLE_ACCESS_TOKEN，请设置环境变量或运行 gcloud auth。")

    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": sample_count,
            "aspectRatio": aspect_ratio,
            "safetyFilterLevel": "block_some",
            "personGeneration": "allow_adult",
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    result = response.json()
    predictions = result.get("predictions", [])
    if not predictions:
        raise RuntimeError(f"Imagen 返回空结果：{result}")

    image_b64 = predictions[0].get("bytesBase64Encoded") or predictions[0].get("image")
    if not image_b64:
        raise RuntimeError(f"无法从 Imagen 响应中解析图片：{predictions[0]}")

    return decode_base64_image(image_b64)


# ---------------------------------------------------------------------------
# 后端调用：通用 HTTP 接口
# ---------------------------------------------------------------------------
def call_generic_api(
    prompt: str,
    api_url: str = GENERIC_API_URL,
    api_key: str = GENERIC_API_KEY,
    width: int = 1024,
    height: int = 576,
    num_inference_steps: int = 28,
    guidance_scale: float = 7.5,
) -> bytes:
    """
    调用任意兼容的 HTTP 图片生成接口。
    默认请求/响应格式参考常见的文生图服务：
      请求：{"prompt": "...", "width": 1024, "height": 576, ...}
      响应：{"image": "base64..."} 或 {"images": ["base64..."]}
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=300)
    response.raise_for_status()

    result = response.json()

    image_b64 = None
    for key in ("image", "images", "output", "result"):
        value = result.get(key)
        if value:
            if isinstance(value, list):
                image_b64 = value[0]
            else:
                image_b64 = value
            break

    if not image_b64:
        raise RuntimeError(f"无法从通用接口响应中解析图片：{result}")

    return decode_base64_image(image_b64)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="根据 Ultraman 场景描述生成图片。",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="直接传入英文绘图提示词。",
    )
    parser.add_argument(
        "--scene",
        type=str,
        help="传入 Ultraman 场景描述文件路径，自动提取其中的 AI 绘图提示词。",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="输出图片路径，默认为 outputs/<timestamp>.png。",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=DEFAULT_BACKEND,
        choices=["openrouter", "google_imagen", "generic"],
        help="图片生成后端（默认 openrouter）。",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="配置文件路径（默认 scripts/config.json）。",
    )
    parser.add_argument(
        "--size",
        type=str,
        default=None,
        help="(OpenRouter) 图片尺寸，如 1024x1024、1024x1536、1536x1024；"
             "未指定时使用 config.json 中的 openrouter.size。",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default=None,
        help="(OpenRouter) 图片质量，如 standard、hd；"
             "未指定时使用 config.json 中的 openrouter.quality。",
    )
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        default="16:9",
        help="(Imagen) 图片宽高比。",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="(通用接口) 图片宽度。",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=576,
        help="(通用接口) 图片高度。",
    )

    args = parser.parse_args()

    # 1. 获取 prompt
    if args.prompt:
        prompt = args.prompt.strip()
    elif args.scene:
        scene_path = Path(args.scene)
        if not scene_path.exists():
            print(f"错误：场景文件不存在 {scene_path}", file=sys.stderr)
            return 1
        scene_text = scene_path.read_text(encoding="utf-8")
        prompt = extract_prompt_from_scene(scene_text)
    else:
        scene_text = sys.stdin.read()
        if not scene_text.strip():
            print("错误：请提供 --prompt、--scene 或从 stdin 输入场景描述。", file=sys.stderr)
            return 1
        prompt = extract_prompt_from_scene(scene_text)

    print(f"[提示词] {prompt}\n")

    # 2. 调用后端生成图片
    if args.backend == "openrouter":
        config = load_config(Path(args.config))
        openrouter_cfg = config.get("openrouter", {})
        effective_size = args.size or openrouter_cfg.get("size", "1024x1024")
        effective_quality = args.quality or openrouter_cfg.get("quality", "")
        image_bytes = call_openrouter_api(
            prompt=prompt,
            config=config,
            size=effective_size,
            quality=effective_quality,
        )
    elif args.backend == "google_imagen":
        image_bytes = call_google_imagen(
            prompt=prompt,
            aspect_ratio=args.aspect_ratio,
        )
    else:
        image_bytes = call_generic_api(
            prompt=prompt,
            width=args.width,
            height=args.height,
        )

    # 3. 保存图片
    if args.output:
        output_path = Path(args.output)
    else:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(DEFAULT_OUTPUT_DIR) / f"ultraman_{timestamp}.png"

    saved_path = save_image(image_bytes, output_path)
    print(f"[已保存] {saved_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
