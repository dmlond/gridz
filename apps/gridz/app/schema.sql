drop table if exists schemas;
create table schemas (
  id integer primary key autoincrement,
  name varchar(255) not null,
  description text not null
);

drop table if exists grids;
create table grids (
  id integer primary key autoincrement,
  schema_id integer not null,
  name varchar(255) not null,
  description text not null
);

drop table if exists grid_fields;
create table grid_fields (
  id integer primary key autoincrement,
  grid_id integer not null,
  name varchar(255) not null,
  is_attribute boolean,
  is_filter boolean
);
