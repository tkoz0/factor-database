-- =============================================================================
-- Factor Database PostgreSQL Schema
-- creates the tables for the initial database setup
-- =============================================================================

create table logs
(
    text text not null,
    level int not null,
    time timestamp default timezone('utc',now()) not null,
    constraint check_level check (level in (0,1,2))
);

-- ==================
-- factorization data
-- ==================

-- nontrivial factorization results
create table factors
(
    id bigserial primary key unique not null,
    -- big endian integer value, no leading zero bytes
    value bytea unique not null,
    -- -1 = unknown, 0 = composite, 1 = probable prime, 2 = proven prime
    primality int default -1 not null,
    -- value = factor1 * factor2 (reference factorization if known)
    -- factor1 should be the smallest known factor (which can change)
    f1_id bigint default null, f2_id bigint default null,
    created timestamp default timezone('utc',now()) not null,
    modified timestamp default timezone('utc',now()) not null,
    constraint check_primality check (primality in (-1,0,1,2)),
    constraint check_factor_ids check (
        -- both null or both non null
        (f1_id = null and f2_id = null) or
        -- primality must be composite if number is factored
        (primality = 0 and f1_id <> null and f2_id <> null)),
    constraint check_value check (
        length(value) > 0 and substr(value,1,1) <> '\x00'::bytea),
    foreign key (f1_id) references factors(id),
    foreign key (f2_id) references factors(id)
);
create index factors_f1id_index on factors(f1_id);
create index factors_f2id_index on factors(f2_id);
create index factors_value_len on factors(length(value));

-- starting numbers to factor (the nicely chosen ones)
create table numbers
(
    id bigserial primary key unique not null,
    -- big endian integer value, no leading zero bytes
    value bytea unique not null,
    -- small prime factors as 2/4/8 byte values (big endian)
    -- 2 byte values from automatic trial division
    -- 4/8 byte values stored afterward to optimize
    spf2 bytea, spf4 bytea, spf8 bytea,
    -- reference factors table for nontrivial factorization
    cof_id bigint default null,
    -- is factorization complete
    complete boolean default false not null,
    created timestamp default timezone('utc',now()) not null,
    modified timestamp default timezone('utc',now()) not null,
    constraint check_value check (
        length(value) > 0 and substr(value,1,1) <> '\x00'::bytea),
    constraint check_spf2 check (spf2 = null or length(spf2) % 2 = 0),
    constraint check_spf4 check (spf4 = null or length(spf4) % 4 = 0),
    constraint check_spf8 check (spf8 = null or length(spf8) % 8 = 0),
    foreign key (cof_id) references factors(id)
);
create index numbers_cofactor_index on numbers(cof_id);
create index numbers_value_len on numbers(length(value));

-- store old factorizations if a smaller f1 is found
-- which replaces a previous factorization in the factors table
create table factors_old
(
    fac_id bigint not null,
    f1_id bigint not null,
    f2_id bigint not null,
    unique (fac_id,f1_id,f2_id),
    foreign key (fac_id) references factors(id),
    foreign key (f1_id) references factors(id),
    foreign key (f2_id) references factors(id)
);
create index factors_old_f0_index on factors_old(fac_id);
create index factors_old_f1_index on factors_old(f1_id);
create index factors_old_f2_index on factors_old(f2_id);

-- ====================
-- numbers organization
-- ====================

-- category is either a directory listing of subcategories
-- or a table listing a number sequence
create table categories
(
    id bigserial primary key unique not null,
    -- parent id (root points to self)
    parent_id bigint not null,
    -- number for ordering
    order_num bigint default null,
    -- name for path
    name text not null,
    -- name displayed on pages
    title text not null,
    is_table boolean not null,
    -- text body for details
    info text not null,
    -- expression for nth term
    expr text,
    created timestamp default timezone('utc',now()) not null,
    modified timestamp default timezone('utc',now()) not null,
    constraint check_name check (
        (id = 0 and name = '') or
        (name ~ '^[\w\+\-\=][\w\+\-\=\.]*$')),
    constraint check_parent check (id = 0 or id <> parent_id),
    unique (parent_id,name),
    foreign key (parent_id) references categories(id)
);
-- setup root category using reserved id = 0
insert into categories (id,parent_id,name,title,is_table,info)
values (0,0,'','Factor Tables',false,'');

-- information for a number sequence
create table sequences
(
    cat_id bigint not null,
    -- index in the seqquence
    index bigint not null,
    num_id bigint,
    -- value for nonpositive numbers
    value text,
    -- expression for this number
    expr text,
    unique (cat_id,index),
    constraint check_index check (index >= 0),
    constraint check_value check (value ~ '^\-?\d+$'),
    foreign key (cat_id) references categories(id),
    foreign key (num_id) references numbers(id)
);
create index sequences_num_id_index on sequences(num_id);

-- =============
-- user accounts
-- =============

create table users
(
    id bigserial primary key unique not null,
    username text unique,
    email text unique,
    fullname text default '' not null,
    pwd_hash bytea not null,
    pwd_salt bytea not null,
    created timestamp default timezone('utc',now()) not null,
    modified timestamp default timezone('utc',now()) not null,
    last_login timestamp default null,
    is_disabled boolean default false not null,
    is_admin boolean default false not null,
    api_key bytea unique,
    constraint check_pwd_hash check (length(pwd_hash) = 64),
    constraint check_pwd_salt check (length(pwd_salt) = 64),
    constraint check_username check (
        (username ~ '^\w+$') and length(username) <= 32),
    constraint check_email check (email ~ '^[\w\-\.]+@[\w\-]+(\.[\w\-]+)+$')
);

create table sessions
(
    user_id bigint not null,
    -- user cookie stores token, server stores token hash
    token_hash bytea unique not null,
    created timestamp default timezone('utc',now()) not null,
    expires timestamp not null,
    accessed timestamp default timezone('utc',now()) not null,
    last_ip inet default null,
    constraint check_token check (length(token_hash) = 64),
    foreign key (user_id) references users(id)
);
create index sessions_user_id_index on sessions(user_id);

-- ==================
-- factor submissions
-- ==================

-- submitted results, should remove once necessary data is collected
create table submissions
(
    id bigserial primary key unique not null,
    fac_id bigint,
    user_id bigint,
    text_name text not null,
    text_factors text not null,
    text_details text not null,
    submitted timestamp default timezone('utc',now()) not null,
    from_ip inet,
    foreign key (fac_id) references factors(id),
    foreign key (user_id) references users(id)
);
create index submissions_user_index on submissions(user_id);
create index submissions_facid_index on submissions(fac_id);
