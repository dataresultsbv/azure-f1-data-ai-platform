resource "azurerm_resource_group" "rg" {
  name     = "rg-${var.resource_name_suffix}"
  location = var.location
  tags     = var.tags
}