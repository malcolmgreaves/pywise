from pytest import raises

from core_utils.url_bucket_kv import InvalidBucketKvUrl, parse_bucket_kv_url

"""
what to do here is to refactor this function to a helper
then we call it with gs, s3 and custom w/ support for custom
and just verify it!
"""


def test_parse_bucket_kv_url(protocol):
    u = parse_bucket_kv_url(f"{protocol}://bucket/a/long32/key-here")
    assert u.protocol == protocol
    assert u.bucket == "bucket"
    assert u.key == "a/long32/key-here"


def test_parse_bucket_kv_url_fail():
    with raises(InvalidBucketKvUrl):
        parse_bucket_kv_url("")

    with raises(InvalidBucketKvUrl):
        parse_bucket_kv_url("protocol://bucket")

    with raises(InvalidBucketKvUrl):
        parse_bucket_kv_url("protocol://bucket")

    with raises(InvalidBucketKvUrl):
        parse_bucket_kv_url("custom://bucket/key", support_custom_protocol="")
