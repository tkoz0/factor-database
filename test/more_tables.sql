-- these tables are planned to be added later
-- currently they are not included because they are not used

-- ====================
-- contribution details
-- ====================

create table contributions
(
    id bigserial primary key unique not null,
    user_id bigint,
    -- details that may be included
    software text,
    hardware text,
    ecm_b1 bigint,
    ecm_sigma text,
    nfs_poly text,
    other text,
    date date,
    foreign key (user_id) references users(id)
);
create index contributions_user_id_index on contributions(user_id);

-- =====================
-- ecm progress tracking
-- =====================

create table ecm_runs
(
    user_id bigint not null,
    factor_id bigint not null,
    ecm_b1 int not null,
    num_runs bigint,
    unique (user_id,factor_id,ecm_b1),
    foreign key (user_id) references users(id),
    foreign key (factor_id) references factors(id)
);
create index ecm_runs_factor_index on ecm_runs(factor_id);

-- ======================
-- factoring reservations
-- ======================

create table reservations
(
    factor_id bigint unique not null,
    user_id bigint not null,
    reserved timestamp default timezone('utc',now()) not null,
    expires timestamp,
    foreign key (factor_id) references factors(id),
    foreign key (user_id) references users(id)
);
create index reservations_user_id_index on reservations(user_id);
