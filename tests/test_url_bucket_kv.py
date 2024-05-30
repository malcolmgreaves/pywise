from pytest import mark, raises

from core_utils.url_bucket_kv import InvalidBucketKvUrl, parse_bucket_kv_url


@mark.parametrize("p", ["s3", "gs", "custom-protocol"])
def test_parse_bucket_kv_url_proto(p):
    u = parse_bucket_kv_url(
        f"{p}://bucket/a/long32/key-here", support_custom_protocol="custom-protocol"
    )
    assert u.protocol == p
    assert u.bucket == "bucket"
    assert u.key == "a/long32/key-here"
    assert u.region is None


def test_parse_bucket_kv_url_fail():
    for invalid_url in ["", "protocol://bucket/key", "s3://bucket", "gcs://bucket"]:
        with raises(InvalidBucketKvUrl):
            parse_bucket_kv_url(invalid_url)

    with raises(InvalidBucketKvUrl):
        parse_bucket_kv_url("custom://bucket/key", support_custom_protocol="")


@mark.parametrize(
    "url",
    [
        "http://bucket.s3.amazonaws.com/key1/key2",
        "http://bucket.s3-aws-region.amazonaws.com/key1/key2",
        "http://s3.amazonaws.com/bucket/key1/key2",
        "http://bucket.s3-aws-region.amazonaws.com/key1/key2",
        "http://s3-aws-region.amazonaws.com/bucket/key1/key2",
    ],
)
def test_extended_s3_parsing(url):
    p = parse_bucket_kv_url(url)
    assert p.bucket == "bucket"
    assert p.key == "key1/key2"
    assert p.protocol == "s3"
    # only the last example has a region specified
    assert p.region is None or p.region == "region"


@mark.parametrize("url", ["https://storage.cloud.google.com/bucket/this/is/a/key"])
def test_extended_gs_parsing(url):
    p = parse_bucket_kv_url(url)
    assert p.protocol == "gs"
    assert p.bucket == "bucket"
    assert p.key == "this/is/a/key"
    assert p.region is None
