output "snet_ids" {
  value       = { for k, v in azurerm_subnet.snet : k => v.id }
  description = "Key value pairs of all subnets with name and id's"
}