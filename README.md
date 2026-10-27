# qwen-nsfw-pose-telegram-bot

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Main Project](https://img.shields.io/badge/main%20project-qwen21--nsfw--pose--skill-orange.svg)](https://github.com/Arekejoker/qwen21-nsfw-pose-skill)
[![Stars](https://img.shields.io/badge/main%20%E2%98%85-3361-brightgreen.svg)](https://github.com/Arekejoker/qwen21-nsfw-pose-skill)

> 🤖 Telegram Bot 附属项目 — 基于 [Arekejoker/qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill) 的 Telegram 出图机器人封装

---

## 中文说明

### 为什么有这个项目？

主项目 [qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill)（⭐ 3361）提供了完整的 Qwen-Image 2.1 NSFW / 姿势出图配方，面向 Claude Code / Codex / Cursor 等 agent 技能场景和人类手动使用。本项目将其封装为 **Telegram Bot**，让你在手机上也能随时发文字出图、选 3D 人偶姿势、切换 L0–L3 大胆度等级。

### 特性

- 📱 **Telegram 原生交互** — 文字出图、InlineKeyboard 选姿势、按钮切等级
- 🎭 **136 姿势库接入** — 复用主项目 VNCCS 人偶姿势 JSON，Inline 按钮翻页选择
- 🔢 **L0–L3 分级控制** — 全着装 → 湿身泳装 → 极低机位大胆姿态，一键切换
- 🖼️ **ComfyUI API 直连** — 异步队列提交 + 轮询，支持并发出图
- ⚙️ **配置灵活** — 环境变量 / `.env` 一键配置 ComfyUI 地址与 Bot Token
- 🔧 **骨架可扩展** — 清晰的模块划分，方便接入主项目完整配方

### 安装

```bash
git clone https://github.com/zjukop3/qwen-nsfw-pose-telegram-bot.git
cd qwen-nsfw-pose-telegram-bot
pip install -e .
```

### 前置条件

1. 已部署 ComfyUI 并加载 `qwen_image_2.1_int8_convrot` 底模
2. 已按主项目 [安装指南](https://github.com/Arekejoker/qwen21-nsfw-pose-skill/blob/main/install/setup.md) 配置 NSFW LoRA 与 VNCCS 姿势库
3. 从 [@BotFather](https://t.me/BotFather) 获取 Telegram Bot Token

### 快速上手

```bash
# 1. 配置环境变量
export TELEGRAM_BOT_TOKEN="你的BotFather给的token"
export COMFYUI_URL="http://127.0.0.1:8188"

# 2. 启动机器人
qwen-pose-bot

# 3. 在 Telegram 中操作
#    /start          — 查看帮助
#    /gen 海边日落，少女湿发   — 文字出图
#    /pose           — 选择 3D 人偶姿势
#    /level          — 切换 L0–L3 大胆度等级
```

### 与主项目的关系

本项目是 [Arekejoker/qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill) 的 **生态补充**，不替代主项目。

- ✅ 本项目做：Telegram 交互层封装、Bot 命令路由、Inline UI
- ❌ 本项目不做：提示词配方研发、LoRA 训练、姿势库制作
- 所有提示词配方、LoRA 配置、姿势库版权归主项目所有
- 使用前请先按主项目 [安装指南](https://github.com/Arekejoker/qwen21-nsfw-pose-skill/blob/main/install/setup.md) 部署 ComfyUI 环境

### Roadmap

- [x] 基础文字出图（/gen）
- [x] L0–L3 等级切换（/level）
- [x] ComfyUI 异步客户端
- [x] 姿势选择骨架（/pose）
- [ ] 136 姿势库完整 Inline 选择器（翻页 + 分类）
- [ ] 出图历史与 Seed 复用
- [ ] 多用户队列与速率限制
- [ ] Webhook 模式部署
- [ ] 主项目 `doctor.py` 自检集成

### License

MIT — 见 [LICENSE](LICENSE)

---

## English

### Why this project?

The main project [qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill) (⭐ 3361) provides a complete Qwen-Image 2.1 NSFW / pose generation recipe for agent skills (Claude Code / Codex / Cursor) and manual use. This repo wraps it into a **Telegram Bot** so you can generate images, pick 3D mannequin poses, and switch L0–L3 boldness levels right from your phone.

### Features

- 📱 **Native Telegram UX** — text-to-image, InlineKeyboard pose picker, button level switching
- 🎭 **136-pose library** — reuses the main project's VNCCS pose JSONs
- 🔢 **L0–L3 grading** — clothed → wet swimsuit → daring low-angle, one tap to switch
- 🖼️ **ComfyUI API direct** — async queue + polling, concurrent generation supported
- ⚙️ **Flexible config** — env vars / `.env` for ComfyUI URL and Bot Token
- 🔧 **Extensible skeleton** — clean module separation for integrating full recipes

### Install

```bash
git clone https://github.com/zjukop3/qwen-nsfw-pose-telegram-bot.git
cd qwen-nsfw-pose-telegram-bot
pip install -e .
```

### Prerequisites

1. ComfyUI deployed with `qwen_image_2.1_int8_convrot` base model loaded
2. NSFW LoRA and VNCCS pose library configured per the main project's [setup guide](https://github.com/Arekejoker/qwen21-nsfw-pose-skill/blob/main/install/setup.md)
3. Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Quick Start

```bash
export TELEGRAM_BOT_TOKEN="your-token-from-botfather"
export COMFYUI_URL="http://127.0.0.1:8188"
qwen-pose-bot
```

### Relationship to main project

This is an **ecosystem add-on** for [Arekejoker/qwen21-nsfw-pose-skill](https://github.com/Arekejoker/qwen21-nsfw-pose-skill), not a replacement.

- ✅ This project does: Telegram interaction layer, bot command routing, Inline UI
- ❌ This project does NOT: prompt recipe R&D, LoRA training, pose library creation
- All prompt recipes, LoRA configs, and pose libraries belong to the main project
- Please deploy ComfyUI following the main project's [setup guide](https://github.com/Arekejoker/qwen21-nsfw-pose-skill/blob/main/install/setup.md) first

### Roadmap

- [x] Basic text-to-image (/gen)
- [x] L0–L3 level switching (/level)
- [x] ComfyUI async client
- [x] Pose picker skeleton (/pose)
- [ ] Full 136-pose Inline picker (pagination + categories)
- [ ] Generation history & seed reuse
- [ ] Multi-user queue & rate limiting
- [ ] Webhook deployment mode
- [ ] Main project `doctor.py` self-check integration

### License

MIT — see [LICENSE](LICENSE)