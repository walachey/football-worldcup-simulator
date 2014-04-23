default['apache']['default_site_enabled'] = false

default['wmsimulator']['web_install_base'] = '/opt/wmsimulator/web' 
default['wmsimulator']['web_install_dir'] = ::File.join node['wmsimulator']['web_install_base'], 'current', 'web'
default['wmsimulator']['simulator_install_base'] = '/opt/wmsimulator/simulation' 
default['wmsimulator']['simulator_install_dir'] =  ::File.join node['wmsimulator']['simulator_install_base'], 'current', 'simulation'
default['wmsimulator']['worker_install_dir'] =  ::File.join node['wmsimulator']['simulator_install_base'], 'current', 'worker'
default['wmsimulator']['qless_install_dir'] = '/opt/wmsimulator/qless-web' 
default['wmsimulator']['repository'] = 'https://github.com/databus23/football-worldcup-simulator.git' 
default['wmsimulator']['revision'] = 'master' 
default['wmsimulator']['thread_count'] = 8

default['wmsimulator']['admin_password'] = 'secret admin pw' 
default['wmsimulator']['session_key'] = 'lsgvbaapxljcvuafcroqoqvlgtymqtlmuqfwgadnlibsaucjnagdbdnfhryt'
default['wmsimulator']['database']['host'] = 'localhost'
default['wmsimulator']['database']['port'] = node['mysql']['port'].to_i
default['wmsimulator']['database']['name'] = 'worldcup'
default['wmsimulator']['database']['user'] = 'worldcup_admin'
default['wmsimulator']['database']['password'] = 'Ijd6387dBfuwP'
default['wmsimulator']['redis']['host'] = 'localhost'
default['wmsimulator']['redis']['port'] = 6379 
