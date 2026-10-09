from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 本文件在 app/database.py，parent.parent 就是项目根目录 api-convention
BASE_DIA = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIA / "convention.db"

# sqlite:/// 是固定前缀，后面跟文件路径\
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# check_same_thread=False：FastAPI 可能在不同线程里用同一个库，SQLite 默认会拦
engine = create_engine( # 创建引擎，用于连接数据库 engine = 仓库大门的地址和钥匙。
    DATABASE_URL, #指向项目里的 convention.db数据库
    connect_args={"check_same_thread":False} # 允许在不同线程里用同一个库
)

# 以后增删改查都通过 Session，不要直接操作 .db 文件
SessionLocal = sessionmaker(
    bind=engine, # 绑定引擎，用于连接数据库 SessionLocal = 仓库大门的地址和钥匙。
    autoflush=False, # 自动刷新false，不把内存里的改动先刷进库（和后面的 flush() 有关）
    autocommit=False # 自动提交false，不自动永久保存，要你自己 commit()
)
#所有表类的共同父类，用于创建表对象的基类,没有这个父类，SQLAlchemy 不知道 Hall 是一张表。
class Base(DeclarativeBase):#它自己是空的。作用是：凡是 class Hall(Base)、class Device(Base)，都会登记到 Base.metadata 上。
    pass

def get_db():#get_db() 也是领一张工牌，用完归还。get_db() 返回一个生成器，每次调用都会返回一个 Session 对象。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()