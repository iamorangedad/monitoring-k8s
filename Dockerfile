FROM python:3.9-slim
RUN pip install prometheus-client jetson-stats
COPY exporter.py /exporter.py
CMD ["python3", "/exporter.py"]