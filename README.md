# astrbot_plugin_content_detection

AstrBot 插件模板 / A template plugin for AstrBot plugin feature

> [!NOTE]
> This repo is just a template of [AstrBot](https://github.com/AstrBotDevs/AstrBot) Plugin.
> 
> [AstrBot](https://github.com/AstrBotDevs/AstrBot) is an agentic assistant for both personal and group conversations. It can be deployed across dozens of mainstream instant messaging platforms, including QQ, Telegram, Feishu, DingTalk, Slack, LINE, Discord, Matrix, etc. In addition, it provides a reliable and extensible conversational AI infrastructure for individuals, developers, and teams. Whether you need a personal AI companion, an intelligent customer support agent, an automation assistant, or an enterprise knowledge base, AstrBot enables you to quickly build AI applications directly within your existing messaging workflows.

# Supports

- [AstrBot Repo](https://github.com/AstrBotDevs/AstrBot)

- [AstrBot Plugin Development Docs (Chinese)](https://docs.astrbot.app/dev/star/plugin-new.html)

- [AstrBot Plugin Development Docs (English)](https://docs.astrbot.app/en/dev/star/plugin-new.html)

  

# 图片内容检测

描述：利用腾讯云CI对图片进行打分

# 图片加密与解密

群聊发送 `图片加密` 或 `图片解密`，同时附带一张图片，也可以引用包含图片的消息。
使用希尔伯特曲线重排像素，无需密钥，仅支持静态图片。

图片按 UUID 命名并临时保存到 `data/plugin_data/astrbot_plugin_content_detection/`，
处理结果使用 `_encrypt.png` 或 `_decrypt.png` 后缀。发送完成后删除下载文件和处理结果；
下载、处理或发送失败时也会清理临时文件。

解密时请使用未压缩、未缩放的加密 PNG 原图，平台压缩或缩放会影响还原。

# 棋盘格幻影坦克

群聊发送 `幻影坦克` 并附带图片。两张图片依次作为里图、表图；也可以引用一张里图，
再附带一张表图。只提供里图时，使用插件目录中的 `def.png` 作为表图。

输出为灰度棋盘格透明 PNG：白色背景显示表图，黑色背景显示里图。
表图缩放至里图分辨率，里图在合成前加入高斯噪点，强度由插件配置 `noise_level` 控制，
范围为 `0–10`，默认 `5`，设为 `0` 可关闭噪点。
请保留 PNG 原图和透明通道，避免平台转换格式或缩放破坏棋盘格。

下载文件和生成结果保存在插件数据目录，发送完成或发生错误后清理，`def.png` 保留。

# 环境准备

在Astrbot运行的python环境中安装cos-python-sdk-v5

```
 pip install -U cos-python-sdk-v5
```

如果你是使用虚拟环境运行Astrbot,请在该虚拟环境中安装cos-python-sdk-v5

以下 以LLBOT中的虚拟环境运行的Astrbot为例

在 {llbot安装的位置}\bin\astrbot中cmd

```
.venv\Scripts\activate.bat
```

此时进入虚拟环境

在虚拟环境中输入

```
pip install -U cos-python-sdk-v5
```

