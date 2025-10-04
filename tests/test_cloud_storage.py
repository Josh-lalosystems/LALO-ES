import pytest
from connectors.cloud_storage_connector import CloudStorageConnector

def test_aws(monkeypatch):
    class DummyS3:
        def list_buckets(self):
            return {'Buckets': ['b1']}
        def list_objects_v2(self, Bucket):
            return {'Contents': [{'Key': 'file1.txt'}]}
    monkeypatch.setattr('boto3.client', lambda *a, **k: DummyS3())
    connector = CloudStorageConnector({'provider': 'aws', 'aws_creds': {}, 'bucket': 'b1'})
    connector.connect()
    assert connector.test_connection() is True
    assert connector.sync()[0]['Key'] == 'file1.txt'
