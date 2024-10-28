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
-- Data for Name: vymo_dispo_disposition; Type: TABLE DATA; Schema: public; Owner: flexydial
--

COPY public.vymo_dispo_disposition (id, code, value, loan_type) FROM stdin;
1	70301vqadr	AutoFeedback	LOAN
2	kvhghp6o5	CB	LOAN
3	802x9gsff	DEAD	LOAN
4	4ai6lgbled	FU	LOAN
5	7f6idgejhb	LM	LOAN
6	gyvie4ishj	NCIN	LOAN
7	am0tf7j0l5	NCNR	LOAN
8	k7ck4gjsdj	NCRG	LOAN
9	rcix6puz2l	NCSO	LOAN
10	7kyuolew77	NCWN	LOAN
11	uk440841xi	NF(No Feedback)	LOAN
12	50bfsdh4qg	NP	LOAN
13	1ueuv9oxw	PTP	LOAN
14	o2gtgtg9h7	PU	LOAN
15	g3btbtjlx4	PV	LOAN
16	sltp6l5yr9p	Redialed	LOAN
17	xcx3v5z84o	RTP	LOAN
18	iec041mm7	SKIP	LOAN
19	juh46jx41	TPC	LOAN
20	5fmt43mm5q	VI	LOAN
21	escupagq	AutoFeedback	URBAN_LOANS
22	ejqgyyca	CB	URBAN_LOANS
23	ktfpsaml	DEAD	URBAN_LOANS
24	hwrymwcb	FU	URBAN_LOANS
25	utnlurmv	LM	URBAN_LOANS
26	dpvqripz	NCIN	URBAN_LOANS
27	dvanhuhs	NCNR	URBAN_LOANS
28	xxiqicuk	NCRG	URBAN_LOANS
29	gsmukciq	NCSO	URBAN_LOANS
30	nokiuxgs	NCWN	URBAN_LOANS
31	dzcyltsu	NF(No Feedback)	URBAN_LOANS
32	krgqwttz	NP	URBAN_LOANS
33	tqjtrlcc	PTP	URBAN_LOANS
34	wmjexobz	PU	URBAN_LOANS
35	vfxocohy	PV	URBAN_LOANS
36	wbqdebkl	Redialed	URBAN_LOANS
37	wsbgirwl	RTP	URBAN_LOANS
38	ijlhxesp	SKIP	URBAN_LOANS
39	ywkequev	TPC	URBAN_LOANS
40	saoeghkd	VI	URBAN_LOANS
41	kgjkkguh	AutoFeedback	HFC_LOANS
42	gasurflc	CB	HFC_LOANS
43	ndpwwdpq	DEAD	HFC_LOANS
44	uoemevvb	FU	HFC_LOANS
45	fifvkizj	LM	HFC_LOANS
46	gtyguhcv	NCIN	HFC_LOANS
47	oyvoeewd	NCNR	HFC_LOANS
48	tbteipmb	NCRG	HFC_LOANS
49	xznodssr	NCSO	HFC_LOANS
50	ktrdivss	NCWN	HFC_LOANS
51	ldbhbrib	NF(No Feedback)	HFC_LOANS
52	btyuddfl	NP	HFC_LOANS
53	fvioolch	PTP	HFC_LOANS
54	nswgnjui	PU	HFC_LOANS
55	sgskntod	PV	HFC_LOANS
56	eutporxn	Redialed	HFC_LOANS
57	ydaiwruo	RTP	HFC_LOANS
58	aipyngjb	SKIP	HFC_LOANS
59	tyzhcojn	TPC	HFC_LOANS
60	ywpvgfgr	VI	HFC_LOANS
\.


--
-- Name: vymo_dispo_disposition_id_seq; Type: SEQUENCE SET; Schema: public; Owner: flexydial
--

SELECT pg_catalog.setval('public.vymo_dispo_disposition_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

