# ============================================================
# SCNV Agent - Production AWS Infrastructure
# ============================================================

terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
    }
    helm = {
      source  = "hashicorp/helm"
    }
  }
  backend "s3" {
    bucket         = "scnv-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "scnv-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "SCNV-Agent"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "SupplyChainTeam"
    }
  }
}

# ============================================================
# VARIABLES
# ============================================================
variable "aws_region"    { default = "eu-west-1" }
variable "environment"   { default = "prod" }
variable "project"       { default = "scnv" }
variable "db_password"   { sensitive = true }
variable "openai_api_key"{ sensitive = true }

# ============================================================
# VPC & NETWORKING
# ============================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name    = "${var.project}-vpc-${var.environment}"
  cidr    = "10.0.0.0/16"

  azs              = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets   = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  database_subnets = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  create_database_subnet_group = true
}

# ============================================================
# EKS CLUSTER (Agent Orchestration + FastAPI Backend)
# ============================================================
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.project}-eks-${var.environment}"
  cluster_version = "1.29"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

  eks_managed_node_groups = {
    # Agent workers: LangGraph + Python agents
    agents = {
      name           = "agent-workers"
      instance_types = ["c6i.2xlarge"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3
      labels = { role = "agent-worker" }
      taints = [{ key = "dedicated", value = "agents", effect = "NO_SCHEDULE" }]
    }
    # API workers: FastAPI backend
    api = {
      name           = "api-workers"
      instance_types = ["c6i.xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 2
      labels = { role = "api-worker" }
    }
    # General: frontend, monitoring
    general = {
      name           = "general"
      instance_types = ["t3.large"]
      min_size       = 1
      max_size       = 4
      desired_size   = 2
    }
  }
}

# ============================================================
# RDS POSTGRESQL + pgvector (Memory Layer)
# ============================================================
resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-postgres-${var.environment}"
  engine                  = "postgres"
  engine_version          = "16.1"
  instance_class          = "db.r6g.xlarge"
  allocated_storage       = 200
  max_allocated_storage   = 1000
  storage_encrypted       = true
  storage_type            = "gp3"

  db_name  = "scnv"
  username = "scnv_admin"
  password = var.db_password

  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = true
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "Sun:04:00-Sun:05:00"
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.project}-final-snapshot"

  performance_insights_enabled = true
  monitoring_interval          = 60

  # pgvector extension enabled via RDS parameter group
  parameter_group_name = aws_db_parameter_group.postgres_params.name
}

resource "aws_db_parameter_group" "postgres_params" {
  family = "postgres16"
  name   = "${var.project}-pg-params"
  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }
}

# Read replica for RAG queries (heavy reads)
resource "aws_db_instance" "postgres_replica" {
  identifier          = "${var.project}-postgres-replica-${var.environment}"
  replicate_source_db = aws_db_instance.postgres.identifier
  instance_class      = "db.r6g.large"
  publicly_accessible = false
  skip_final_snapshot = true
}

# ============================================================
# ELASTICACHE REDIS (Session + Cache)
# ============================================================
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project}-redis"
  description                = "SCNV Redis cache for sessions and agent state"
  node_type                  = "cache.r6g.large"
  port                       = 6379
  num_cache_clusters         = 3
  automatic_failover_enabled = true
  multi_az_enabled           = true
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project}-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

# ============================================================
# MSK KAFKA (Event Streaming - STO Events from SAP)
# ============================================================
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "${var.project}-kafka-${var.environment}"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = module.vpc.private_subnets
    storage_info {
      ebs_storage_info { volume_size = 500 }
    }
    security_groups = [aws_security_group.kafka.id]
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.scnv.arn
    encryption_in_transit {
      client_broker = "TLS"
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.kafka_config.arn
    revision = 1
  }
}

resource "aws_msk_configuration" "kafka_config" {
  kafka_versions = ["3.6.0"]
  name           = "${var.project}-kafka-config"
  server_properties = <<PROPERTIES
auto.create.topics.enable = false
default.replication.factor = 3
min.insync.replicas = 2
num.partitions = 12
log.retention.hours = 168
PROPERTIES
}

# Kafka topics
resource "aws_msk_scram_secret_association" "kafka_auth" {
  cluster_arn     = aws_msk_cluster.kafka.arn
  secret_arn_list = [aws_secretsmanager_secret.kafka_creds.arn]
}

# ============================================================
# ECR REPOSITORIES (Docker Images)
# ============================================================
locals {
  ecr_repos = [
    "scnv-fastapi-backend",
    "scnv-langgraph-agents",
    "scnv-react-frontend",
    "scnv-kafka-consumer"
  ]
}

resource "aws_ecr_repository" "repos" {
  for_each             = toset(local.ecr_repos)
  name                 = each.value
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration { scan_on_push = true }
  encryption_configuration     { encryption_type = "KMS" }
}

