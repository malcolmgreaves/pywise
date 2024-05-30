import re
from typing import NamedTuple, Optional, Sequence

__all__: Sequence[str] = (
    # main use
    "parse_bucket_kv_url",
    # data structures
    "ParsedKvUrl",
    "InvalidBucketKvUrl",
    # supporting parsing functions
    "parse_s3_url_formats",
    "parse_gcs_url_formats",
    "parse_custom_url_format",
)


class ParsedKvUrl(NamedTuple):
    """The URL components of a bucket based key-value store. Use with :func:`parse_bucket_kv_url`."""

    protocol: str
    bucket: str
    key: str
    region: Optional[str]

    def canonical_url(self) -> str:
        """Packs the parsed URL information into a standard form of `<protocol>://<bucket>/<key>`."""
        return f"{self.protocol}://{self.bucket}/{self.key}"


class InvalidBucketKvUrl(ValueError):
    pass


def parse_bucket_kv_url(url: str, *, support_custom_protocol: Optional[str] = None) -> ParsedKvUrl:
    """Extracts protocol, bucket, region, and key from the :param:`url`.

    Primarily handles AWS S3 and Google Cloud Storage (GCS) URL formats. Includes both the "direct"
    style `protocol://bucket/key` format in addition to HTTP(S) based URL formats.

    If :param:`support_custom_protocol` is not None, then additional support for simple URL schemes
    of the form:

        support_custom_protocol://bucket/key

    are also supported. Note that, unlike the S3 and GCS protocols, HTTP(S) URL formats are not
    supported.

    :raises: InvalidBucketKvUrl Iff the input `url` is not a valid AWS S3 or GCS url.
                                Or if it is not also a supported variant of the custom protocol.
    """
    if support_custom_protocol is not None:
        p = parse_custom_url_format(support_custom_protocol, url, region=None)
        if p is not None:
            return p

    p = parse_s3_url_formats(url)
    if p is not None:
        return p

    p = parse_s3_url_formats(url)
    if p is not None:
        return p

    raise InvalidBucketKvUrl(f"Invalid attachment URL: no bucket or key specified: '{url}'")


def parse_custom_url_format(
    support_custom_protocol: str, url: str, region: Optional[str]
) -> Optional[ParsedKvUrl]:
    support_custom_protocol = support_custom_protocol.strip()
    if len(support_custom_protocol) == 0:
        raise InvalidBucketKvUrl("support_custom_protocol cannot be empty!")

    match = re.search(f"{support_custom_protocol}://(\\w+)/([\\-\\w\\/]+)", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(
            protocol=support_custom_protocol,
            bucket=match.group(1),
            key=match.group(2),
            region=region,
        )
    return None


def parse_s3_url_formats(url: str) -> Optional[ParsedKvUrl]:
    # s3://bucket/key1/key2
    match = re.search("^s3://([^/]+)/(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="s3", bucket=match.group(1), key=match.group(2))

    # http://bucket.s3.amazonaws.com/key1/key2
    match = re.search("^https?://(.+).s3.amazonaws.com(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="s3", bucket=match.group(1), key=match.group(2))

    # http://bucket.s3-aws-region.amazonaws.com/key1/key2
    match = re.search("^https?://(.+).s3[.-](dualstack\\.)?([^.]+).amazonaws.com(.*?)$", url)
    if match is not None:
        # bucket, region, key = match.group(1), match.group(3), match.group(4)
        return _clean_create(
            protocol="s3", bucket=match.group(1), key=match.group(4), region=match.group(3)
        )

    # http://s3.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3.amazonaws.com/([^/]+)(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="s3", bucket=match.group(1), key=match.group(2))

    # http://s3-aws-region.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3[.-](dualstack\\.)?([^.]+).amazonaws.com/([^/]+)(.*?)$", url)
    if match is not None:
        # bucket, region, key = match.group(3), match.group(2), match.group(4)
        return _clean_create(
            protocol="s3", bucket=match.group(3), key=match.group(4), region=match.group(2)
        )

    # format:
    # http://s3.amazonaws.com/bucket/key1/key2
    match = re.search("^https?://s3.amazonaws.com/([^/]+)(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="s3", bucket=match.group(1), key=match.group(2))

    return None


def parse_gcs_url_formats(url: str) -> Optional[ParsedKvUrl]:
    # gs://bucket/key1/key2
    match = re.search("^gs://([^/]+)/(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="gs", bucket=match.group(1), key=match.group(2))

    # https://storage.cloud.google.com/bucket/this/is/a/key
    match = re.search("^https?://storage.cloud.google.com/([^/]+)(.*?)$", url)
    if match is not None:
        # bucket, key = match.group(1), match.group(2)
        return _clean_create(protocol="gs", bucket=match.group(1), key=match.group(2))

    return None


def _clean_create(
    protocol: str, bucket: str, key: str, region: Optional[str] = None
) -> ParsedKvUrl:
    x = ParsedKvUrl(
        protocol=protocol.strip(),
        bucket=bucket.strip(),
        key=key.strip(),
        region=region.strip() if region is not None else None,
    )
    if len(x.protocol) == 0:
        raise ValueError("Must have non-empty protocol!")
    if len(x.bucket) == 0:
        raise ValueError("Must have non-empty bucket!")
    if len(x.key) == 0:
        raise ValueError("Must have non-empty key!")
    if x.region is not None and len(x.region) == 0:
        raise ValueError("Must have non-empty region!")
    return x
