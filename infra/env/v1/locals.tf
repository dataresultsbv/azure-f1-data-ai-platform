locals {
  vnet_flat = (flatten([
    for vnet_key, vnet_val in var.network :
    {
      vnet_name          = vnet_key
      vnet_address_space = vnet_val.vnet_address_space
    }
  ]))

  subnet_flat = flatten([
    for vnet_key, vnet_val in var.network : [
      for snet_key, snet_val in vnet_val.snets : {
        vnet_name           = vnet_key
        snet_name           = snet_key
        snet_address_prefix = snet_val.snet_address_prefix
        snet_delegation     = snet_val.delegation
        service_endpoints   = snet_val.service_endpoints
      }
    ]
  ])
}