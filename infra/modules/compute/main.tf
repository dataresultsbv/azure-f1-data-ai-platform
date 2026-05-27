resource "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = "laws-${var.resource_name_suffix}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_container_app_environment" "container_app_environment" {
  name                           = "cae-${var.resource_name_suffix}"
  location                       = var.location
  resource_group_name            = var.resource_group_name
  log_analytics_workspace_id     = azurerm_log_analytics_workspace.log_analytics_workspace.id
  infrastructure_subnet_id       = var.infra_subnet_id
  internal_load_balancer_enabled = true # Together with external_enabled in the container_app.ingress makes sure there is no public-ip
  tags                           = var.tags
}

resource "azurerm_container_app" "container_app" {
  name                         = "ca-f1-ingestion-${var.resource_name_suffix}"
  container_app_environment_id = azurerm_container_app_environment.container_app_environment.id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "f1-processor"
      image  = var.image_name
      cpu    = "0.25"
      memory = "0.5Gi"

      env {
        name  = "ENVIRONMENT"
        value = "dev"
      }
    }
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = false # Together with internal_load_balancer_enabled in the container_app_environment makes sure there is no public-ip
    target_port                = 80
    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
  tags = var.tags
}