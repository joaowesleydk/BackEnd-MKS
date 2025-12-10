from fastapi.responses import JSONResponse

def success_response(data=None, message="Success"):
    return JSONResponse(content={
        "success": True,
        "data": data,
        "message": message
    })

def error_response(message="Error", status_code=400):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "message": message
        }
    )