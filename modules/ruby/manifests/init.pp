class ruby {
  package {
    "ruby":
      ensure => true;
    "ruby-devel":
      ensure => true;
    "rubygems":
      ensure => true;
    "bundler":
      ensure   => 'installed',
      provider => 'gem';
    "rails":
      ensure => 'installed',
      provider => 'gem';
  }
}
