"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from connectors.base_connector import BaseConnector
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage

class CloudStorageConnector(BaseConnector):
    def connect(self):
        provider = self.config.get('provider')
        if provider == 'aws':
            self.client = boto3.client('s3', **self.config.get('aws_creds', {}))
        elif provider == 'azure':
            self.client = BlobServiceClient.from_connection_string(self.config.get('azure_conn_str'))
        elif provider == 'gcp':
            self.client = storage.Client.from_service_account_json(self.config.get('gcp_keyfile'))
        else:
            raise ValueError('Unknown provider')
        return True

    def test_connection(self):
        try:
            if self.config.get('provider') == 'aws':
                self.client.list_buckets()
            elif self.config.get('provider') == 'azure':
                list(self.client.list_containers())
            elif self.config.get('provider') == 'gcp':
                list(self.client.list_buckets())
            return True
        except Exception:
            return False

    def sync(self):
        # Example: List files in bucket
        bucket = self.config.get('bucket')
        if self.config.get('provider') == 'aws':
            return self.client.list_objects_v2(Bucket=bucket).get('Contents', [])
        elif self.config.get('provider') == 'azure':
            container = self.client.get_container_client(bucket)
            return [b.name for b in container.list_blobs()]
        elif self.config.get('provider') == 'gcp':
            b = self.client.get_bucket(bucket)
            return [blob.name for blob in b.list_blobs()]
        return []
