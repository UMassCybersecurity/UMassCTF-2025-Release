CREATE DATABASE flashgamestudio;
\c flashgamestudio;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    uid varchar(255)  UNIQUE NOT NULL,
    username varchar(255) PRIMARY KEY,
    password varchar(255) NOT NULL,
    user_desc text NOT NULL,
    role_id smallint NOT NULL
);

CREATE TABLE games (
    code text NOT NULL,
    game_name varchar(255) NOT NULL,
    game_desc varchar(255) NOT NULL,
    username varchar(255) REFERENCES users
);

INSERT INTO users VALUES(
    uuid_generate_v4(),
    'admin',
    '1Mp0ss1bl3_t0_gu3ss_h0p3fully!11!_812yifdehwbgfdahj',
    'i am the admin',
    3
);

INSERT INTO games VALUES(
    'UMASS{CR0SS_th3_fl4sH_g4m3_t0_1nj3ct_Pyth0n!1!!11}',
    'best game ever',
    'the best game ever',
    'admin'
);