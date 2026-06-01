resource_name_suffix = "afdap123987123"
location             = "West Europe"

tags = {
  Environment = "Dev"
  Project     = "Azure F1 Data & AI Platform"
  ManagedBy   = "Terraform"
}

network = {
  "generic" = {
    vnet_address_space = ["10.0.0.0/16"]
    snets = {
      "ingestion" = {
        snet_address_prefix = ["10.0.1.0/24"]
        delegation          = "Microsoft.App/environments"
        service_endpoints   = ["Microsoft.Storage"]
      }
    }
  }
}

sa_container_names = ["bronze", "silver", "gold"]

f1_api_ingestion_ci = {
  ci_name           = "f1_api_ingestion"
  start_season      = "2014"
  end_season        = "2025"
  sa_container_name = "bronze"
}

f1_transformation_ci = {
  ci_name           = "f1_to_silver"
  start_season      = "2014"
  end_season        = "2025"
}