alter table administration.users
    add constraint users_username_pk
        unique (username);