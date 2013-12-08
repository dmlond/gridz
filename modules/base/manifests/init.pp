class base {
  package {
    "gcc":
      ensure => true;
    "make":
      ensure => true;
    "gcc-c++":
      ensure => true;
    "zlib-devel":
      ensure => true;
    "readline-devel":
      ensure => true;
    'libcurl-devel':
      ensure => true;
  }
}
