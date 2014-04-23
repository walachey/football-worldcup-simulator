# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.
  config.omnibus.chef_version = '11.12.2' 
  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "chef/ubuntu-12.04"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 9292, host: 8081

  config.vm.provision "chef_solo" do |chef|
    config.librarian_chef.cheffile_dir = "chef" if Vagrant.has_plugin?("vagrant-librarian-chef-nochef")
    chef.custom_config_path = "chef/chef-solo.vagrant.conf"
    chef.log_level = ENV['CHEF_LOG'] || 'info'
    chef.cookbooks_path = %w{chef/cookbooks chef/site-cookbooks}
    #chef.roles_path = "chef/roles"
    chef.add_recipe "wmsimulator::allinone"
  #
  #   # You may also specify custom JSON attributes:
    chef.json = { :mysql_password => "foo" }
  end

end
