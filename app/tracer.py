"""
thanks for https://adex.ltd/integrating-opentelemetry-with-fastapi-in-python
"""

from opentelemetry import trace

# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,  # Optional for debugging
)

SERVICE_NAME = "api.rss.navydev.top"


# Initialize OpenTelemetry Tracer globally
def initialize_tracer():
    # Create a resource for trace identification with service info
    resource = Resource.create({"service.name": SERVICE_NAME})

    # Set up the TracerProvider, the root of all tracing
    tracer_provider = TracerProvider(resource=resource)

    # Configure the OTLP Exporter to send traces to the OpenTelemetry Collector
    # otlp_exporter = OTLPSpanExporter(endpoint=OTLP_COLLECTOR_ENDPOINT)
    # span_processor = BatchSpanProcessor(otlp_exporter)
    # tracer_provider.add_span_processor(span_processor)

    # Optional: Add a ConsoleSpanExporter for local debugging
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())
    tracer_provider.add_span_processor(console_processor)

    # Set the global TracerProvider
    trace.set_tracer_provider(tracer_provider)


# Function to get the global OpenTelemetry Tracer
def get_tracer():
    return trace.get_tracer(SERVICE_NAME)
