resource "azurerm_container_registry" "container_registry" {

  name                = "acr${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = var.tags
}

output "acr_login_server" {
  value = azurerm_container_registry.container_registry.login_server
}

output "acr_admin_username" {
  value = azurerm_container_registry.container_registry.admin_username
}

output "acr_admin_password" {
  value     = azurerm_container_registry.container_registry.admin_password
  sensitive = true
}