# vagrant box add fedora http://puppet-vagrant-boxes.puppetlabs.com/fedora-18-x64-vbox4210.box
Vagrant::Config.run do |config|

  config.vm.define 'gridz' do |gridz_config|
    gridz_config.vm.box = "fedora"
    gridz_config.vm.host_name = 'gridz'
    gridz_config.vm.forward_port 80, 8800
    gridz_config.vm.forward_port 5000, 5000
    gridz_config.vm.provision :puppet, :module_path => "modules" #, :options => "--verbose --debug"
    gridz_config.vm.share_folder "apps", "/home/vagrant/apps", "#{ ENV['HOME'] }/gridz/apps"
  end

end
