resource "azurerm_container_registry" "container_registry" {

  name                = "acr${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = var.tags
}

resource "azurerm_container_group" "f1_container_group" {
  name                = replace("ci-${var.f1_api_ingestion_ci.ci_name}-${var.resource_name_suffix}", "_", "-")
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"

  identity {
    type = "SystemAssigned"
  }

  container {
    name   = replace(var.f1_api_ingestion_ci.ci_name, "_", "-")
    image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
    cpu    = "0.5"
    memory = "1.0"

  ports {
      port     = 443
      protocol = "TCP"
    }

    environment_variables = {
      START_SEASON         = var.f1_api_ingestion_ci.start_season
      END_SEASON           = var.f1_api_ingestion_ci.end_season
      STORAGE_ACCOUNT_NAME = var.storage_account_name
      CONTAINER_NAME       = var.f1_api_ingestion_ci.sa_container_name
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.container_registry.login_server
    username = azurerm_container_registry.container_registry.admin_username
    password = azurerm_container_registry.container_registry.admin_password
  }
  tags = var.tags

  lifecycle {
    ignore_changes = [
      container[0].image
    ]
  }
}

data "azurerm_subscription" "current" {}

resource "azurerm_role_assignment" "aci_to_bronze" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Storage/storageAccounts/${var.storage_account_name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_container_group.f1_container_group.identity[0].principal_id
}