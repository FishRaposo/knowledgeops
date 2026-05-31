"""Refusal validation judge."""

from typing import Any


def check_refusal(expected_refusal: bool, actual_refusal: bool) -> bool:
    """Check if the refusal behavior matches expectations.

    Validates that the system correctly refuses to answer when expected
    and correctly answers when no refusal is expected.

    Args:
        expected_refusal: Whether the system should have refused.
        actual_refusal: Whether the system actually refused.

    Returns:
        True if refusal behavior matches expectation.
    """
    return expected_refusal == actual_refusal


def validate_refusal_response(response: dict[str, Any]) -> dict[str, Any]:
    """Validate the structure of a refusal response.

    Args:
        response: Query response to validate.

    Returns:
        Validation result with is_valid and reason.
    """
    if not response.get("refusal", False):
        return {"is_valid": True, "reason": "Not a refusal response"}

    if not response.get("refusal_reason"):
        return {"is_valid": False, "reason": "Refusal missing reason"}

    if not response.get("answer"):
        return {"is_valid": False, "reason": "Refusal missing answer text"}

    return {"is_valid": True, "reason": "Valid refusal response"}
