variable "resource_name_suffix" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "storage_account_name" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "container_image"{
  type = map(object(
    {
      start_season = string
      end_season = string
      sa_container_name = string
    }
  ))
}