# 1. USER-ASSIGNED MANAGED IDENTITIES
resource "azurerm_user_assigned_identity" "ingestion_identity" {
  name                = "id-f1-ingestion-${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "transformation_identity" {
  name                = "id-f1-transformation-${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "aggregation_identity" {
  name                = "id-f1-aggregation-${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

# 2. SHARED CONTAINER REGISTRY (Admin Access Explicitly Disabled)
resource "azurerm_container_registry" "container_registry" {
  name                = "acr${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

# 3. F1 INGESTION CONTAINER GROUP
resource "azurerm_container_group" "f1_ingestion_group" {
  name                = replace("ci-${var.f1_api_ingestion_ci.ci_name}-${var.resource_name_suffix}", "_", "-")
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.ingestion_identity.id]
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
    server                    = azurerm_container_registry.container_registry.login_server
    user_assigned_identity_id = azurerm_user_assigned_identity.ingestion_identity.id
  }
  tags = var.tags

  lifecycle {
    ignore_changes = [container[0].image]
  }
}

# 4. F1 TRANSFORMATION CONTAINER GROUP
resource "azurerm_container_group" "f1_transformation_group" {
  name                = replace("ci-${var.f1_transformation_ci.ci_name}-${var.resource_name_suffix}", "_", "-")
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.transformation_identity.id]
  }

  container {
    name   = replace(var.f1_transformation_ci.ci_name, "_", "-")
    image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
    cpu    = "0.5"
    memory = "1.0"

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      START_SEASON              = var.f1_transformation_ci.start_season
      END_SEASON                = var.f1_transformation_ci.end_season
      AZURE_STORAGE_ACCOUNT_URL = "https://${var.storage_account_name}.dfs.core.windows.net"
    }
  }

  image_registry_credential {
    server                    = azurerm_container_registry.container_registry.login_server
    user_assigned_identity_id = azurerm_user_assigned_identity.transformation_identity.id
  }
  tags = var.tags

  lifecycle {
    ignore_changes = [container[0].image]
  }
}

# 5. F1 AGGREGATION CONTAINER GROUP
resource "azurerm_container_group" "f1_aggregation_group" {
  name                = replace("ci-${var.f1_aggregation_ci.ci_name}-${var.resource_name_suffix}", "_", "-")
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aggregation_identity.id]
  }

  container {
    name   = replace(var.f1_aggregation_ci.ci_name, "_", "-")
    image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
    cpu    = "0.5"
    memory = "1.0"

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      START_SEASON              = var.f1_aggregation_ci.start_season
      END_SEASON                = var.f1_aggregation_ci.end_season
      AZURE_STORAGE_ACCOUNT_URL = "https://${var.storage_account_name}.dfs.core.windows.net"
    }
  }

  image_registry_credential {
    server                    = azurerm_container_registry.container_registry.login_server
    user_assigned_identity_id = azurerm_user_assigned_identity.aggregation_identity.id
  }
  tags = var.tags

  lifecycle {
    ignore_changes = [container[0].image]
  }
}

# 6. PERMISSIONS (RBAC) ON STORAGE & CONTAINER REGISTRY
data "azurerm_subscription" "current" {}

# Storage Assignments
resource "azurerm_role_assignment" "ingestion_to_storage" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Storage/storageAccounts/${var.storage_account_name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.ingestion_identity.principal_id
}

resource "azurerm_role_assignment" "transformation_to_storage" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Storage/storageAccounts/${var.storage_account_name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.transformation_identity.principal_id
}

resource "azurerm_role_assignment" "aggregation_to_storage" {
  scope                = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Storage/storageAccounts/${var.storage_account_name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.aggregation_identity.principal_id
}

resource "azurerm_role_assignment" "ingestion_to_acr" {
  scope                = azurerm_container_registry.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.ingestion_identity.principal_id
}

resource "azurerm_role_assignment" "transformation_to_acr" {
  scope                = azurerm_container_registry.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.transformation_identity.principal_id
}

resource "azurerm_role_assignment" "aggregation_to_acr" {
  scope                = azurerm_container_registry.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.aggregation_identity.principal_id
}