--
-- PostgreSQL database dump
--

-- Dumped from database version 9.1.19
-- Dumped by pg_dump version 9.1.19
-- Started on 2016-05-13 20:23:50 BRT

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 166 (class 3079 OID 11679)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 1921 (class 0 OID 0)
-- Dependencies: 166
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 165 (class 1259 OID 16430)
-- Dependencies: 5
-- Name: change_points; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE change_points (
    id_user bigint,
    id_time_series bigint,
    change_points text
);


ALTER TABLE public.change_points OWNER TO postgres;

--
-- TOC entry 164 (class 1259 OID 16419)
-- Dependencies: 5
-- Name: time_series; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE time_series (
    id bigint NOT NULL,
    mac text,
    server text,
    csv_path text,
    date_start text,
    date_end text
);


ALTER TABLE public.time_series OWNER TO postgres;

--
-- TOC entry 163 (class 1259 OID 16417)
-- Dependencies: 5 164
-- Name: probes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE probes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.probes_id_seq OWNER TO postgres;

--
-- TOC entry 1922 (class 0 OID 0)
-- Dependencies: 163
-- Name: probes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE probes_id_seq OWNED BY time_series.id;


--
-- TOC entry 162 (class 1259 OID 16406)
-- Dependencies: 5
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    id bigint NOT NULL,
    email text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 161 (class 1259 OID 16404)
-- Dependencies: 162 5
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 1923 (class 0 OID 0)
-- Dependencies: 161
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- TOC entry 1799 (class 2604 OID 16422)
-- Dependencies: 163 164 164
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY time_series ALTER COLUMN id SET DEFAULT nextval('probes_id_seq'::regclass);


--
-- TOC entry 1798 (class 2604 OID 16409)
-- Dependencies: 161 162 162
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- TOC entry 1913 (class 0 OID 16430)
-- Dependencies: 165 1914
-- Data for Name: change_points; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY change_points (id_user, id_time_series, change_points) FROM stdin;
\.


--
-- TOC entry 1924 (class 0 OID 0)
-- Dependencies: 163
-- Name: probes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('probes_id_seq', 3854, true);


--
-- TOC entry 1912 (class 0 OID 16419)
-- Dependencies: 164 1914
-- Data for Name: time_series; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY time_series (id, mac, server, csv_path, date_start, date_end) FROM stdin;
\.


--
-- TOC entry 1910 (class 0 OID 16406)
-- Dependencies: 162 1914
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY users (id, email) FROM stdin;
\.


--
-- TOC entry 1925 (class 0 OID 0)
-- Dependencies: 161
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('users_id_seq', 19, true);


--
-- TOC entry 1805 (class 2606 OID 16447)
-- Dependencies: 164 164 1915
-- Name: time_series_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY time_series
    ADD CONSTRAINT time_series_pkey PRIMARY KEY (id);


--
-- TOC entry 1801 (class 2606 OID 16416)
-- Dependencies: 162 162 1915
-- Name: users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 1803 (class 2606 OID 16414)
-- Dependencies: 162 162 1915
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 1807 (class 2606 OID 16453)
-- Dependencies: 164 165 1804 1915
-- Name: change_points_id_time_series_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY change_points
    ADD CONSTRAINT change_points_id_time_series_fkey FOREIGN KEY (id_time_series) REFERENCES time_series(id);


--
-- TOC entry 1806 (class 2606 OID 16448)
-- Dependencies: 165 1802 162 1915
-- Name: change_points_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY change_points
    ADD CONSTRAINT change_points_id_user_fkey FOREIGN KEY (id_user) REFERENCES users(id);


--
-- TOC entry 1920 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2016-05-13 20:23:50 BRT

--
-- PostgreSQL database dump complete
--

