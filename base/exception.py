from fastapi import HTTPException, status

default_error_code = 10000


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized",
)

# 权限不足
permission_denied_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permission denied",
)


class CustomError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def create_custom_error(code: int, message: str):
    return CustomError(code, message)


# 未知错误
unknown_error_exception = create_custom_error(default_error_code, "未知错误")

# 索引不存在
index_not_found_exception = create_custom_error("10001", "索引不存在")

# 索引已存在
index_already_exists_exception = create_custom_error("10002", "索引已存在")
