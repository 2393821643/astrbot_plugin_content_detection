from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.api.message_components import *
from astrbot.api import logger

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos.cos_comm import CiDetectType


@register("astrbot_plugin_content_detection", "mataHape", "腾讯云CI内容检测", "1.0.0")
class MyPlugin(Star):
    # 判断配置是否完整
    def config_is_complete(self):
        if self.region == "NULL" or self.secret_id == "NULL" or self.secret_key == "NULL" or self.bucket == "NULL":
            return False
        else:
            return True

    # cos_client
    cos_client = None

    def __init__(self, context: Context, config: dict):
        super().__init__(context)  # 调用父类初始化
        self.config = config
        self.secret_id = config.get("secret_id", "NULL") or "NULL"
        self.secret_key = config.get("secret_key", "NULL") or "NULL"
        self.region = config.get("region", "NULL") or "NULL"
        self.bucket = config.get("bucket", "NULL") or "NULL"
        cos_config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        self.cos_client = CosS3Client(cos_config)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    # 图片检测入口
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def check_image(self, event: AstrMessageEvent):
        # 是否需要图片检测
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
        else:
            yield event.plain_result("开始进行图片检测")

        # 判断配置完整型
        if not self.config_is_complete():
            yield event.plain_result("插件配置不完全，请检查插件配置")
            return

        try:
            # 发送请求
            response = self.cos_client.get_object_sensitive_content_recognition(
                Bucket=self.bucket,
                DetectUrl=first_image_url,
            )
            logger.info(response)
            # 提取分数
            ads_score = response['AdsInfo']['Score']
            politics_score = response['PoliticsInfo']['Score']
            porn_score = response['PornInfo']['Score']
            terrorism_score = response['TerrorismInfo']['Score']
            # 添加结果到消息列表
            # 在 aiocqhttp 消息适配器中，对于 plain 类型的消息，在发送中会使用 strip() 方法去除空格及换行符，可以在消息前后添加零宽空格 \u200b 以解决这个问题。
            result_msg_list = []
            result_msg_list.append(Image.fromURL(first_image_url))
            result_msg_list.append(Plain(f"广告：{ads_score} \u200b\n\u200b"))
            result_msg_list.append(Plain(f"违规：{politics_score} \u200b\n\u200b"))
            result_msg_list.append(Plain(f"涩情：{porn_score} \u200b\n\u200b"))
            result_msg_list.append(Plain(f"暴力：{terrorism_score} \u200b\n\u200b"))
            result_msg_list.append(Plain(f"0~60分表示图片正常，60~90分表示图片疑似敏感，90~100分确定敏感"))

            yield event.chain_result(result_msg_list)
        except Exception as e:
            logger.error(f"COS检测请求失败: {e}")
            yield event.plain_result(f"图片检测请求出错，请检查配置是否正确")

