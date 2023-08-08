from sqlalchemy import create_engine
import config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, TEXT, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
import threading

engine = create_engine(config.db_url, echo=config.log_sql)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

Model = declarative_base()
class Prompt(Model):
    __tablename__ = 'prompt'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), unique=True)
    name = Column(String(255), server_default="")
    few_shot = Column(Boolean, server_default="0")
    template = Column(TEXT, server_default="")
    examples = Column(TEXT, server_default="")
    prefix = Column(TEXT, server_default="")
    suffix = Column(TEXT, server_default="")
    seperator = Column(String(255), server_default="")

class DataSet(Model):
    __tablename__ = 'data_set'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), unique=True)
    name = Column(String(255), server_default="", unique=True)

class DataItem(Model):
    __tablename__ = 'data_item'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), unique=True)
    dataset_uid = Column(String(255))
    args = Column(TEXT, server_default="{}")

LLM_TYPE_MOSS = 'moss'
LLM_TYPE_GLM = 'glm'
LLM_TYPES = [LLM_TYPE_MOSS]

class LLM(Model):
    __tablename__ = 'llm'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), unique=True)
    name = Column(String(255), server_default="")
    type = Column(String(255), server_default="")
    path = Column(String(255), server_default="")
    args = Column(TEXT, server_default="{}")


def db_create_all():
    Model.metadata.create_all(engine)

