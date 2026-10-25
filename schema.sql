-- Table: public.users

-- DROP TABLE IF EXISTS public.users;

CREATE TABLE IF NOT EXISTS public.users
(
    id serial PRIMARY KEY,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    email character varying(255) COLLATE pg_catalog."default" NOT NULL,
    password_hash text COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.users
    OWNER to fit;

-- Table: public.sessions

-- DROP TABLE IF EXISTS public.sessions;

CREATE TABLE IF NOT EXISTS public.sessions
(
    id serial PRIMARY KEY,
    token_hash character varying(64) COLLATE pg_catalog."default" NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT sessions_pkey PRIMARY KEY (id),
    CONSTRAINT sessions_token_hash_key UNIQUE (token_hash),
    CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.sessions
    OWNER to fit;

    -- Table: public.workouts

-- DROP TABLE IF EXISTS public.workouts;

CREATE TABLE IF NOT EXISTS public.workouts
(
    id serial PRIMARY KEY,
    user_id integer NOT NULL,
    title character varying(200) COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    note text COLLATE pg_catalog."default",
    CONSTRAINT workouts_pkey PRIMARY KEY (id),
    CONSTRAINT workouts_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.workouts
    OWNER to fit;

    -- Table: public.workout_exercises

-- DROP TABLE IF EXISTS public.workout_exercises;

CREATE TABLE IF NOT EXISTS public.workout_exercises
(
    id serial PRIMARY KEY,
    workout_id integer NOT NULL,
    name character varying(200) COLLATE pg_catalog."default" NOT NULL,
    sets integer NOT NULL,
    reps integer NOT NULL,
    weight numeric(7,2),
    CONSTRAINT workout_exercises_pkey PRIMARY KEY (id),
    CONSTRAINT workout_exercises_workout_id_fkey FOREIGN KEY (workout_id)
        REFERENCES public.workouts (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT workout_exercises_reps_check CHECK (reps >= 1 AND reps <= 100),
    CONSTRAINT workout_exercises_sets_check CHECK (sets >= 1 AND sets <= 20),
    CONSTRAINT workout_exercises_weight_check CHECK (weight >= 0::numeric)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.workout_exercises
    OWNER to fit;