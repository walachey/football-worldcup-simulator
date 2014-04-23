directory node['wmsimulator']['qless_install_dir'] do
  recursive true
end

chef_gem 'bundler'
remote_directory node['wmsimulator']['qless_install_dir'] do
  source 'qless-server'
  notifies :run, 'execute[bundle install]', :immediately
end
execute 'bundle install' do
  command '/opt/chef/embedded/bin/bundle --binstubs --shebang=/opt/chef/embedded/bin/ruby --path vendor/bundle'
  cwd node['wmsimulator']['qless_install_dir']
  action :nothing
  notifies :restart, 'runit_service[qless-web]'
end

template ::File.join(node['wmsimulator']['qless_install_dir'], 'config.ru') do
  source 'qless-server/config.ru.erb'
  notifies :restart, 'runit_service[qless-web]'
end 

include_recipe 'runit::default'
runit_service 'qless-web' do
  default_logger true 
end


