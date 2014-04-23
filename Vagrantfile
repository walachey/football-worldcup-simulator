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

  config.librarian_chef.cheffile_dir = "chef" if Vagrant.has_plugin?("vagrant-librarian-chef-nochef")
  #default chef config as proc we later call
  chef_defaults = Proc.new do |chef| 
    chef.custom_config_path = "chef/chef-solo.vagrant.conf"
    chef.log_level = ENV['CHEF_LOG'] || 'info'
    chef.cookbooks_path = %w{chef/cookbooks chef/site-cookbooks}
    #chef.roles_path = "chef/roles"
    #dynamically create a nested hash
    chef.json = JSON.parse(File.read 'chef/deploy.json') if File.exists? 'chef/deploy.json'
    chef.json.default_proc = proc { |l, k| l[k] = Hash.new(&l.default_proc) }
  end

  #everything on one box
  config.vm.define "allinone", primary: true do |allinone|
    allinone.vm.hostname = "hostname"
    allinone.vm.network "forwarded_port", guest: 80, host: 8080
    allinone.vm.network "forwarded_port", guest: 9292, host: 8081
    allinone.vm.provision "chef_solo" do |allinone_chef|
      chef_defaults.call allinone_chef
      allinone_chef.add_recipe "wmsimulator::allinone"
      allinone_chef.json['wmsimulator']['database']['host'] = 'localhost'
      allinone_chef.json['redisio']['servers'] = [port: 6379, address:"127.0.0.1"]
    end
  end

  #This machine only contains the webserver
  config.vm.define "web" do |web|
    web.vm.hostname = "web"
    web.vm.network "forwarded_port", guest: 80, host: 8080
    web.vm.network "forwarded_port", guest: 9292, host: 8081
    web.vm.provision "chef_solo" do |web_chef|
      chef_defaults.call web_chef
      web_chef.add_recipe "wmsimulator::web"
      web_chef.add_recipe "wmsimulator::qless-web"
    end
  end

  #This machine only contains the mysql and redis server
  config.vm.define "db" do |db|
    db.vm.hostname = "db"
    db.vm.provision "chef_solo" do |db_chef|
      chef_defaults.call db_chef
      db_chef.add_recipe "wmsimulator::database"
      db_chef.json['wmsimulator']['database']['host'] = 'localhost'
    end
  end

  #this machine only contains the simulator/qless worker
  config.vm.define "worker" do |worker|
    worker.vm.hostname = "worker"
    worker.vm.provision "chef_solo" do |worker_chef|
      chef_defaults.call worker_chef
      worker_chef.add_recipe "wmsimulator::worker"
    end
  end

end
