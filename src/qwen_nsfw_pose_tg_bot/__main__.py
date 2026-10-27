"""Telegram bot entry point for Qwen-Image NSFW pose generation.

Wraps the main project's ComfyUI recipes into a conversational Telegram bot.
Run with::

    qwen-pose-bot

(after ``pip install -e .``)

Environment variables:
    TELEGRAM_BOT_TOKEN  — token from @BotFather (required)
    COMFYUI_URL         — ComfyUI server URL (default: http://127.0.0.1:8188)
"""

from __future__ import annotations

import logging
import os
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .comfyui_client import ComfyUIClient, build_basic_workflow

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("qwen-pose-bot")

# ---------------------------------------------------------------------------
# Configuration (env-based; swap for pydantic-settings in production)
# ---------------------------------------------------------------------------

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# L0–L3 boldness levels, mirroring the main project's grading system.
# Adjust lora names to match your ComfyUI models directory.
LORA_MAP: dict[str, dict[str, Any]] = {
    "L0": {"lora": "", "strength": 0.0, "label": "全着装 · 无LoRA"},
    "L1": {"lora": "taws_v13.safetensors", "strength": 1.0, "label": "湿身泳装 · LoRA@1.0"},
    "L2": {"lora": "taws_v13.safetensors", "strength": 1.0, "label": "极低机位 · 大胆姿态"},
    "L3": {"lora": "taws_v13.safetensors", "strength": 1.2, "label": "极限 · LoRA@1.2"},
}

# Skeleton pose list — in production, load 136 poses from the main project's
# VNCCS pose library JSON files.
POSE_LIST: list[tuple[str, str]] = [
    ("01_standing", "站立"),
    ("02_sitting", "坐姿"),
    ("03_squat", "蹲姿"),
    ("04_lying", "躺姿"),
    ("05_back", "背影"),
    ("06_lowangle", "低机位"),
]

# Per-user state (in-memory; replace with Redis/DB for production)
_user_level: dict[int, str] = {}
_user_pose: dict[int, str] = {}

# Shared ComfyUI client
comfy = ComfyUIClient(COMFYUI_URL)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show welcome message and command list."""
    await update.message.reply_text(
        "👋 *Qwen NSFW Pose Bot*\n\n"
        "基于 [qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill) "
        "的 Telegram 出图机器人。\n\n"
        "*命令：*\n"
        "/gen `<提示词>` — 文字出图\n"
        "/pose — 选择 3D 人偶姿势\n"
        "/level — 切换 L0–L3 等级\n"
        "/help — 查看帮助\n",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Alias for /start."""
    await cmd_start(update, ctx)


async def cmd_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show InlineKeyboard for L0–L3 level selection."""
    keyboard = [
        [InlineKeyboardButton("L0 · 全着装", callback_data="lvl_L0")],
        [InlineKeyboardButton("L1 · 湿身泳装", callback_data="lvl_L1")],
        [InlineKeyboardButton("L2 · 极低机位", callback_data="lvl_L2")],
        [InlineKeyboardButton("L3 · 极限", callback_data="lvl_L3")],
    ]
    await update.message.reply_text(
        "选择大胆度等级：", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cmd_pose(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show InlineKeyboard for 3D mannequin pose selection."""
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"pose_{pid}")]
        for pid, label in POSE_LIST
    ]
    await update.message.reply_text(
        "选择 3D 人偶姿势（骨架，更多姿势待接入主项目 136 姿势库）：",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_gen(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate an image from a text prompt via ComfyUI."""
    if not ctx.args:
        await update.message.reply_text(
            "用法：/gen <提示词>\n例：/gen 海边日落，少女湿发"
        )
        return

    prompt_text = " ".join(ctx.args)
    user_id = update.effective_user.id
    level = _user_level.get(user_id, "L0")
    lora_cfg = LORA_MAP[level]

    await update.message.reply_text(
        f"🎨 生成中…\n等级：{level} ({lora_cfg['label']})\n提示词：{prompt_text[:80]}"
    )

    workflow = build_basic_workflow(
        prompt_text=prompt_text,
        negative_prompt="low quality, blurry, deformed, bad anatomy",
        steps=50,
        cfg=2.5,
        lora_name=lora_cfg["lora"],
        lora_strength=lora_cfg["strength"],
    )

    try:
        result = await comfy.generate(workflow, timeout=300)
        if result.images:
            seed_used = workflow["3"]["inputs"]["seed"]
            await update.message.reply_photo(
                photo=result.images[0],
                caption=f"✅ {level} · seed={seed_used}",
            )
        else:
            await update.message.reply_text(
                "⚠️ 生成完成但未返回图片，请检查 ComfyUI 输出节点。"
            )
    except Exception as exc:
        logger.exception("Generation failed")
        await update.message.reply_text(f"❌ 生成失败：{exc}")


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle InlineKeyboard button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("lvl_"):
        level = data[4:]
        _user_level[user_id] = level
        await query.edit_message_text(
            f"✅ 已切换到 {level} ({LORA_MAP[level]['label']})\n"
            f"用 /gen <提示词> 出图即可应用此等级。"
        )

    elif data.startswith("pose_"):
        pose_id = data[5:]
        _user_pose[user_id] = pose_id
        await query.edit_message_text(
            f"已选姿势：{pose_id}\n"
            f"（骨架：姿势 JSON 注入待接入主项目姿势库）\n"
            f"用 /gen <提示词> 出图即可应用此姿势。"
        )


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------


def main() -> None:
    """Build and run the Telegram bot."""
    if not BOT_TOKEN:
        raise SystemExit(
            "❌ 请设置 TELEGRAM_BOT_TOKEN 环境变量。\n"
            "从 @BotFather 获取 token 后：\n"
            "  export TELEGRAM_BOT_TOKEN='your-token'"
        )

    logger.info("ComfyUI URL: %s", COMFYUI_URL)
    logger.info("Starting Telegram bot…")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("gen", cmd_gen))
    app.add_handler(CommandHandler("pose", cmd_pose))
    app.add_handler(CommandHandler("level", cmd_level))
    app.add_handler(CallbackQueryHandler(on_callback))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
