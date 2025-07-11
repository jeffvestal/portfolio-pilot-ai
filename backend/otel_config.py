from opentelemetry.distro import OpenTelemetryDistro
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def setup_telemetry():
    """Configures OpenTelemetry for the application."""
    distro = OpenTelemetryDistro()
    distro.configure(
        trace_exporter=OTLPSpanExporter(
            endpoint="http://localhost:4318/v1/traces"
        )
    )
