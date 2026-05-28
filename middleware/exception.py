import traceback

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from base.exception import CustomError, default_error_code


class ErrorResponse(BaseModel):
    code: int = Field(default_error_code, description="错误码")
    message: str = Field("internal server error", description="错误信息")


async def exception_handler(request: Request, call_next):
    wrapped = None
    try:
        return await call_next(request)
    except CustomError as e:
        print("CustomError", traceback.format_exc())
        wrapped = ErrorResponse(code=e.code, message=str(e))
        response = JSONResponse(status_code=200, content=wrapped.model_dump())
    except TimeoutError:
        print("TimeoutError", traceback.format_exc())
        wrapped = ErrorResponse(code=default_error_code, message="Request Timeout")
        response = JSONResponse(status_code=408, content=wrapped.model_dump())
    except HTTPException as e:
        print("HTTPException", traceback.format_exc())
        wrapped = ErrorResponse(code=default_error_code, message=str(e.detail))
        response = JSONResponse(status_code=e.status_code, content=wrapped.model_dump())
    except RequestValidationError as e:
        print("RequestValidationError", traceback.format_exc())
        wrapped = ErrorResponse(code=default_error_code, message="Validation Error", data=e.errors())
        response = JSONResponse(status_code=422, content=wrapped.model_dump())
    except Exception as e:
        print("Exception", traceback.format_exc())
        wrapped = ErrorResponse(code=default_error_code, message=str(e))
        response = JSONResponse(status_code=500, content=wrapped.model_dump())

    request.state.response_body = wrapped.model_dump()
    return response
