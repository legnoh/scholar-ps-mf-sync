from prometheus_client import Gauge, Counter, Info, CollectorRegistry

def create_metric_instance(definition:dict, registry:CollectorRegistry):
    return Gauge( definition['name'], definition['desc'], definition['labels'], registry=registry )

def set_metrics(m, labels:list, value):
    m.labels(*labels).set(value)