# ============================================================
# APPLICATION LOAD BALANCER
# ============================================================
resource "aws_lb" "main" {
  name               = "${var.project}-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  enable_deletion_protection = true
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.scnv.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# API target group
resource "aws_lb_target_group" "api" {
  name     = "${var.project}-api-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
  }
}

# Frontend target group
resource "aws_lb_target_group" "frontend" {
  name        = "${var.project}-frontend-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"
}

# ============================================================
# WAF (Web Application Firewall)
# ============================================================
resource "aws_wafv2_web_acl" "scnv" {
  name  = "${var.project}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 2
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitMetric"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "SCNVWAFMetric"
    sampled_requests_enabled   = true
  }
}

# ============================================================
# SECRETS MANAGER
# ============================================================
resource "aws_secretsmanager_secret" "scnv_secrets" {
  name                    = "${var.project}/prod/app-secrets"
  recovery_window_in_days = 30
}

resource "aws_secretsmanager_secret_version" "scnv_secrets" {
  secret_id = aws_secretsmanager_secret.scnv_secrets.id
  secret_string = jsonencode({
    DB_PASSWORD      = var.db_password
    OPENAI_API_KEY   = var.openai_api_key
    SLACK_BOT_TOKEN  = "REPLACE_ME"
    SAP_API_KEY      = "REPLACE_ME"
    CELONIS_TOKEN    = "REPLACE_ME"
    NEO4J_PASSWORD   = "REPLACE_ME"
  })
}

resource "aws_secretsmanager_secret" "kafka_creds" {
  name = "${var.project}/prod/kafka-credentials"
}

# ============================================================
# S3 BUCKETS
# ============================================================
resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project}-artifacts-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.scnv.arn
    }
  }
}

# ============================================================
# KMS KEY
# ============================================================
resource "aws_kms_key" "scnv" {
  description             = "SCNV production encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# ============================================================
# CLOUDWATCH MONITORING
# ============================================================
resource "aws_cloudwatch_dashboard" "scnv" {
  dashboard_name = "${var.project}-production-dashboard"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title   = "STO Classification Latency (p99)"
          metrics = [["SCNV/Agents", "ClassificationLatency", "Percentile", "p99"]]
          period  = 60
          stat    = "p99"
        }
      },
      {
        type = "metric"
        properties = {
          title   = "Auto-Execution Rate"
          metrics = [["SCNV/Agents", "AutoExecutionCount"], ["SCNV/Agents", "EscalationCount"]]
          period  = 300
        }
      },
      {
        type = "metric"
        properties = {
          title   = "API Request Rate + Error Rate"
          metrics = [["SCNV/API", "RequestCount"], ["SCNV/API", "ErrorCount"]]
          period  = 60
        }
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "classification_errors" {
  alarm_name          = "${var.project}-classification-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ClassificationErrors"
  namespace           = "SCNV/Agents"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "STO classification errors exceeded threshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_sns_topic" "alerts" {
  name              = "${var.project}-prod-alerts"
  kms_master_key_id = aws_kms_key.scnv.arn
}

# ============================================================
# ACM CERTIFICATE
# ============================================================
resource "aws_acm_certificate" "scnv" {
  domain_name       = "scnv.yourcompany.com"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

# ============================================================
# SECURITY GROUPS
# ============================================================
resource "aws_security_group" "alb" {
  name   = "${var.project}-alb-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "eks_workers" {
  name   = "${var.project}-eks-workers-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name   = "${var.project}-rds-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_workers.id]
  }
}

resource "aws_security_group" "redis" {
  name   = "${var.project}-redis-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_workers.id]
  }
}

resource "aws_security_group" "kafka" {
  name   = "${var.project}-kafka-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 9096
    to_port         = 9096
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_workers.id]
  }
}

# ============================================================
# IAM ROLES
# ============================================================
resource "aws_iam_role" "scnv_app" {
  name = "${var.project}-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scnv_secrets" {
  name = "${var.project}-secrets-policy"
  role = aws_iam_role.scnv_app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = [aws_secretsmanager_secret.scnv_secrets.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = ["${aws_s3_bucket.artifacts.arn}/*"]
      }
    ]
  })
}

# ============================================================
# DATA SOURCES
# ============================================================
data "aws_caller_identity" "current" {}

# ============================================================
# OUTPUTS
# ============================================================
output "eks_cluster_endpoint"     { value = module.eks.cluster_endpoint }
output "rds_endpoint"             { value = aws_db_instance.postgres.endpoint }
output "redis_endpoint"           { value = aws_elasticache_replication_group.redis.primary_endpoint_address }
output "kafka_bootstrap_brokers"  { value = aws_msk_cluster.kafka.bootstrap_brokers_tls }
output "alb_dns_name"             { value = aws_lb.main.dns_name }
