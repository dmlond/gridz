class httpd {
  package {
    "httpd":
      ensure => true;
    "httpd-devel":
      ensure => true;
    "apr":
      ensure => true;
    "apr-devel":
      ensure => true;
    "apr-util-devel":
      ensure => true;
  }

  service {
    "httpd":
      ensure => "running",
      require => Package['httpd','httpd-devel','apr','apr-devel','apr-util-devel'];
    "firewalld":
      ensure => "stopped";
  }
}
