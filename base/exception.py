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


# 配置未找到
unknown_error_exception = create_custom_error(default_error_code, "未知错误")

