include_recipe 'apt'
include_recipe 'mysql::server'
include_recipe 'redisio::install'
include_recipe 'redisio::enable'
