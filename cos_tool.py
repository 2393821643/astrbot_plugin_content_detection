from qcloud_cos import CosS3Client


def image_detection(cos_client: CosS3Client, bucket: str, image_url: str) -> dict:
    """Send an image detection request and return the four detection scores."""
    response = cos_client.get_object_sensitive_content_recognition(
        Bucket=bucket,
        DetectUrl=image_url,
    )
    return {
        "ads_score": response["AdsInfo"]["Score"],
        "politics_score": response["PoliticsInfo"]["Score"],
        "porn_score": response["PornInfo"]["Score"],
        "terrorism_score": response["TerrorismInfo"]["Score"],
    }
