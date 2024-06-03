import pandas as pd
import logging
import dropbox
from .data_access import DataAccess
import io

class DropboxDataAccess(DataAccess):

    def __init__(self, access_token, directory, file_name):
        self.dbx = dropbox.Dropbox(access_token)
        self.directory = directory
        self.file_name = file_name
        self.file_path = f"{self.directory}/{self.file_name}"

    def file_exists(self) -> bool:
        try:
            self.dbx.files_get_metadata(self.file_path)
            return True
        except dropbox.exceptions.ApiError as e:
            logging.error(f"Error checking if file exists in Dropbox: {e}")
            return False

    def save(self, data: pd.DataFrame) -> None:
        try:
            with io.BytesIO() as output:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    data.to_excel(writer, index=False)
                output.seek(0)
                self.dbx.files_upload(output.read(), self.file_path, mode=dropbox.files.WriteMode('overwrite'))
        except Exception as e:
            logging.error(f"Error saving to Dropbox: {e}")

    def load(self) -> pd.DataFrame:
        try:
            metadata, res = self.dbx.files_download(path=self.file_path)
            data = pd.read_excel(io.BytesIO(res.content), engine='openpyxl')
            data['CustomerID'] = data['CustomerID'].astype(str)
            return data
        except Exception as e:
            logging.error(f"Error loading from Dropbox: {e}")
            return pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])
