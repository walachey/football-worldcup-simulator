#install python from package
include_recipe 'python::package'
#install pip from source
include_recipe 'python::pip'
#install python dependencies
%w{decorator qless-py}.each do |python_pkg|
  python_pip python_pkg
end

package 'git'

apt_repository 'ubuntu-toolchain-r-test-precise' do
  uri 'http://ppa.launchpad.net/ubuntu-toolchain-r/test/ubuntu'
  distribution node['lsb']['codename'] 
  components ['main']
  keyserver 'keyserver.ubuntu.com'
  key 'BA9EF27F'
end

package 'gcc-4.8' do
  action :install
  notifies :run, 'bash[update-alternatives gcc]', :immediately
end

bash 'update-alternatives gcc' do
  code <<-EOT
    update-alternatives --remove-all gcc
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 20
    update-alternatives --config gcc
  EOT
  action :nothing
end

package 'g++-4.8' do
  action :install
  notifies :run, 'bash[update-alternatives g++]', :immediately
end

bash 'update-alternatives g++' do
  code <<-EOT
    update-alternatives --remove-all g++
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 20
    update-alternatives --config g++
  EOT
  action :nothing
end

deploy_revision 'simulator' do
  deploy_to node['wmsimulator']['simulator_install_base']
  repository node['wmsimulator']['repository'] 
  revision node['wmsimulator']['revision'] 
  migrate false 
  symlink_before_migrate({})
  enable_submodules true
  create_dirs_before_symlink []
  symlinks({})
  notifies :run, 'bash[build simulator]', :immediately
end

bash 'build simulator' do
  code <<-EOT
    mkdir -p obj 
    make
  EOT
  cwd node['wmsimulator']['simulator_install_dir']
  action :nothing
end

template ::File.join(node['wmsimulator']['worker_install_dir'], 'simulation_job_config.py') do
  source 'simulation_job_config.py.erb'
  mode 0644
end

include_recipe 'runit::default'
runit_service 'simulator' do
  default_logger true 
end
