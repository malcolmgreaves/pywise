import re
from typing import NamedTuple, Optional, Sequence

__all__: Sequence[str] = (
    "parse_bucket_kv_url",
    "ParsedKvUrl",
    "InvalidBucketKvUrl",
)


class ParsedKvUrl(NamedTuple):
    """The URL components of a bucket based key-value store.

    Useful for AWS S3-like stores. Use alongside the `parse_attachment_url` function.
    """

    protocol: str
    bucket: str
    key: str
    region: Optional[str]

    def canonical_url(self) -> str:
        """Packs the parsed URL information into a standard form of
        `<protocol>://<bucket>/<key>`.
        """
        return f"{self.protocol}://{self.bucket}/{self.key}"


class InvalidBucketKvUrl(ValueError):
    pass


def parse_bucket_kv_url(url: str, *, support_custom_protocol: Optional[str] = None) -> ParsedKvUrl:
    """Extracts protocol, bucket, region, and key from the :param:`url`.

    :raises: InvalidBucketKvUrl Iff the input `url` is not a valid AWS S3 or GCS url.
    """
    # returns dict of protocol, bucket, region, key
    protocol = "s3"
    bucket = None
    region = None
    key = None

    # s3://bucket/key1/key2
    match = re.search("^s3://([^/]+)/(.*?)$", url)
    if match:
        bucket, key = match.group(1), match.group(2)

    # gs://bucket/key1/key2
    match = re.search("^gs://([^/]+)/(.*?)$", url)
    if match:
        protocol = "gs"
        bucket, key = match.group(1), match.group(2)

    # http://bucket.s3.amazonaws.com/key1/key2
    match = re.search("^https?://(.+).s3.amazonaws.com(.*?)$", url)
    if match:
        bucket, key = match.group(1), match.group(2)

    # http://bucket.s3-aws-region.amazonaws.com/key1/key2
    match = re.search("^https?://(.+).s3[.-](dualstack\\.)?([^.]+).amazonaws.com(.*?)$", url)
    if match:
        bucket, region, key = match.group(1), match.group(3), match.group(4)

    # http://s3.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3.amazonaws.com/([^/]+)(.*?)$", url)
    if match:
        bucket, key = match.group(1), match.group(2)

    # http://s3-aws-region.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3[.-](dualstack\\.)?([^.]+).amazonaws.com/([^/]+)(.*?)$", url)
    if match:
        bucket, region, key = match.group(3), match.group(2), match.group(4)

    # https://storage.cloud.google.com/bucket/this/is/a/key
    match = re.search("^https?://storage.cloud.google.com/([^/]+)(.*?)$", url)
    if match:
        protocol = "gs"
        bucket, key = match.group(1), match.group(2)

    # http://s3.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3.amazonaws.com/([^/]+)(.*?)$", url)
    if match:
        bucket, key = match.group(1), match.group(2)

    if support_custom_protocol is not None:
        support_custom_protocol = support_custom_protocol.strip()
        if len(support_custom_protocol) == 0:
            raise InvalidBucketKvUrl("support_custom_protocol cannot be empty!")

        match = re.search(f"{support_custom_protocol}://(\\w+)/([\\-\\w\\/]+)", url)
        if match:
            bucket, key = match.group(1), match.group(2)
            protocol = support_custom_protocol

    if bucket is None or key is None:
        raise InvalidBucketKvUrl(
            "Invalid attachment URL: no bucket or key specified: \n" f"'{url}'"
        )

    clean = lambda v: (v and v.strip("/"))

    return ParsedKvUrl(
        protocol=clean(protocol),
        bucket=clean(bucket),
        region=clean(region),
        key=clean(key),
    )
