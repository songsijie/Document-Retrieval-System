import asyncio
import base64
import hashlib
import hmac
import random
import secrets
import string


def calculate_md5(content: str) -> str:
    """计算MD5值"""
    md5_hash = hashlib.md5()
    md5_hash.update(content.encode("utf-8"))
    return md5_hash.hexdigest()


def calculate_sha256(content: str) -> str:
    """计算SHA256值"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content.encode("utf-8"))
    return sha256_hash.hexdigest()


def get_file_extension(content_type):
    """根据 MIME 类型返回文件扩展名"""
    mime_to_extension = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/webp": "webp",
        "image/svg+xml": "svg",
        "image/tiff": "tiff",
        "image/heif": "heif",
        "image/vnd.microsoft.icon": "ico",
    }
    # 返回对应的文件后缀，如果不在字典中，默认返回 None
    return mime_to_extension.get(content_type)


def mask_sensitive_info(input: str) -> str:
    """掩码敏感信息"""
    str_input = str(input)

    # 计算要替换的字符数量和开始替换的位置
    mask_length = (len(str_input) + 1) // 3
    start = (len(str_input) - mask_length) // 2

    # 使用字符串切片和重复字符串创建掩码
    return str_input[:start] + "*" * mask_length + str_input[(start + mask_length) :]


def generate_random_string(length=10):
    """生成随机字符串"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_secret(length: int = 24) -> str:
    """生成随机密码：长度 8~32，至少包含四类中的任意三类。

    四类：大写字母、小写字母、数字、特殊字符；特殊字符仅: !@#$%^&*()_+-=
    """
    if length < 8 or length > 32:
        raise ValueError("length must be between 8 and 32")

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    punctuation = "!@#$%^&*()_+-="

    classes = [lowercase, uppercase, digits, punctuation]

    # 随机选择 3 类以确保至少覆盖三类
    sysrand = random.SystemRandom()
    selected = sysrand.sample(classes, 3)
    password_chars = [secrets.choice(cls) for cls in selected]

    # 剩余位数从允许的全集中选取
    all_chars = lowercase + uppercase + digits + punctuation
    password_chars += [secrets.choice(all_chars) for _ in range(length - 3)]

    # CSPRNG 洗牌
    sysrand.shuffle(password_chars)
    return "".join(password_chars)


def generate_6_digit_code():
    """生成 6 位纯数字验证码（可能包含前导 0),简单且性能好。"""
    num = random.randint(0, 999999)  # 生成 0~999999 的随机数
    return f"{num:06d}"


async def sleep(milliseconds: int):
    await asyncio.sleep(milliseconds / 1000)


def generate_signature(message: str, secret_key: str) -> str:
    """生成签名"""
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode()


def verify_signature(message: str, secret_key: str, signature: str) -> bool:
    """验证签名"""
    expected_signature = generate_signature(message, secret_key)
    return hmac.compare_digest(expected_signature, signature)
