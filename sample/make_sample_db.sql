-- resets the database used for testing
drop database if exists test_fdb;
drop user if exists test_fdb;
create user test_fdb with encrypted password 'test_fdb';
create database test_fdb with owner test_fdb;
\c test_fdb
set role test_fdb;
