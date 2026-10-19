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

