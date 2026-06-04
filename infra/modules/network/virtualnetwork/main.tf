# 1. Maak de VNets aan (eenvoudige loop over de buitenste map)
resource "azurerm_virtual_network" "vnet" {
  for_each = {
    for vnet in var.vnet_details : vnet.vnet_name => vnet
  }
  name                = "vnet-${each.key}-${var.resource_name_suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  address_space       = each.value.vnet_address_space
  tags                = var.tags
}

resource "azurerm_subnet" "snet" {
  for_each = {
    for subnet in var.snet_details : subnet.snet_name => subnet
  }

  name                 = "snet-${each.key}-${var.resource_name_suffix}"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet[each.value.vnet_name].name
  address_prefixes     = each.value.snet_address_prefix
  service_endpoints    = each.value.service_endpoints

  dynamic "delegation" {
    for_each = each.value.snet_delegation != null ? [1] : []
    content {
      name = "${each.value.snet_name}-delegation"
      service_delegation {
        name    = each.value.snet_delegation
        actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
      }
    }
  }
}