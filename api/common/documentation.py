from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Decorator for standardized documentation
def document_endpoint(
    summary: str,
    description: str,
    request_examples: list = None,
    response_examples: list = None,
    parameters: list = None
):
    """Standard endpoint documentation decorator"""
    
    return extend_schema(
        summary=summary,
        description=description,
        parameters=parameters or [],
        examples=[
            OpenApiExample(
                name=example['name'],
                value=example['value'],
                request_only=example.get('request_only', False),
                response_only=example.get('response_only', False)
            )
            for example in (request_examples or []) + (response_examples or [])
        ]
    )