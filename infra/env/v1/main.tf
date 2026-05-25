module "resource_group" {
    source               = "../../modules/general/resourcegroup"

    resource_name_suffix = var.resource_name_suffix
    location             = var.location
    tags                 = var.tags
}