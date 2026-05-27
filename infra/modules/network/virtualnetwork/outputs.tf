output "snet_ids" {
  value       = { for k, v in azurerm_subnet.snet : k => v.id }
  description = "Key value pairs of all subnets with name and id's"
}

output "vnet_ids" {
  value       = { for k, v in azurerm_virtual_network.vnet : k => v.id }
  description = "Key value pairs of all VNets with name and id's"
}