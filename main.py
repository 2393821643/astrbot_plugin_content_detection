import asyncio
import re
from pathlib import Path
from uuid import uuid4

import aiohttp
from qcloud_cos import CosConfig, CosS3Client

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import *
from astrbot.api.star import Context, Star, register
from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .cos_tool import image_detection
from .encrypt_tool import decrypt_image, encrypt_image
from .phantom_tank_tool import create_phantom_tank


@register(
    "astrbot_plugin_content_detection",
    "mataHape",
    "图片检测、加密和幻影坦克制作",
    "2.0.2",
)
class MyPlugin(Star):
    # 判断配置是否完整
    def config_is_complete(self):
        if (
            self.region == "NULL"
            or self.secret_id == "NULL"
            or self.secret_key == "NULL"
            or self.bucket == "NULL"
        ):
            return False
        else:
            return True

    # cos_client
    cos_client = None

    def __init__(self, context: Context, config: dict):
        super().__init__(context)  # 调用父类初始化
        self.config = config
        # 获取腾讯云配置
        self.open_content_detection = (
            config.get("cos_config", "{}").get("open_content_detection", True) or True
        )
        self.secret_id = (
            config.get("cos_config", "{}").get("secret_id", "NULL") or "NULL"
        )
        self.secret_key = (
            config.get("cos_config", "{}").get("secret_key", "NULL") or "NULL"
        )
        self.region = config.get("cos_config", "{}").get("region", "NULL") or "NULL"
        self.bucket = config.get("cos_config", "{}").get("bucket", "NULL") or "NULL"
        cos_config = CosConfig(
            Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key
        )
        self.cos_client = CosS3Client(cos_config)
        # 获取敏感保护配置
        sensitive_config = config.get("sensitive_protection", {})
        self.open_sensitive_protection = sensitive_config.get(
            "open_sensitive_protection", True
        )
        self.sensitive_score = sensitive_config.get("sensitive_score", 90)
        # 噪点等级
        self.noise_level = config.get("noise_level", 5)
        # 图片大小
        self.image_size = config.get("image_size", 16.0)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    # 图片检测入口
    @filter.event_message_type(EventMessageType.ALL)
    async def check_image(self, event: AstrMessageEvent):
        # 是否需要图片检测
        if not self.open_content_detection:
            yield event.plain_result("未开启图片检测")
            return
        # 判断配置完整型
        if not self.config_is_complete():
            yield event.plain_result("插件配置不完全，请检查插件配置")
            return

        need_check = False
        # 是否已有第一张图片
        first_image_url = None
        # 获取消息链
        message_chain = event.get_messages()

        for message_info in message_chain:
            # 检测消息是否含有 图片检测 这个字段 有就触发检查
            if message_info.type == "Plain" and message_info.text == "图片检测":
                need_check = True
            elif message_info.type == "Image":
                # 检测消息是否含有图片 有就记录第一张图片
                if first_image_url is None:
                    first_image_url = message_info.url
                else:
                    continue
            elif message_info.type == "Reply":
                # 检测消息是否引用其他消息 有就读取引用消息的第一张图片
                # 读取引用消息的消息链
                reply_message_chain = message_info.chain
                for reply_message_chain_info in reply_message_chain:
                    if reply_message_chain_info.type == "Image":
                        first_image_url = reply_message_chain_info.url
                        break

        # 判断是否需要检测提示
        if not need_check:
            return
        elif need_check and first_image_url is None:
            yield event.plain_result("未检测到图片")
            return
        try:
            image_size_bytes = await self._get_image_size(first_image_url)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            logger.error(f"获取图片大小失败: {e}")
            yield event.plain_result("无法获取图片大小，请检查图片链接或稍后重试")
            return

        megabyte = 1024 * 1024
        if image_size_bytes > self.image_size * megabyte:
            yield event.plain_result(
                f"当前图片大小超过设定大小，当前图片大小{image_size_bytes / megabyte:.2f}MB"
            )
            return
        if image_size_bytes >= 5 * megabyte:
            yield event.plain_result("开始进行图片检测，图片超过5MB，检测将会缓慢")
        else:
            yield event.plain_result("开始进行图片检测")

        try:
            # 发送请求
            response = await self._run_image_processing(
                image_detection,
                cos_client=self.cos_client,
                bucket=self.bucket,
                image_url=first_image_url,
                image_size_bytes=image_size_bytes,
            )
            logger.info(response)
            needs_protection = self.open_sensitive_protection and any(
                float(response[key]) >= self.sensitive_score
                for key in (
                    "ads_score",
                    "politics_score",
                    "porn_score",
                    "terrorism_score",
                )
            )
            # 添加结果到消息列表
            # 在 aiocqhttp 消息适配器中，对于 plain 类型的消息，在发送中会使用 strip() 方法去除空格及换行符，可以在消息前后添加零宽空格 \u200b 以解决这个问题。
            result_msg_list = []
            result_msg_list.append(
                Plain(f"广告：{response['ads_score']} \u200b\n\u200b")
            )
            result_msg_list.append(
                Plain(f"违规：{response['politics_score']} \u200b\n\u200b")
            )
            result_msg_list.append(
                Plain(f"涩情：{response['porn_score']} \u200b\n\u200b")
            )
            result_msg_list.append(
                Plain(f"暴力：{response['terrorism_score']} \u200b\n\u200b")
            )
            result_msg_list.append(
                Plain("0~60分表示图片正常，60~90分表示图片疑似敏感，90~100分确定敏感")
            )

            if needs_protection:
                result_msg_list.append(
                    Plain(
                        "\u200b\n\u200b当前图片分数超过设定值，已生成幻影坦克，请点击查看"
                    )
                )
                await self._send_phantom_tank(
                    event, first_image_url, extra_components=result_msg_list
                )
            else:
                result_msg_list.insert(0, Image.fromURL(first_image_url))
                yield event.chain_result(result_msg_list)
        except Exception as e:
            logger.error(f"COS检测请求失败: {e}")
            yield event.plain_result("图片检测请求出错，请检查配置是否正确")

    # 图片加密入口
    @filter.event_message_type(EventMessageType.ALL)
    async def image_encrypt(self, event: AstrMessageEvent):
        # 是否需要图片加密
        need_encrypt = False
        # 是否已有第一张图片
        first_image_url = None
        # 获取消息链
        message_chain = event.get_messages()

        for message_info in message_chain:
            # 检测消息是否含有 图片检测 这个字段 有就触发检查
            if message_info.type == "Plain" and message_info.text == "图片加密":
                need_encrypt = True
            elif message_info.type == "Image":
                # 检测消息是否含有图片 有就记录第一张图片
                if first_image_url is None:
                    first_image_url = message_info.url
                else:
                    continue
            elif message_info.type == "Reply":
                # 检测消息是否引用其他消息 有就读取引用消息的第一张图片
                # 读取引用消息的消息链
                reply_message_chain = message_info.chain or []
                for reply_message_chain_info in reply_message_chain:
                    if reply_message_chain_info.type == "Image":
                        first_image_url = reply_message_chain_info.url
                        break

        # 判断是否需要检测提示
        if not need_encrypt:
            return
        elif need_encrypt and first_image_url is None:
            yield event.plain_result("未检测到图片")
            return
        else:
            yield event.plain_result("开始进行图片加密")

        await self._process_image(event, first_image_url, decrypt=False)

    # 图片解密入口
    @filter.event_message_type(EventMessageType.ALL)
    async def image_decrypt(self, event: AstrMessageEvent):
        need_decrypt = False
        first_image_url = None

        for message_info in event.get_messages():
            if message_info.type == "Plain" and message_info.text == "图片解密":
                need_decrypt = True
            elif message_info.type == "Image" and first_image_url is None:
                first_image_url = message_info.url
            elif message_info.type == "Reply":
                for reply_message in message_info.chain or []:
                    if reply_message.type == "Image":
                        first_image_url = reply_message.url
                        break

        if not need_decrypt:
            return
        if first_image_url is None:
            yield event.plain_result("未检测到图片")
            return

        yield event.plain_result("开始进行图片解密")
        await self._process_image(event, first_image_url, decrypt=True)

    async def _process_image(
        self, event: AstrMessageEvent, first_image_url: str, decrypt: bool
    ):
        operation = "decrypt" if decrypt else "encrypt"
        action = "解密" if decrypt else "加密"
        plugin_data_path = (
            Path(get_astrbot_data_path())
            / "plugin_data"
            / "astrbot_plugin_content_detection"
        )
        source_path = plugin_data_path / f"{uuid4()}.img"
        output_path = source_path.with_name(f"{source_path.stem}_{operation}.png")
        phantom_path = output_path.with_name(f"{output_path.stem}_phantom_tank.png")
        temporary_paths = [source_path, output_path]
        if decrypt:
            temporary_paths.append(phantom_path)

        try:
            plugin_data_path.mkdir(parents=True, exist_ok=True)
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                await self._download_image(session, first_image_url, source_path)

            transform = decrypt_image if decrypt else encrypt_image
            await self._run_image_processing(transform, source_path)

            send_path = output_path
            if decrypt:
                await self._run_image_processing(
                    create_phantom_tank,
                    output_path,
                    Path(__file__).with_name("def.png"),
                    phantom_path,
                    noise_strength=self.noise_level,
                )
                send_path = phantom_path

            result_msg_list = [Image.fromFileSystem(str(send_path))]
            await event.send(event.chain_result(result_msg_list))
        except Exception as e:
            logger.error(f"图片{action}失败: {e}")
            await event.send(
                event.plain_result(f"图片{action}失败，请检查图片链接和格式")
            )
        finally:
            for image_path in temporary_paths:
                try:
                    image_path.unlink(missing_ok=True)
                except OSError as e:
                    logger.warning(f"清理图片临时文件失败 {image_path.name}: {e}")

    @staticmethod
    async def _get_image_size(image_url: str) -> int:
        """Probe total bytes with a one-byte range, without reading the body."""
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(
            timeout=timeout, auto_decompress=False
        ) as session:
            async with session.get(
                image_url,
                headers={"Range": "bytes=0-0", "Accept-Encoding": "identity"},
                read_until_eof=False,
            ) as response:
                try:
                    response.raise_for_status()
                    if response.status == 206:
                        content_range = response.headers.get("Content-Range", "")
                        match = re.fullmatch(
                            r"bytes\s+0-0/([1-9]\d*)",
                            content_range.strip(),
                            re.IGNORECASE,
                        )
                        if match:
                            return int(match.group(1))
                    elif response.status == 200:
                        # Some servers ignore Range and expose the full length instead.
                        content_type = response.headers.get("Content-Type", "").lower()
                        content_length = response.headers.get("Content-Length", "")
                        encoding = response.headers.get("Content-Encoding", "identity")
                        if (
                            not content_type.startswith(("text/", "application/json"))
                            and encoding.lower() == "identity"
                            and content_length.isdecimal()
                            and int(content_length) > 0
                        ):
                            return int(content_length)
                    raise ValueError("服务器未返回有效的图片总大小")
                finally:
                    response.close()

    @staticmethod
    async def _download_image(
        session: aiohttp.ClientSession, image_url: str, image_path: Path
    ):
        async with session.get(image_url) as response:
            response.raise_for_status()
            with image_path.open("wb") as image_file:
                async for chunk in response.content.iter_chunked(64 * 1024):
                    image_file.write(chunk)

    @staticmethod
    async def _run_image_processing(transform, *args, **kwargs):
        processing_task = asyncio.create_task(
            asyncio.to_thread(transform, *args, **kwargs)
        )
        try:
            return await asyncio.shield(processing_task)
        except asyncio.CancelledError:
            # Wait for the worker before removing files it may still be writing.
            try:
                await processing_task
            finally:
                raise

    # 幻影坦克入口
    @filter.event_message_type(EventMessageType.ALL)
    async def image_phantom_tank(self, event: AstrMessageEvent):
        need_phantom_tank = False
        invisible_img_url = None  # 里图
        visible_img_url = None  # 表图
        direct_image_urls = []

        for message_info in event.get_messages():
            if message_info.type == "Plain" and message_info.text == "幻影坦克":
                need_phantom_tank = True
            elif message_info.type == "Reply" and invisible_img_url is None:
                for reply_message in message_info.chain or []:
                    if reply_message.type == "Image":
                        invisible_img_url = reply_message.url
                        break
            elif message_info.type == "Image" and message_info.url:
                direct_image_urls.append(message_info.url)

        if not need_phantom_tank:
            return
        if invisible_img_url is None and direct_image_urls:
            invisible_img_url = direct_image_urls.pop(0)
        if direct_image_urls:
            visible_img_url = direct_image_urls[0]
        if invisible_img_url is None:
            yield event.plain_result("未检测到图片作为里图")
            return

        yield event.plain_result("开始进行幻影坦克制作")
        await self._send_phantom_tank(event, invisible_img_url, visible_img_url)

    async def _send_phantom_tank(
        self,
        event: AstrMessageEvent,
        invisible_img_url: str,
        visible_img_url: str | None = None,
        extra_components: list | None = None,
    ):
        """Build and send a tank with optional results, then clean temporary files."""
        plugin_data_path = (
            Path(get_astrbot_data_path())
            / "plugin_data"
            / "astrbot_plugin_content_detection"
        )
        request_id = uuid4()
        invisible_path = plugin_data_path / f"{request_id}_invisible.img"
        visible_download_path = plugin_data_path / f"{request_id}_visible.img"
        output_path = plugin_data_path / f"{request_id}_phantom_tank.png"
        visible_path = (
            visible_download_path
            if visible_img_url
            else Path(__file__).with_name("def.png")
        )
        temporary_paths = [invisible_path, output_path]
        if visible_img_url:
            temporary_paths.append(visible_download_path)

        try:
            plugin_data_path.mkdir(parents=True, exist_ok=True)
            if not visible_img_url and not visible_path.is_file():
                raise FileNotFoundError("插件目录缺少默认表图 def.png")
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                await self._download_image(session, invisible_img_url, invisible_path)
                if visible_img_url:
                    await self._download_image(session, visible_img_url, visible_path)

            await self._run_image_processing(
                create_phantom_tank,
                invisible_path,
                visible_path,
                output_path,
                noise_strength=self.noise_level,
            )
            result_msg_list = [Image.fromFileSystem(str(output_path))]
            if extra_components:
                result_msg_list.extend(extra_components)
            await event.send(event.chain_result(result_msg_list))
        except Exception as e:
            logger.error(f"幻影坦克制作失败: {e}")
            await event.send(
                event.plain_result(
                    "幻影坦克制作失败，请检查图片链接、格式及默认表图 def.png"
                )
            )
        finally:
            for image_path in temporary_paths:
                try:
                    image_path.unlink(missing_ok=True)
                except OSError as e:
                    logger.warning(f"清理幻影坦克临时文件失败 {image_path.name}: {e}")
