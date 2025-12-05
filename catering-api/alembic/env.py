from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

from core.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# 添加当前项目路径到环境变量
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 导入项目中的基本映射类，与 需要迁移的 ORM 模型
from apps.vadmin.system.models import *
from apps.vadmin.record.models import *
from apps.vadmin.product.models import *

# 修改配置中的参数
target_metadata = Base.metadata


def run_migrations_offline():
    """
    以“脱机”模式运行迁移。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 是否检查字段类型，字段长度
        compare_server_default=True  # 是否比较在数据库中的默认值
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    以"在线"模式运行迁移。
    """
    # 获取配置节（dev 或 pro）
    configuration = config.get_section(config.config_ini_section, {})
    
    # 从配置中获取数据库 URL
    url = configuration.get("sqlalchemy.url")
    if not url:
        # 如果配置节中没有，尝试从主配置获取
        url = config.get_main_option("sqlalchemy.url")
    
    if not url:
        raise ValueError(f"未找到数据库 URL 配置。请检查 alembic.ini 文件中的 [{config.config_ini_section}] 节。")
    
    # engine_from_config 使用 prefix="sqlalchemy." 时，会查找 sqlalchemy.url 键
    # 直接使用 create_engine 更简单可靠
    from sqlalchemy import create_engine
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 是否检查字段类型，字段长度
            compare_server_default=True  # 是否比较在数据库中的默认值
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    print("offline")
    run_migrations_offline()
else:
    print("online")
    run_migrations_online()
