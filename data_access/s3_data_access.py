import pandas as pd
import os
import io
import logging
import boto3
from .data_access import DataAccess

class S3DataAccess(DataAccess):

    def __init__(self, bucket_name, directory, file_name, region, access_key, secret_key):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        self.bucket_name = bucket_name
        self.directory = directory
        self.file_name = file_name
        self.file_path = f"{self.directory}/{self.file_name}"

    def file_exists(self) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=self.file_path)
            return True
        except Exception as e:
            logging.error(f"Error checking if file exists in S3: {e}")
            return False

    def save(self, data: pd.DataFrame) -> None:
        try:
            with io.BytesIO() as output:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False)
                output.seek(0)
                self.s3_client.put_object(Bucket=self.bucket_name, Key=self.file_path, Body=output.read())
        except Exception as e:
            logging.error(f"Error saving to S3: {e}")

    def load(self) -> pd.DataFrame:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.file_path)
            data = pd.read_excel(io.BytesIO(response['Body'].read()), engine='openpyxl')
            data['CustomerID'] = data['CustomerID'].astype(str)
            return data
        except Exception as e:
            logging.error(f"Error loading from S3: {e}")
            return pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])
