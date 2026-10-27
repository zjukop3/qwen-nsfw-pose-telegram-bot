"""Async ComfyUI API client for queueing prompts and retrieving images.

This module talks directly to a running ComfyUI server's HTTP API.
It is designed to work with the workflow JSONs from the main project
(qwen21-nsfw-pose-skill) and provides a convenience builder for a
basic Qwen-Image text-to-image workflow.
"""

from __future__ import annotations

import asyncio
import random
import uuid
from dataclasses import dataclass, field
from typing import Any

import aiohttp

DEFAULT_TIMEOUT = 300  # seconds
POLL_INTERVAL = 1.5    # seconds


@dataclass
class GenerationResult:
    """Holds the result of a single image generation request."""

    prompt_id: str
    images: list[bytes] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ComfyUIClient:
    """Async client that communicates with a ComfyUI server.

    Usage::

        client = ComfyUIClient("http://127.0.0.1:8188")
        result = await client.generate(workflow_json)
        for img_bytes in result.images:
            # send to Telegram, save to disk, etc.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8188") -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = str(uuid.uuid4())

    # -- public API --------------------------------------------------------

    async def queue_prompt(
        self,
        workflow: dict[str, Any],
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """Submit a workflow JSON to ``/prompt`` and return the ``prompt_id``."""
        payload = {"prompt": workflow, "client_id": self.client_id}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["prompt_id"]

    async def get_history(self, prompt_id: str) -> dict[str, Any]:
        """Fetch ``/history/{prompt_id}``; returns empty dict if not finished."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/history/{prompt_id}"
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get(prompt_id, {})

    async def get_image(
        self,
        filename: str,
        subfolder: str = "",
        folder_type: str = "output",
    ) -> bytes:
        """Download a generated image via ``/view``."""
        params: dict[str, str] = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/view", params=params
            ) as resp:
                resp.raise_for_status()
                return await resp.read()

    async def wait_for_result(
        self,
        prompt_id: str,
        timeout: int = DEFAULT_TIMEOUT,
        poll_interval: float = POLL_INTERVAL,
    ) -> GenerationResult:
        """Poll ``/history`` until the job finishes, then download all images."""
        elapsed = 0.0
        while elapsed < timeout:
            history = await self.get_history(prompt_id)
            if history:
                images: list[bytes] = []
                outputs = history.get("outputs", {})
                for _node_id, node_out in outputs.items():
                    for img_info in node_out.get("images", []):
                        img_bytes = await self.get_image(
                            img_info["filename"],
                            img_info.get("subfolder", ""),
                            img_info.get("type", "output"),
                        )
                        images.append(img_bytes)
                return GenerationResult(
                    prompt_id=prompt_id,
                    images=images,
                    metadata=history,
                )
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"ComfyUI job {prompt_id} did not finish within {timeout}s"
        )

    async def generate(
        self,
        workflow: dict[str, Any],
        timeout: int = DEFAULT_TIMEOUT,
    ) -> GenerationResult:
        """Convenience method: queue + wait + return images."""
        prompt_id = await self.queue_prompt(workflow, timeout=timeout)
        return await self.wait_for_result(prompt_id, timeout=timeout)


# -- workflow builder --------------------------------------------------------


def build_basic_workflow(
    prompt_text: str,
    negative_prompt: str = "",
    seed: int = -1,
    steps: int = 50,
    cfg: float = 2.5,
    sampler: str = "euler_ancestral",
    scheduler: str = "karras",
    width: int = 832,
    height: int = 1216,
    lora_name: str = "",
    lora_strength: float = 1.0,
) -> dict[str, Any]:
    """Build a minimal ComfyUI workflow JSON for Qwen-Image text-to-image.

    This is a skeleton workflow. Adjust checkpoint name, LoRA names, and
    node parameters to match your ComfyUI installation and the main project's
    verified recipes from
    https://github.com/Arekejoker/qwen21-nsfw-pose-skill
    """
    actual_seed = seed if seed >= 0 else random.randint(0, 2**32 - 1)

    # Node 3 (KSampler) model input depends on whether LoRA is used
    model_input: list[Any] = ["4", 0] if not lora_name else ["10", 0]

    workflow: dict[str, Any] = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": actual_seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1.0,
                "model": model_input,
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "qwen_image_2.1_int8_convrot.safetensors",
            },
        },
        "5": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt_text, "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["4", 1]},
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "qwen_pose_bot",
            },
        },
    }

    if lora_name:
        workflow["10"] = {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["4", 0],
                "clip": ["4", 1],
                "lora_name": lora_name,
                "strength_model": lora_strength,
                "strength_clip": lora_strength,
            },
        }

    return workflow
