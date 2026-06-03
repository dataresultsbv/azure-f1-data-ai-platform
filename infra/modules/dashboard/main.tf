resource "azurerm_static_web_app" "evidence_dashboard" {
  name                = "swa-f1-dashboard-${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku_tier            = "Free"
  sku_size            = "Free"
  tags                = var.tags
}