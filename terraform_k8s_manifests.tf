# ============================================================
# KUBERNETES MANIFESTS via Helm / kubectl (inline for reference)
# Deployed into EKS cluster
# ============================================================

# Helm release: FastAPI Backend
resource "helm_release" "fastapi_backend" {
  name             = "scnv-backend"
  chart            = "./charts/fastapi-backend"
  namespace        = "scnv"
  create_namespace = true

  set = [
    {
      name  = "image.repository"
      value = aws_ecr_repository.repos["scnv-fastapi-backend"].repository_url
    },
    {
      name  = "image.tag"
      value = var.app_version
    },
    {
      name  = "replicaCount"
      value = "3"
    },
    {
      name  = "autoscaling.enabled"
      value = "true"
    },
    {
      name  = "autoscaling.minReplicas"
      value = "2"
    },
    {
      name  = "autoscaling.maxReplicas"
      value = "10"
    },
    {
      name  = "autoscaling.targetCPU"
      value = "60"
    },
    {
      name  = "resources.requests.cpu"
      value = "500m"
    },
    {
      name  = "resources.requests.memory"
      value = "1Gi"
    },
    {
      name  = "resources.limits.cpu"
      value = "2000m"
    },
    {
      name  = "resources.limits.memory"
      value = "4Gi"
    },
    {
      name  = "env.DATABASE_URL"
      value = "postgresql://scnv_admin:@${aws_db_instance.postgres.endpoint}/scnv"
    },
    {
      name  = "env.REDIS_URL"
      value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379"
    }
  ]
}

# Helm release: LangGraph Agent Orchestrator
resource "helm_release" "langgraph_agents" {
  name      = "scnv-agents"
  chart     = "./charts/langgraph-agents"
  namespace = "scnv"

  set = [
    {
      name  = "image.repository"
      value = aws_ecr_repository.repos["scnv-langgraph-agents"].repository_url
    },
    {
      name  = "image.tag"
      value = var.app_version
    },
    {
      name  = "replicaCount"
      value = "2"
    },
    {
      name  = "tolerations[0].key"
      value = "dedicated"
    },
    {
      name  = "tolerations[0].value"
      value = "agents"
    },
    {
      name  = "tolerations[0].effect"
      value = "NoSchedule"
    },
    {
      name  = "nodeSelector.role"
      value = "agent-worker"
    },
    {
      name  = "resources.requests.cpu"
      value = "1000m"
    },
    {
      name  = "resources.requests.memory"
      value = "4Gi"
    },
    {
      name  = "resources.limits.cpu"
      value = "4000m"
    },
    {
      name  = "resources.limits.memory"
      value = "8Gi"
    },
    {
      name  = "env.KAFKA_BOOTSTRAP"
      value = aws_msk_cluster.kafka.bootstrap_brokers_tls
    },
    {
      name  = "env.CELONIS_ENABLED"
      value = "false"
    }
  ]
}

# Helm release: Kafka Consumer (SAP Event Ingestion)
resource "helm_release" "kafka_consumer" {
  name      = "scnv-kafka-consumer"
  chart     = "./charts/kafka-consumer"
  namespace = "scnv"

  set = [
    {
      name  = "image.repository"
      value = aws_ecr_repository.repos["scnv-kafka-consumer"].repository_url
    },
    {
      name  = "replicaCount"
      value = "3"
    },
    {
      name  = "kafka.topics"
      value = "sto-events,delivery-events,so-events"
    },
    {
      name  = "kafka.consumerGroup"
      value = "scnv-agent-group"
    }
  ]
}

# Helm release: React Frontend
resource "helm_release" "frontend" {
  name      = "scnv-frontend"
  chart     = "./charts/react-frontend"
  namespace = "scnv"

  set = [
    {
      name  = "image.repository"
      value = aws_ecr_repository.repos["scnv-react-frontend"].repository_url
    },
    {
      name  = "replicaCount"
      value = "2"
    }
  ]
}

# Helm release: Prometheus + Grafana monitoring
resource "helm_release" "monitoring" {
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true

  set = [
    {
      name  = "grafana.enabled"
      value = "true"
    },
    {
      name  = "prometheus.prometheusSpec.retention"
      value = "30d"
    },
    {
      name  = "grafana.adminPassword"
      value = "REPLACE_WITH_SECRET"
    }
  ]
}

variable "app_version" { default = "latest" }
