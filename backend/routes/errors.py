from flask import jsonify
from werkzeug.exceptions import HTTPException

from . import api


def error_response(message, status=400, error_type="request_error", details=None):
    payload = {
        "success": False,
        "message": message,
        "error": {
            "code": status,
            "type": error_type,
        },
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status


@api.app_errorhandler(HTTPException)
def handle_http_exception(error):
    status = error.code or 500
    if status == 404:
        message = "API route not found"
    elif status == 400:
        message = error.description or "Invalid request format"
    else:
        message = error.description
    error_type = "request_error" if status < 500 else "server_error"
    return error_response(message, status, error_type)


@api.app_errorhandler(Exception)
def handle_unexpected_error(error):
    return error_response(
        "An unexpected server error occurred",
        500,
        "server_error",
    )
