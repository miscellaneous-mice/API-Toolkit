import yaml
import pandas as pd
import urllib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

class PostGreUtils:
    def __init__(self):
        with open('configs/config.yaml') as file:
            self.config = yaml.load(file, Loader=yaml.SafeLoader)
        self.host = self.config['DATABASE_HOST']
        self.name = self.config['DATABASE_NAME']
        self.username = self.config['DATABASE_USERNAME']
        self.password = urllib.parse.quote_plus(self.config['DATABASE_PASSWORD'])
        self.url = ''

    async def create_connection(self):
        self.url = f'postgresql+psycopg2://{self.host}:{self.password}@{self.host}/{self.name}'
        self.engine = create_engine(self.url)
        self.conn = self.engine.connect()
    
    async def create_session(self):
        if self.url:
            await self.create_connection()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    async def get_from_db(self, **kwargs):
        if 'chunksize' in kwargs:
            df = pd.read_sql(kwargs['sql'], self.engine, chunksize=kwargs['chunksize'])
        else:
            df = pd.read_sql(kwargs['sql'], self.engine)
        return df
    
    async def insert_into_db(self, **kwargs):
        df = kwargs['df']
        df.to_sql('db_table2', self.engine, if_exists='append')
    
    def __del__(self):
        self.conn.close()
        self.engine.dispose()