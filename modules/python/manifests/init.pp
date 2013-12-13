class python {
  package {
    "python":
      ensure => true;
    "python-devel":
      ensure => true;
    "python-pip":
      ensure => true;
    "python-flask":
      ensure => true;
    "openssl":
      ensure => true;
    "openssl-devel":
      ensure => true;
    "libyaml-devel":
      ensure => true;
    "sqlite":
      ensure => true;
    "python-pyquery":
      ensure => true;
    "python-flask-wtf":
      ensure => true;
  }
}
