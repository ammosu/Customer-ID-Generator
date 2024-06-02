from data_access.s3_data_access import S3DataAccess
from data_access.db_data_access import DBDataAccess

class DataAccessFactory:

    @staticmethod
    def get_data_access(storage_type, **kwargs):
        if storage_type == 's3':
            return S3DataAccess(
                bucket_name=kwargs['bucket_name'],
                directory=kwargs['directory'],
                file_name=kwargs['file_name'],
                region=kwargs['region'],
                access_key=kwargs['access_key'],
                secret_key=kwargs['secret_key']
            )
        elif storage_type == 'db':
            return DBDataAccess(
                db_url=kwargs['db_url']
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
