import requests


class ExternalApiError(RuntimeError):
    pass


def _get_json(url, params, timeout, service_name, headers=None):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers=headers,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise ExternalApiError(f"{service_name} request timed out") from exc
    except requests.RequestException as exc:
        raise ExternalApiError(f"{service_name} request failed") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ExternalApiError(f"{service_name} returned malformed JSON") from exc


def _post_json(url, data, timeout, service_name, headers=None):
    try:
        response = requests.post(
            url,
            data=data,
            timeout=timeout,
            headers=headers or {},
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise ExternalApiError(f"{service_name} request timed out") from exc
    except requests.RequestException as exc:
        raise ExternalApiError(f"{service_name} request failed") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ExternalApiError(f"{service_name} returned malformed JSON") from exc
