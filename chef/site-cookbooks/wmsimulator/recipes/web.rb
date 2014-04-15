include_recipe 'apt::default'
include_recipe 'apache2::default'
include_recipe 'apache2::mod_wsgi'
include_recipe 'mysql::client'


include_recipe 'python::package'

package 'git'

deploy_revision node['wmsimulator']['install_path'] do
  repository node['wmsimulator']['repository'] 
  revision node['wmsimulator']['revision'] 
  migrate false
  symlink_before_migrate({})
end


