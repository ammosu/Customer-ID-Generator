import pandas as pd
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from .data_access import DataAccess

class DBDataAccess(DataAccess):

    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.metadata = MetaData()
        self.customers_table = Table('customers', self.metadata,
                                     Column('Region', String),
                                     Column('Category', String),
                                     Column('CompanyName', String),
                                     Column('ExtraRegionCode', String, nullable=True),
                                     Column('BranchName', String, nullable=True),
                                     Column('BranchHandling', String, nullable=True),
                                     Column('CustomerID', String, primary_key=True))
        if not self.engine.dialect.has_table(self.engine, 'customers'):
            self.metadata.create_all(self.engine)

    def file_exists(self) -> bool:
        return self.engine.dialect.has_table(self.engine, 'customers')

    def save(self, data: pd.DataFrame) -> None:
        try:
            data.to_sql('customers', self.engine, if_exists='replace', index=False)
        except Exception as e:
            logging.error(f"Error saving to database: {e}")

    def load(self) -> pd.DataFrame:
        try:
            data = pd.read_sql_table('customers', self.engine)
            data['CustomerID'] = data['CustomerID'].astype(str)
            return data
        except Exception as e:
            logging.error(f"Error loading from database: {e}")
            return pd.DataFrame(columns=['Region', 'Category', 'CompanyName', 'ExtraRegionCode', 'BranchName', 'BranchHandling', 'CustomerID'])
