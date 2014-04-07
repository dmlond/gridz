class mongo {
  package {
    'mongodb':
      ensure => true;
    'mongodb-server':
      ensure => true;
    'python-pymongo':
      ensure => true;
  }

  service {
    'mongod':
      ensure => 'running',
      require => Package['mongodb-server'];
  }
}
