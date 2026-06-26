--
-- PostgreSQL database dump
--

\restrict zHKIkcIZPBcetzFgbVOksg2ZTDdbyxfpocgmoNxI3RaKkZtj5HAWPdRnPJ2p7LA

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(128) NOT NULL
);


--
-- Name: app_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_settings (
    id integer NOT NULL,
    key character varying(100) NOT NULL,
    value text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: app_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: app_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.app_settings_id_seq OWNED BY public.app_settings.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    username character varying(100),
    action character varying(100) NOT NULL,
    entity_type character varying(100),
    entity_id character varying(100),
    ip_address character varying(100),
    user_agent character varying(500),
    details text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    department_id integer
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: barcode_code_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.barcode_code_catalog (
    id integer NOT NULL,
    code character varying(20) NOT NULL,
    name character varying(255),
    category character varying(100),
    status character varying(50) DEFAULT 'available'::character varying NOT NULL,
    owner character varying(255),
    notes text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_barcode_code_catalog_status_allowed CHECK (((status)::text = ANY ((ARRAY['available'::character varying, 'active'::character varying, 'reserved'::character varying, 'blocked'::character varying, 'deprecated'::character varying])::text[])))
);


--
-- Name: barcode_code_catalog_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.barcode_code_catalog_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: barcode_code_catalog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.barcode_code_catalog_id_seq OWNED BY public.barcode_code_catalog.id;


--
-- Name: barcode_counters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.barcode_counters (
    id integer NOT NULL,
    package_type character varying(20) NOT NULL,
    current_value integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    region_code character varying(2) NOT NULL
);


--
-- Name: barcode_counters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.barcode_counters_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: barcode_counters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.barcode_counters_id_seq OWNED BY public.barcode_counters.id;


--
-- Name: barcode_ranges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.barcode_ranges (
    id integer NOT NULL,
    package_type character varying(20) NOT NULL,
    start_number integer NOT NULL,
    end_number integer NOT NULL,
    current_number integer NOT NULL,
    status character varying(50) DEFAULT 'active'::character varying NOT NULL,
    issued_to_client_id integer,
    issued_to_department_id integer,
    request_id integer,
    issued_by integer,
    issued_at timestamp with time zone,
    expires_at timestamp with time zone,
    notes text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    cancellation_reason text,
    cancelled_by integer,
    cancelled_at timestamp with time zone,
    region_code character varying(2),
    CONSTRAINT ck_barcode_ranges_current_number_inside_range CHECK (((current_number >= start_number) AND (current_number <= end_number))),
    CONSTRAINT ck_barcode_ranges_end_number_gte_start_number CHECK ((end_number >= start_number)),
    CONSTRAINT ck_barcode_ranges_status_allowed CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'exhausted'::character varying, 'expired'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: barcode_ranges_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.barcode_ranges_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: barcode_ranges_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.barcode_ranges_id_seq OWNED BY public.barcode_ranges.id;


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.clients (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    contact_person character varying(255),
    contact_phone character varying(100),
    email character varying(255),
    notes text,
    is_active boolean DEFAULT true NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: clients_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.clients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: clients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.clients_id_seq OWNED BY public.clients.id;


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    region character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    parent_id integer,
    department_type character varying(50),
    full_path character varying(1000),
    external_id character varying(100),
    is_active boolean DEFAULT true NOT NULL,
    shpi_region_code character varying(2)
);


--
-- Name: departments_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.departments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: departments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.departments_id_seq OWNED BY public.departments.id;


--
-- Name: generated_barcodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generated_barcodes (
    id integer NOT NULL,
    batch_id integer NOT NULL,
    barcode character varying(50) NOT NULL,
    package_type character varying(20) NOT NULL,
    department_id integer,
    sequence_number integer NOT NULL,
    printed boolean DEFAULT false NOT NULL,
    printed_at timestamp with time zone,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    range_id integer,
    status character varying(50) DEFAULT 'generated'::character varying NOT NULL,
    cancelled_at timestamp with time zone,
    cancelled_by character varying(100),
    cancellation_reason text,
    used_at timestamp with time zone,
    used_by character varying(100),
    usage_notes text,
    generated_by character varying(100),
    printed_by character varying(100),
    CONSTRAINT ck_generated_barcodes_status_allowed CHECK (((status)::text = ANY ((ARRAY['generated'::character varying, 'printed'::character varying, 'used'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: generated_barcodes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.generated_barcodes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: generated_barcodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.generated_barcodes_id_seq OWNED BY public.generated_barcodes.id;


--
-- Name: generated_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.generated_batches (
    id integer NOT NULL,
    package_type character varying(20) NOT NULL,
    quantity integer NOT NULL,
    first_barcode character varying(50) NOT NULL,
    last_barcode character varying(50) NOT NULL,
    department_id integer,
    generated_by character varying(100),
    source character varying(50) DEFAULT 'api'::character varying,
    status character varying(50) DEFAULT 'generated'::character varying NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text,
    range_id integer
);


--
-- Name: generated_batches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.generated_batches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: generated_batches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.generated_batches_id_seq OWNED BY public.generated_batches.id;


--
-- Name: printed_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printed_batches (
    id integer NOT NULL,
    generated_batch_id integer NOT NULL,
    department_id integer,
    printed_count integer NOT NULL,
    first_barcode character varying(50) NOT NULL,
    last_barcode character varying(50) NOT NULL,
    printed_by character varying(100),
    printer_name character varying(255),
    status character varying(50) DEFAULT 'printed'::character varying NOT NULL,
    printed_at timestamp with time zone DEFAULT now() NOT NULL,
    notes text
);


--
-- Name: printed_batches_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.printed_batches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: printed_batches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.printed_batches_id_seq OWNED BY public.printed_batches.id;


--
-- Name: range_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.range_requests (
    id integer NOT NULL,
    requester_id integer NOT NULL,
    client_id integer,
    department_id integer,
    package_type character varying(20),
    requested_quantity integer NOT NULL,
    request_type character varying(100) DEFAULT 'issue_range'::character varying NOT NULL,
    payload text,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    handled_by integer,
    handled_at timestamp with time zone,
    notes text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    purpose text,
    requested_code character varying(20),
    approved_code character varying(20),
    decision_notes text,
    CONSTRAINT ck_range_requests_status_allowed CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: range_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.range_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: range_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.range_requests_id_seq OWNED BY public.range_requests.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    hashed_password character varying(255),
    full_name character varying(255),
    role character varying(50) NOT NULL,
    department_id integer,
    is_active boolean DEFAULT true NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    client_id integer,
    email character varying(255),
    phone character varying(50),
    CONSTRAINT ck_users_role_allowed CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'operator'::character varying, 'client'::character varying])::text[])))
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: app_settings id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings ALTER COLUMN id SET DEFAULT nextval('public.app_settings_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: barcode_code_catalog id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_code_catalog ALTER COLUMN id SET DEFAULT nextval('public.barcode_code_catalog_id_seq'::regclass);


--
-- Name: barcode_counters id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_counters ALTER COLUMN id SET DEFAULT nextval('public.barcode_counters_id_seq'::regclass);


--
-- Name: barcode_ranges id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges ALTER COLUMN id SET DEFAULT nextval('public.barcode_ranges_id_seq'::regclass);


--
-- Name: clients id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients ALTER COLUMN id SET DEFAULT nextval('public.clients_id_seq'::regclass);


--
-- Name: departments id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments ALTER COLUMN id SET DEFAULT nextval('public.departments_id_seq'::regclass);


--
-- Name: generated_barcodes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_barcodes ALTER COLUMN id SET DEFAULT nextval('public.generated_barcodes_id_seq'::regclass);


--
-- Name: generated_batches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_batches ALTER COLUMN id SET DEFAULT nextval('public.generated_batches_id_seq'::regclass);


--
-- Name: printed_batches id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printed_batches ALTER COLUMN id SET DEFAULT nextval('public.printed_batches_id_seq'::regclass);


--
-- Name: range_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests ALTER COLUMN id SET DEFAULT nextval('public.range_requests_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: app_settings pk_app_settings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT pk_app_settings PRIMARY KEY (id);


--
-- Name: audit_logs pk_audit_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT pk_audit_logs PRIMARY KEY (id);


--
-- Name: barcode_code_catalog pk_barcode_code_catalog; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_code_catalog
    ADD CONSTRAINT pk_barcode_code_catalog PRIMARY KEY (id);


--
-- Name: barcode_counters pk_barcode_counters; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_counters
    ADD CONSTRAINT pk_barcode_counters PRIMARY KEY (id);


--
-- Name: barcode_ranges pk_barcode_ranges; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT pk_barcode_ranges PRIMARY KEY (id);


--
-- Name: clients pk_clients; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT pk_clients PRIMARY KEY (id);


--
-- Name: departments pk_departments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT pk_departments PRIMARY KEY (id);


--
-- Name: generated_barcodes pk_generated_barcodes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_barcodes
    ADD CONSTRAINT pk_generated_barcodes PRIMARY KEY (id);


--
-- Name: generated_batches pk_generated_batches; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_batches
    ADD CONSTRAINT pk_generated_batches PRIMARY KEY (id);


--
-- Name: printed_batches pk_printed_batches; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printed_batches
    ADD CONSTRAINT pk_printed_batches PRIMARY KEY (id);


--
-- Name: range_requests pk_range_requests; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests
    ADD CONSTRAINT pk_range_requests PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: app_settings uq_app_settings_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_settings
    ADD CONSTRAINT uq_app_settings_key UNIQUE (key);


--
-- Name: barcode_counters uq_barcode_counters_package_type_region_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_counters
    ADD CONSTRAINT uq_barcode_counters_package_type_region_code UNIQUE (package_type, region_code);


--
-- Name: departments uq_departments_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT uq_departments_code UNIQUE (code);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_department_id ON public.audit_logs USING btree (department_id);


--
-- Name: ix_audit_logs_department_id_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_department_id_created_at ON public.audit_logs USING btree (department_id, created_at);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_audit_logs_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_username ON public.audit_logs USING btree (username);


--
-- Name: ix_barcode_code_catalog_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_barcode_code_catalog_code ON public.barcode_code_catalog USING btree (code);


--
-- Name: ix_barcode_code_catalog_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_code_catalog_status ON public.barcode_code_catalog USING btree (status);


--
-- Name: ix_barcode_ranges_issued_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_issued_by ON public.barcode_ranges USING btree (issued_by);


--
-- Name: ix_barcode_ranges_issued_to_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_issued_to_client_id ON public.barcode_ranges USING btree (issued_to_client_id);


--
-- Name: ix_barcode_ranges_issued_to_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_issued_to_department_id ON public.barcode_ranges USING btree (issued_to_department_id);


--
-- Name: ix_barcode_ranges_package_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_package_type ON public.barcode_ranges USING btree (package_type);


--
-- Name: ix_barcode_ranges_region_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_region_code ON public.barcode_ranges USING btree (region_code);


--
-- Name: ix_barcode_ranges_request_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_request_id ON public.barcode_ranges USING btree (request_id);


--
-- Name: ix_barcode_ranges_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_barcode_ranges_status ON public.barcode_ranges USING btree (status);


--
-- Name: ix_clients_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_clients_name ON public.clients USING btree (name);


--
-- Name: ix_departments_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_departments_code ON public.departments USING btree (code);


--
-- Name: ix_departments_external_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_departments_external_id ON public.departments USING btree (external_id);


--
-- Name: ix_departments_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_parent_id ON public.departments USING btree (parent_id);


--
-- Name: ix_departments_shpi_region_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_departments_shpi_region_code ON public.departments USING btree (shpi_region_code);


--
-- Name: ix_generated_barcodes_barcode; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_generated_barcodes_barcode ON public.generated_barcodes USING btree (barcode);


--
-- Name: ix_generated_barcodes_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_barcodes_batch_id ON public.generated_barcodes USING btree (batch_id);


--
-- Name: ix_generated_barcodes_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_barcodes_department_id ON public.generated_barcodes USING btree (department_id);


--
-- Name: ix_generated_barcodes_package_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_barcodes_package_type ON public.generated_barcodes USING btree (package_type);


--
-- Name: ix_generated_barcodes_range_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_barcodes_range_id ON public.generated_barcodes USING btree (range_id);


--
-- Name: ix_generated_barcodes_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_barcodes_status ON public.generated_barcodes USING btree (status);


--
-- Name: ix_generated_batches_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_batches_department_id ON public.generated_batches USING btree (department_id);


--
-- Name: ix_generated_batches_generated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_batches_generated_at ON public.generated_batches USING btree (generated_at);


--
-- Name: ix_generated_batches_package_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_batches_package_type ON public.generated_batches USING btree (package_type);


--
-- Name: ix_generated_batches_range_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_generated_batches_range_id ON public.generated_batches USING btree (range_id);


--
-- Name: ix_printed_batches_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_printed_batches_department_id ON public.printed_batches USING btree (department_id);


--
-- Name: ix_printed_batches_generated_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_printed_batches_generated_batch_id ON public.printed_batches USING btree (generated_batch_id);


--
-- Name: ix_printed_batches_printed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_printed_batches_printed_at ON public.printed_batches USING btree (printed_at);


--
-- Name: ix_range_requests_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_client_id ON public.range_requests USING btree (client_id);


--
-- Name: ix_range_requests_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_department_id ON public.range_requests USING btree (department_id);


--
-- Name: ix_range_requests_handled_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_handled_by ON public.range_requests USING btree (handled_by);


--
-- Name: ix_range_requests_package_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_package_type ON public.range_requests USING btree (package_type);


--
-- Name: ix_range_requests_requester_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_requester_id ON public.range_requests USING btree (requester_id);


--
-- Name: ix_range_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_range_requests_status ON public.range_requests USING btree (status);


--
-- Name: ix_users_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_client_id ON public.users USING btree (client_id);


--
-- Name: ix_users_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_department_id ON public.users USING btree (department_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_logs fk_audit_logs_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT fk_audit_logs_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: audit_logs fk_audit_logs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT fk_audit_logs_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: barcode_ranges fk_barcode_ranges_cancelled_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT fk_barcode_ranges_cancelled_by_users FOREIGN KEY (cancelled_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: barcode_ranges fk_barcode_ranges_issued_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT fk_barcode_ranges_issued_by_users FOREIGN KEY (issued_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: barcode_ranges fk_barcode_ranges_issued_to_client_id_clients; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT fk_barcode_ranges_issued_to_client_id_clients FOREIGN KEY (issued_to_client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: barcode_ranges fk_barcode_ranges_issued_to_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT fk_barcode_ranges_issued_to_department_id_departments FOREIGN KEY (issued_to_department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: barcode_ranges fk_barcode_ranges_request_id_range_requests; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.barcode_ranges
    ADD CONSTRAINT fk_barcode_ranges_request_id_range_requests FOREIGN KEY (request_id) REFERENCES public.range_requests(id) ON DELETE SET NULL;


--
-- Name: departments fk_departments_parent_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT fk_departments_parent_id_departments FOREIGN KEY (parent_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: generated_barcodes fk_generated_barcodes_batch_id_generated_batches; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_barcodes
    ADD CONSTRAINT fk_generated_barcodes_batch_id_generated_batches FOREIGN KEY (batch_id) REFERENCES public.generated_batches(id) ON DELETE CASCADE;


--
-- Name: generated_barcodes fk_generated_barcodes_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_barcodes
    ADD CONSTRAINT fk_generated_barcodes_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: generated_barcodes fk_generated_barcodes_range_id_barcode_ranges; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_barcodes
    ADD CONSTRAINT fk_generated_barcodes_range_id_barcode_ranges FOREIGN KEY (range_id) REFERENCES public.barcode_ranges(id) ON DELETE SET NULL;


--
-- Name: generated_batches fk_generated_batches_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_batches
    ADD CONSTRAINT fk_generated_batches_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: generated_batches fk_generated_batches_range_id_barcode_ranges; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.generated_batches
    ADD CONSTRAINT fk_generated_batches_range_id_barcode_ranges FOREIGN KEY (range_id) REFERENCES public.barcode_ranges(id) ON DELETE SET NULL;


--
-- Name: printed_batches fk_printed_batches_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printed_batches
    ADD CONSTRAINT fk_printed_batches_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: printed_batches fk_printed_batches_generated_batch_id_generated_batches; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printed_batches
    ADD CONSTRAINT fk_printed_batches_generated_batch_id_generated_batches FOREIGN KEY (generated_batch_id) REFERENCES public.generated_batches(id) ON DELETE CASCADE;


--
-- Name: range_requests fk_range_requests_client_id_clients; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests
    ADD CONSTRAINT fk_range_requests_client_id_clients FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: range_requests fk_range_requests_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests
    ADD CONSTRAINT fk_range_requests_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: range_requests fk_range_requests_handled_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests
    ADD CONSTRAINT fk_range_requests_handled_by_users FOREIGN KEY (handled_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: range_requests fk_range_requests_requester_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.range_requests
    ADD CONSTRAINT fk_range_requests_requester_id_users FOREIGN KEY (requester_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users fk_users_client_id_clients; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_client_id_clients FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: users fk_users_department_id_departments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_department_id_departments FOREIGN KEY (department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict zHKIkcIZPBcetzFgbVOksg2ZTDdbyxfpocgmoNxI3RaKkZtj5HAWPdRnPJ2p7LA

