from qcloud_cos import CosS3Client


def image_detection(
    cos_client: CosS3Client, bucket: str, image_url: str, image_size_bytes: int = 0
) -> dict:
    """Send an image detection request and return the four detection scores."""
    request: dict[str, str | int] = {"Bucket": bucket, "DetectUrl": image_url}
    if 5 * 1024 * 1024 <= image_size_bytes < 32 * 1024 * 1024:
        request["LargeImageDetect"] = 1
    response = cos_client.get_object_sensitive_content_recognition(**request)
    return {
        "ads_score": response["AdsInfo"]["Score"],
        "politics_score": response["PoliticsInfo"]["Score"],
        "porn_score": response["PornInfo"]["Score"],
        "terrorism_score": response["TerrorismInfo"]["Score"],
    }
