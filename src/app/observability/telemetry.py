from __future__ import annotations
import os
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor,ConsoleSpanExporter
def configure_telemetry(app:FastAPI)->None:
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT");console=os.getenv("OTEL_CONSOLE_EXPORTER","false").lower()=="true"
    if endpoint or console:
        provider=TracerProvider(resource=Resource.create({"service.name":"production-rag-agent"}))
        if endpoint:provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        if console:provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
tracer=trace.get_tracer("production-rag-agent")
