include_recipe 'apt::default'
include_recipe 'apache2::default'
include_recipe 'apache2::mod_wsgi'
include_recipe 'mysql::client'

#install python from package
include_recipe 'python::package'
#install pip from source
include_recipe 'python::pip'
#install python dependencies
%w{Flask  Flask-SQLAlchemy Flask-Admin  Flask-Cache  MySQL-python qless-py decorator}.each do |python_pkg|
  python_pip python_pkg
end

#ensure git is installed
package 'git'

directory ::File.join node['wmsimulator']['web_install_base'], 'shared/log' do
  recursive true
  owner 'www-data'
end

template ::File.join node['wmsimulator']['web_install_base'], 'shared/configuration_custom.py'  do
  source 'configuration.py.erb'
  notifies :reload, 'service[apache2]'
end

deploy_revision 'web' do
  deploy_to node['wmsimulator']['web_install_base']
  repository node['wmsimulator']['repository'] 
  revision node['wmsimulator']['revision'] 
  migrate true 
  migration_command "python web/defaults.py"
  symlink_before_migrate({
    'configuration_custom.py' => 'web/configuration_custom.py'
  })
  create_dirs_before_symlink []
  symlinks({
    'log' => 'log',
  })
  notifies :reload, 'service[apache2]'
end

#drop apache virtual host configuration
template "#{node['apache']['dir']}/sites-available/wmsimulator" do
  source 'apache_site.conf.erb'
  mode 0644
  notifies :reload, 'service[apache2]' 
end
apache_site 'wmsimulator' do
  action :enable
end
