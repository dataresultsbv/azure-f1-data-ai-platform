module "resource_group" {
    source               = "../../modules/general/resourcegroup"

    resource_name_suffix = var.resource_name_suffix
    location             = var.location
    tags                 = var.tags
}

module "network" {
    source               = "../../modules/network/virtualnetwork"

    resource_group_name  = module.resource_group.resource_group_name
    resource_name_suffix = var.resource_name_suffix
    location             = var.location
    vnet_details        = local.vnet_flat
    snet_details        = local.subnet_flat
    tags                 = var.tags
    depends_on           = [ module.resource_group ]
}