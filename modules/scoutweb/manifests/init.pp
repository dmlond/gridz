class scoutweb {

  file {
    '/etc/httpd/conf.d/scoutweb.conf':
      owner => 'root',
      group => 'root',
      source => "puppet:///modules/scoutweb/scoutweb.conf",
      notify => Service['httpd'];
  }

  exec {
    'bundle_install':
      command => '/usr/local/bin/bundle install --gemfile=/home/vagrant/scoutweb/Gemfile',
      require => Exec['bundler_gem'];
  }
}
