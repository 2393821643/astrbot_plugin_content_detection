# 图片检测、加密和幻影坦克制作

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Python 3.10+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-4.0%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-mataHape-blue)](https://github.com/Zhalslar)

## 1:介绍

本插件用于AstrBot 

- 可将AstrBot 图片通过腾讯云COS进行图片检测；

- 通过希尔伯特曲线混淆对AstrBot 图片进行加密/解密；


- 可对AstrBot 图片进行幻影坦克制作


## 2:安装说明

> [!CAUTION]
>
> 注：由于AstrBot4.26后对底层代码进行修改，本插件无法在AstrBot4.26及其以上使用。后续插件将会适配

在Astrbot运行的python环境中安装cos-python-sdk-v5

```
 pip install -U cos-python-sdk-v5
```



如果你是使用虚拟环境运行Astrbot,请在该虚拟环境中安装cos-python-sdk-v5

以下 以LLBOT中的虚拟环境运行的Astrbot为例

在 {llbot安装的位置}\bin\astrbot中进入cmd

```
.venv\Scripts\activate.bat
```

此时进入虚拟环境

在虚拟环境中输入

```
pip install -U cos-python-sdk-v5
```



## 3:腾讯云图片检测快速使用

### 3.1:创建密钥

在[](https://console.cloud.tencent.com/cam/capi)中登录后创建密钥

这里图省事直接使用主账号API访问密钥

![](https://www.matahape.cn/minio/share/github/QQ20261020-010218.png)

点击继续使用后，将出现SecretId和SecretKey,这里请记录这2个值，否则后续找不到只能重新创建。勾选“我已知晓并保存SecretKey”后点击确认。到这里密钥就创建完毕。请保管好你的密钥防止泄露，你也不想你的密钥被别人刷吧。

![](https://www.matahape.cn/minio/share/github/QQ20261020-010757.png)

### 3.2:创建桶

在[](https://console.cloud.tencent.com/cos5/bucket)中创建桶，点击创建存储桶，进入创建页面

![](https://www.matahape.cn/minio/share/github/QQ20261020-012901.png)

在创建页面中，输入名称；

存储桶地域推荐选择国内；

数据冗余策略选择"单AZ存储"；

访问权限选择"公有读私有写"

![](https://www.matahape.cn/minio/share/github/QQ20261020-013507.png)

点击创建后，完成桶的创建

请记录你的桶名称和存储桶地域，插件后面需要使用

以下是常用存储桶地域的地域 ID

| **地域** | **地域 ID**  |
| -------- | ------------ |
| 北京     | ap-beijing   |
| 上海     | ap-shanghai  |
| 南京     | ap-nanjing   |
| 广州     | ap-guangzhou |
| 成都     | ap-chengdu   |
| 重庆     | ap-chongqing |
| 中国香港 | ap-hongkong  |

其他地域ID请在[](https://cloud.tencent.com/document/product/213/6091)中查找

## 4:配置说明

| 配置项目             | 配置值                 | 配置描述                                                     |
| -------------------- | ---------------------- | ------------------------------------------------------------ |
| 是否开启内容审核     | 开/关                  | 开启后,可进行内容审核                                        |
| SecretId             | 例：AB123cd456         | 密钥                                                         |
| SecretKey            | 例：AbcdEFg            | 密钥                                                         |
| region               | 例：ap-beijing         | 存储桶地域ID                                                 |
| bucket               | 例：test-bucket-123456 | 存储桶名称 注意：-后面的数字也要                             |
| 是否开启敏感保护     | 开/关                  | 是否开启敏感保护 开启敏感保护后，如果图片检测的分数超过敏感分数，则通过幻影坦克展示 |
| 敏感分数             | 0~100 默认90           | 0~60分表示图片正常，60~90分表示图片疑似敏感，90~100分确定敏感 |
| 噪点等级             | 0~10 默认5             | 这是幻影坦克的噪点。等级越高，噪点越多                       |
| 图片检测文件大小限制 | 5~32 默认16            | 超过图片文件大小将不被检测,单位MB                            |

![](https://www.matahape.cn/minio/share/github/QQ20261020-014336.png)

![](https://www.matahape.cn/minio/share/github/QQ20261020-221246.png)

## 5:命令

### 5.1:图片检测

描述：对图片进行检测

命令： 图片+图片检测 / 图片检测+图片 /  引用+图片检测 

检测前通过 `Range: bytes=0-0` 查询文件总大小，只读取响应头后关闭连接。
大小按 `1MB = 1024 × 1024` 字节计算；超过配置 `image_size` 时提示当前大小并停止检测，
等于上限时仍可检测。无法获取有效大小时会提示失败并停止检测。

小于 5MB 时提示“开始进行图片检测”；大于等于 5MB 时提示检测将会缓慢。
大于等于 5MB 且小于 32MB 的图片会设置腾讯云参数 `LargeImageDetect=1`。

例1：

![](https://www.matahape.cn/minio/share/github/QQ20261020-015000.png)

例2：

![](https://www.matahape.cn/minio/share/github/QQ20261020-015133.png)

### 5.2:图片加密

描述：对图片进行加密

命令： 图片+图片加密 / 图片加密 +图片 /  引用+图片加密

例：

![](https://www.matahape.cn/minio/share/github/QQ20261020-015422.png)

### 5.3:图片解密

描述：对图片进行解密

命令： 图片+图片解密 / 图片解密 +图片 /  引用+图片解密

例：

![](https://www.matahape.cn/minio/share/github/QQ20261020-015749.png)

### 5.4:幻影坦克

描述：对图片进行幻影坦克制作

命令： 幻影坦克+里图+表图 / 幻影坦克+里图 /  引用里图+幻影坦克 / 引用里图+幻影坦克+表图
如果没表图将使用默认图片作为表图

例：

![](https://www.matahape.cn/minio/share/github/QQ20261020-020117.png)
