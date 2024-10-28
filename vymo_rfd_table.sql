--
-- PostgreSQL database dump
--

-- Dumped from database version 12.17
-- Dumped by pg_dump version 12.17

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: vymo_dispo_rfd; Type: TABLE DATA; Schema: public; Owner: flexydial
--

COPY public.vymo_dispo_rfd (id, code, value, loan_type) FROM stdin;
1	ghmdxj5gvm	Cancellation and Rebooking	LOAN
2	duy9rvxsb	Disputed	LOAN
3	2pvxotk0na	Senior level escalation (To CEO / RBI)	LOAN
4	6ayhbnt8q	Confirmed death	LOAN
5	vq2pz6tj96	Death in Family	LOAN
6	95vtk75tx4	Confirmed Fraud (Documents or Identity)	LOAN
7	z40tm4ar2o	BT Case	LOAN
8	xr3gsqi4s	Loss of job	LOAN
9	q0id9x3h3l	Letter Sent	LOAN
10	h6smuim0p	Medical Expense	LOAN
11	5kfgazn3f	Matured/Live Account – charges &lt INR. 500	LOAN
12	yuzq1coqdo	Not Contactable	LOAN
13	1je0qaqiv	Out of station	LOAN
14	h188vmfu8q	Out of control circumstances / Temp Finan Prob	LOAN
15	xp4xak3m5e	Over leveraged. Multiple debts	LOAN
16	0iyvald6pd	Payment problem with correspondent Banks	LOAN
17	vy36d5cx8f	Post settlement waiver Request	LOAN
18	7yf78mt1mo	Intentional default. Refusing to pay	LOAN
19	jq2jox2ss	Cut in salary	LOAN
20	sb74smmpxl	Shifted but contactable on phone only	LOAN
21	9dz61i8vnh	Suspected Death	LOAN
22	o6a5jvnaxi	Internal Sys updation issue	LOAN
23	59hvbbkth5	Top up Loan, old LAN to be closed.	LOAN
24	4wjbxox23v	Wants Settlement	LOAN
25	qorzhumx9i	Loan Cancellation in progress	LOAN
26	2u20bbrnd	Permanent Job Loss	LOAN
27	ddj74trk8o	Temporary Job Loss	LOAN
28	zxm8hayu6q	Permanent Business Shut Down	LOAN
29	ng1zxml4	Temporary Business Slow Down	LOAN
30	y3aln37p7d	Loss in Business	LOAN
31	j6oye6101s	Fund Available in Debit AC for Clearance ECS Within PDD	LOAN
64	duy9rvxsb	Disputed	URBAN LOANS
59	rvbyrcfz	Permanent Business Shut Down	HFC_LOANS
60	alafrgqj	Temporary Business Slow Down	HFC_LOANS
61	cnlyvztm	Loss in Business	HFC_LOANS
62	tboynbhg	Fund Available in Debit AC for Clearance ECS Within PDD	HFC_LOANS
63	ghmdxj5gvm	Cancellation and Rebooking	URBAN_LOANS
65	2pvxotk0na	Senior level escalation (To CEO / RBI)	URBAN_LOANS
66	6ayhbnt8q	Confirmed death	URBAN_LOANS
67	vq2pz6tj96	Death in Family	URBAN_LOANS
68	95vtk75tx4	Confirmed Fraud (Documents or Identity)	URBAN_LOANS
69	z40tm4ar2o	BT Case	URBAN_LOANS
70	xr3gsqi4s	Loss of job	URBAN_LOANS
72	h6smuim0p	Medical Expense	URBAN_LOANS
33	atoqhbku	Disputed	HFC_LOANS
73	5kfgazn3f	Matured/Live Account – charges &lt INR. 500	URBAN_LOANS
74	yuzq1coqdo	Not Contactable	URBAN_LOANS
75	1je0qaqiv	Out of station	URBAN_LOANS
76	h188vmfu8q	Out of control circumstances / Temp Finan Prob	URBAN_LOANS
77	xp4xak3m5e	Over leveraged. Multiple debts	URBAN_LOANS
78	0iyvald6pd	Payment problem with correspondent Banks	URBAN_LOANS
79	vy36d5cx8f	Post settlement waiver Request	URBAN_LOANS
80	7yf78mt1mo	Intentional default. Refusing to pay	URBAN_LOANS
81	jq2jox2ss	Cut in salary	URBAN_LOANS
43	wtuekkez	Not Contactable	HFC_LOANS
44	etgbebtt	Out of station	HFC_LOANS
45	piyslixk	Out of control circumstances / Temp Finan Prob	HFC_LOANS
46	ygfjrcdi	Over leveraged. Multiple debts	HFC_LOANS
47	hraliiah	Payment problem with correspondent Banks	HFC_LOANS
48	cdxhoosv	Post settlement waiver Request	HFC_LOANS
49	flynntul	Intentional default. Refusing to pay	HFC_LOANS
50	gweuxjmb	Cut in salary	HFC_LOANS
51	dcrqemzg	Shifted but contactable on phone only	HFC_LOANS
52	ldympolw	Suspected Death	HFC_LOANS
53	fxjmotxt	Internal Sys updation issue	HFC_LOANS
54	vpnwaysr	Top up Loan, old LAN to be closed.	HFC_LOANS
55	cqzwbpub	Wants Settlement	HFC_LOANS
83	9dz61i8vnh	Suspected Death	URBAN_LOANS
56	afgimjue	Loan Cancellation in progress	HFC_LOANS
57	axbnawgz	Permanent Job Loss	HFC_LOANS
58	qvjkbbjb	Temporary Job Loss	HFC_LOANS
71	q0id9x3h3l	Letter Sent	URBAN_LOANS
85	59hvbbkth5	Top up Loan, old LAN to be closed.	URBAN_LOANS
86	4wjbxox23v	Wants Settlement	URBAN_LOANS
87	qorzhumx9i	Loan Cancellation in progress	URBAN_LOANS
88	2u20bbrnd	Permanent Job Loss	URBAN_LOANS
89	ddj74trk8o	Temporary Job Loss	URBAN_LOANS
90	zxm8hayu6q	Permanent Business Shut Down	URBAN_LOANS
91	ng1zxml4	Temporary Business Slow Down	URBAN_LOANS
92	y3aln37p7d	Loss in Business	URBAN_LOANS
93	j6oye6101s	Fund Available in Debit AC for Clearance ECS Within PDD	URBAN_LOANS
32	ixzvqksd	Cancellation and Rebooking	HFC_LOANS
82	sb74smmpxl	Shifted but contactable on phone only	URBAN_LOANS
84	o6a5jvnaxi	Internal Sys updation issue	URBAN_LOANS
34	wgupnngq	Senior level escalation (To CEO / RBI)	HFC_LOANS
35	ljlcddoq	Confirmed death	HFC_LOANS
36	zpllfsda	Death in Family	HFC_LOANS
37	lgeeytkd	Confirmed Fraud (Documents or Identity)	HFC_LOANS
38	xprgslyr	BT Case	HFC_LOANS
39	gxporxxy	Loss of job	HFC_LOANS
40	txnsaoiy	Letter Sent	HFC_LOANS
41	wdwobwbz	Medical Expense	HFC_LOANS
42	xdyuylsw	Matured/Live Account – charges &lt INR. 500	HFC_LOANS
\.


--
-- Name: vymo_dispo_rfd_id_seq; Type: SEQUENCE SET; Schema: public; Owner: flexydial
--

SELECT pg_catalog.setval('public.vymo_dispo_rfd_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

