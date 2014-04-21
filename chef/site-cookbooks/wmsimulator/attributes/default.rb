default['apache']['default_site_enabled'] = false

default['wmsimulator']['install_dir'] = '/opt/wmsimulator' 
default['wmsimulator']['web_install_dir'] = '/opt/wmsimulator/current/web' 
default['wmsimulator']['simulator_install_dir'] = '/opt/wmsimulator/current/simulation' 
default['wmsimulator']['log_dir'] = '/opt/wmsimulator/current/log' 
default['wmsimulator']['repository'] = 'https://github.com/walachey/football-worldcup-simulator.git' 
default['wmsimulator']['revision'] = 'master' 

default['wmsimulator']['admin_password'] = 'secret admin pw' 
default['wmsimulator']['session_key'] = 'lsgvbaapxljcvuafcroqoqvlgtymqtlmuqfwgadnlibsaucjnagdbdnfhryt'
default['wmsimulator']['database']['host'] = 'localhost'
default['wmsimulator']['database']['port'] = node['mysql']['port'].to_i
default['wmsimulator']['database']['name'] = 'worldcup'
default['wmsimulator']['database']['user'] = 'worldcup_admin'
default['wmsimulator']['database']['password'] = 'Ijd6387dBfuwP'
default['wmsimulator']['redis']['host'] = 'localhost'
default['wmsimulator']['redis']['port'] = 6379 
