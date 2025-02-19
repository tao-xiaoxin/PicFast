"""
安全相关工具
Created by: tao-xiaoxin
Created time: 2025-02-19 09:55:12
"""

import secrets
import string
import uuid
from passlib.context import CryptContext

# 密码加密上下文 - 使用 Argon2 算法
pwd_context = CryptContext(
    schemes=["argon2"],  # 使用 Argon2 算法，它比 bcrypt 更安全
    deprecated="auto",
    # Argon2 配置参数
    argon2__time_cost=4,  # 迭代次数
    argon2__memory_cost=65536,  # 内存成本
    argon2__parallelism=2  # 并行度
)


def generate_random_string(length: int = 32) -> str:
    """
    生成随机字符串

    Args:
        length: 字符串长度

    Returns:
        str: 随机字符串
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_access_key() -> str:
    """
    生成访问密钥

    Returns:
        str: 访问密钥
    """
    return f"ak-{str(uuid.uuid4()).replace('-', '')}"


def generate_secret_key() -> str:
    """
    生成密钥

    Returns:
        str: 原始密钥
    """
    return f"sk-{generate_random_string(40)}"


def hash_secret_key(secret_key: str) -> str:
    """
    对密钥进行哈希加密

    Args:
        secret_key: 原始密钥

    Returns:
        str: 加密后的密钥哈希值
    """
    return pwd_context.hash(secret_key)


def verify_secret_key(plain_secret_key: str, hashed_secret_key: str) -> bool:
    """
    验证密钥

    Args:
        plain_secret_key: 原始密钥
        hashed_secret_key: 加密后的密钥哈希值

    Returns:
        bool: 验证是否通过
    """
    return pwd_context.verify(plain_secret_key, hashed_secret_key)


def hash_password(password: str) -> str:
    """
    使用哈希算法加密密码

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 要验证的密码
        hashed_password: 要比较的哈希密码

    Returns:
        bool: 验证是否通过
    """
    return pwd_context.verify(plain_password, hashed_password)
