deploy_revision 'wmsimulator' do
  deploy_to node['wmsimulator']['install_dir']
  repository node['wmsimulator']['repository'] 
  revision node['wmsimulator']['revision'] 
  migrate false
  symlink_before_migrate({})
  create_dirs_before_symlink []
  symlinks({
    'log' => 'log',
    'configuration_custom.py' => 'web/configuration_custom.py',
  })
end
