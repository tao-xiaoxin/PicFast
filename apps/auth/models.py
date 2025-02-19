"""
认证相关数据库模型
Created by: tao-xiaoxin
Created time: 2025-02-19 00:48:16
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from utils.database import MappedBase
from utils.timezone import timezone


class AccessKey(MappedBase):
    """访问密钥模型"""

    __tablename__ = "fp_access_keys"
    __table_args__ = {'comment': '访问密钥表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = Column(String(50), nullable=False, comment='密钥名称')
    access_key = Column(String(100), unique=True, nullable=False, index=True, comment='访问密钥')
    secret_key = Column(String(100), nullable=False, comment='密钥')
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    description = Column(String(200), nullable=True, comment='描述')
    expires_at = Column(DateTime, nullable=True, comment='过期时间')
    last_used_at = Column(DateTime, nullable=True, comment='最后使用时间')
    created_at = Column(DateTime, default=timezone.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=timezone.now, onupdate=timezone.now,
                        nullable=False, comment='更新时间')

    def __repr__(self):
        return f"<AccessKey {self.name}>"
