"""
图片模型
Created by: tao-xiaoxin
Created time: 2025-02-14 07:18:52
"""
from sqlalchemy import Column, String, DateTime, BigInteger
from database.base import Base
from utils.timezone import timezone


class ImageModels(Base):
    """图片模型"""
    __tablename__ = "pf_images"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="图片ID")
    key = Column(String(32), unique=True, nullable=False, comment="图片唯一标识(MD5)")
    original_name = Column(String(255), nullable=True, comment="原始文件名")
    extension = Column(String(10), nullable=False, comment="文件后缀")
    size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    mime_type = Column(String(128), nullable=False, comment="文件MIME类型")
    storage_path = Column(String(255), nullable=False, comment="存储路径")
    view_count = Column(BigInteger, default=0, nullable=False, comment="浏览次数")
    created_at = Column(
        DateTime,
        nullable=False,
        default=timezone.now,
        comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=timezone.now,
        onupdate=timezone.now,
        comment="更新时间"
    )

    def __repr__(self):
        return f"<Image {self.key}>"
