# Haal ip adres van laptop op ivm lokaal testen
data "http" "my_public_ip" {
  url = "https://ifconfig.me/ip"
}

module "resource_group" {
  source = "../../modules/general/resourcegroup"

  resource_name_suffix = var.resource_name_suffix
  location             = var.location
  tags                 = var.tags
}

module "network" {
  source = "../../modules/network/virtualnetwork"

  resource_group_name  = module.resource_group.resource_group_name
  resource_name_suffix = var.resource_name_suffix
  location             = var.location
  vnet_details         = local.vnet_flat
  snet_details         = local.subnet_flat
  tags                 = var.tags

  depends_on = [module.resource_group]
}

module "storage" {
  source = "../../modules/storage"

  resource_group_name  = module.resource_group.resource_group_name
  resource_name_suffix = var.resource_name_suffix
  location             = var.location
  allowed_ip_ranges    = [chomp(data.http.my_public_ip.response_body)]
  allowed_subnet_ids   = [for snet in local.subnet_flat : module.network.snet_ids[snet.snet_name]]
  tags                 = var.tags

  depends_on = [module.network]
}

module "compute" {
  source               = "../../modules/compute"
  resource_group_name  = module.resource_group.resource_group_name
  resource_name_suffix = var.resource_name_suffix
  location             = var.location
  infra_subnet_id      = module.network.snet_ids["ingestion"]
  tags                 = var.tags

  depends_on = [module.network]
}

module "registry" {
  source               = "../../modules/registry"
  resource_group_name  = module.resource_group.resource_group_name
  resource_name_suffix = var.resource_name_suffix
  location             = var.location
  tags                 = var.tags

  depends_on = [module.network]
}