# Noble Intel — Global Freight Intelligence Source Catalog

> **Generated**: 2026-03-27  
> **Existing sources in `sources.py`**: ~85  
> **New sources in this catalog**: 915+  
> **Total target**: 1000+  
> **Status**: `[V]` = Verified feed accessible | `[U]` = Unverified (URL known, feed not yet tested) | `[P]` = Paywall / manual review needed

---

## Table of Contents

1. [A — Port Authorities (Top 100 Busiest Ports)](#a--port-authorities-top-100-busiest-ports)
2. [B — National Maritime Authorities](#b--national-maritime-authorities)
3. [C — Aviation & Air Cargo Authorities](#c--aviation--air-cargo-authorities)
4. [D — Customs Agencies](#d--customs-agencies)
5. [E — Logistics Company IR / Newsrooms](#e--logistics-company-ir--newsrooms)
6. [F — Regional Freight News by Continent](#f--regional-freight-news-by-continent)
7. [G — Port Community Systems & Congestion Data](#g--port-community-systems--congestion-data)
8. [H — Geopolitical & Maritime Security](#h--geopolitical--maritime-security)
9. [I — Energy / Fuel / Bunker Pricing](#i--energy--fuel--bunker-pricing)
10. [J — Commodity & Financial Indices](#j--commodity--financial-indices)
11. [K — Social / Forums / Reddit](#k--social--forums--reddit)
12. [L — Technology / Tracking / Visibility](#l--technology--tracking--visibility)
13. [M — Trade Associations & Industry Bodies](#m--trade-associations--industry-bodies)
14. [N — Research / Analytics / Consulting](#n--research--analytics--consulting)
15. [O — Rail Freight Operators & Authorities](#o--rail-freight-operators--authorities)
16. [P — Trucking / Road Freight Regulators](#p--trucking--road-freight-regulators)

---

## A — Port Authorities (Top 100 Busiest Ports)

> **Strategy**: World's busiest container ports by TEU volume. Each port authority typically has a news/press page, some with RSS feeds.  
> **Already in `sources.py`**: port_la, port_long_beach, port_rotterdam, port_singapore, port_shanghai, port_hamburg, port_antwerp

### Asia-Pacific

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Port of Ningbo-Zhoushan | Ocean | News Page | China | port_ningbo | official | 1 | 0.90 | playwright | true | https://www.nbport.com.cn/english/news/ | [U] |
| Port of Shenzhen | Ocean | News Page | China | port_shenzhen | official | 1 | 0.90 | playwright | true | https://www.szport.net/english/ | [U] |
| Port of Guangzhou | Ocean | News Page | China | port_guangzhou | official | 1 | 0.90 | playwright | true | http://www.gzport.com/en/ | [U] |
| Port of Qingdao | Ocean | News Page | China | port_qingdao | official | 1 | 0.90 | playwright | true | http://www.qdport.com/en/ | [U] |
| Port of Tianjin | Ocean | News Page | China | port_tianjin | official | 1 | 0.90 | playwright | true | http://www.ptacn.com/en/ | [U] |
| Port of Xiamen | Ocean | News Page | China | port_xiamen | official | 1 | 0.85 | playwright | true | http://www.xmport.com.cn/en/ | [U] |
| Port of Dalian | Ocean | News Page | China | port_dalian | official | 1 | 0.85 | playwright | true | http://www.dlport.cn/en/ | [U] |
| PSA Singapore — News | Ocean | News Page | Singapore | psa_singapore | official | 1 | 0.95 | playwright | true | https://www.globalpsa.com/news/ | [U] |
| Port of Busan | Ocean | News Page | South Korea | port_busan | official | 1 | 0.90 | playwright | true | https://www.busanpa.com/eng/Board.do?mCode=MN0034 | [U] |
| Port of Incheon | Ocean | News Page | South Korea | port_incheon | official | 1 | 0.85 | playwright | true | https://www.icpa.or.kr/eng/ | [U] |
| Port Klang (Westports/Northport) | Ocean | News Page | Malaysia | port_klang | official | 1 | 0.85 | playwright | true | https://www.westportsholdings.com/media/ | [U] |
| Port of Tanjung Pelepas | Ocean | News Page | Malaysia | port_ptp | official | 1 | 0.85 | playwright | true | https://www.ptp.com.my/news | [U] |
| Port of Kaohsiung | Ocean | News Page | Taiwan | port_kaohsiung | official | 1 | 0.85 | playwright | true | https://kh.twport.com.tw/en/ | [U] |
| Port of Taipei (Keelung) | Ocean | News Page | Taiwan | port_keelung | official | 1 | 0.85 | playwright | true | https://kl.twport.com.tw/en/ | [U] |
| Port of Tokyo | Ocean | News Page | Japan | port_tokyo | official | 1 | 0.85 | playwright | true | https://www.tptc.co.jp/en/ | [U] |
| Port of Yokohama | Ocean | News Page | Japan | port_yokohama | official | 1 | 0.85 | playwright | true | https://www.city.yokohama.lg.jp/business/kigyoshien/port/english/ | [U] |
| Port of Nagoya | Ocean | News Page | Japan | port_nagoya | official | 1 | 0.85 | playwright | true | https://www.port-of-nagoya.jp/english/ | [U] |
| Port of Kobe | Ocean | News Page | Japan | port_kobe | official | 1 | 0.85 | playwright | true | https://www.city.kobe.lg.jp/a02067/kanko/port/ | [U] |
| Jawaharlal Nehru Port (JNPT/Nhava Sheva) | Ocean | News Page | India | port_jnpt | official | 1 | 0.85 | playwright | true | https://www.jnport.gov.in/News | [U] |
| Mundra Port (Adani) | Ocean | News Page | India | port_mundra | official | 1 | 0.85 | playwright | true | https://www.adaniports.com/newsroom | [U] |
| Chennai Port | Ocean | News Page | India | port_chennai | official | 1 | 0.85 | playwright | true | https://www.chennaiport.gov.in/ | [U] |
| Colombo Port (SLPA) | Ocean | News Page | Sri Lanka | port_colombo | official | 1 | 0.85 | playwright | true | https://www.slpa.lk/news | [U] |
| Port of Laem Chabang | Ocean | News Page | Thailand | port_laem_chabang | official | 1 | 0.85 | playwright | true | https://www.laemchabangport.com/en/ | [U] |
| Port of Ho Chi Minh City (Cat Lai) | Ocean | News Page | Vietnam | port_hochiminh | official | 1 | 0.85 | playwright | true | https://www.saigonnewport.com.vn/en/ | [U] |
| Port of Manila | Ocean | News Page | Philippines | port_manila | official | 1 | 0.85 | playwright | true | https://ppa.com.ph/ | [U] |
| Port of Tanjung Priok | Ocean | News Page | Indonesia | port_tanjung_priok | official | 1 | 0.85 | playwright | true | https://inaport2.co.id/ | [U] |
| Hutchison Ports — Global News | Ocean | News Page | Global | hutchison_ports | official | 1 | 0.90 | playwright | true | https://hutchisonports.com/en/media/ | [U] |
| DP World — Media Centre | Ocean | News Page | Global | dpworld_news | official | 1 | 0.90 | playwright | true | https://www.dpworld.com/news | [U] |

### Middle East

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DP World Jebel Ali | Ocean | News Page | UAE | port_jebel_ali | official | 1 | 0.90 | playwright | true | https://www.dpworld.com/uae/news | [U] |
| King Abdullah Port (KAEC) | Ocean | News Page | Saudi Arabia | port_king_abdullah | official | 1 | 0.85 | playwright | true | https://www.kingabdullahport.com.sa/news/ | [U] |
| Jeddah Islamic Port | Ocean | News Page | Saudi Arabia | port_jeddah | official | 1 | 0.85 | playwright | true | https://mawani.gov.sa/en/MediaCenter/Pages/News.aspx | [U] |
| Port of Salalah | Ocean | News Page | Oman | port_salalah | official | 1 | 0.85 | playwright | true | https://www.salalahport.com/news/ | [U] |
| Khalifa Port (Abu Dhabi) | Ocean | News Page | UAE | port_khalifa | official | 1 | 0.85 | playwright | true | https://www.adports.ae/media/ | [U] |
| Port of Sohar | Ocean | News Page | Oman | port_sohar | official | 1 | 0.85 | playwright | true | https://www.soharportandfreezone.com/media | [U] |
| Hamad Port (Qatar) | Ocean | News Page | Qatar | port_hamad | official | 1 | 0.85 | playwright | true | https://www.mwani.com.qa/english/pages/default.aspx | [U] |

### Europe

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Port of Valencia | Ocean | RSS | Spain | port_valencia | official | 1 | 0.90 | rss | false | https://www.valenciaport.com/en/feed/ | [U] |
| Port of Algeciras | Ocean | News Page | Spain | port_algeciras | official | 1 | 0.85 | playwright | true | https://www.apba.es/en/news | [U] |
| Port of Barcelona | Ocean | News Page | Spain | port_barcelona | official | 1 | 0.90 | playwright | true | https://www.portdebarcelona.cat/en/news | [U] |
| Port of Piraeus | Ocean | News Page | Greece | port_piraeus | official | 1 | 0.85 | playwright | true | https://www.olp.gr/en/news | [U] |
| Port of Genoa | Ocean | News Page | Italy | port_genoa | official | 1 | 0.85 | playwright | true | https://www.portsofgenoa.com/en/news.html | [U] |
| Port of Gioia Tauro | Ocean | News Page | Italy | port_gioia_tauro | official | 1 | 0.85 | playwright | true | https://www.portigioiatauro.it/en/ | [U] |
| Port of Felixstowe | Ocean | News Page | UK | port_felixstowe | official | 1 | 0.90 | playwright | true | https://www.portoffelixstowe.co.uk/news/ | [U] |
| Port of Southampton | Ocean | News Page | UK | port_southampton | official | 1 | 0.85 | playwright | true | https://www.abports.co.uk/news/ | [U] |
| Port of Le Havre (HAROPA) | Ocean | News Page | France | port_le_havre | official | 1 | 0.90 | playwright | true | https://www.haropaport.com/en/press | [U] |
| Port of Marseille-Fos | Ocean | News Page | France | port_marseille | official | 1 | 0.85 | playwright | true | https://www.marseille-port.fr/en/press-room | [U] |
| Port of Gothenburg | Ocean | RSS | Sweden | port_gothenburg | official | 1 | 0.90 | rss | false | https://www.portofgothenburg.com/feed/ | [U] |
| Port of Gdansk | Ocean | News Page | Poland | port_gdansk | official | 1 | 0.85 | playwright | true | https://www.portgdansk.pl/en/news | [U] |
| Port of Bremerhaven | Ocean | News Page | Germany | port_bremerhaven | official | 1 | 0.90 | playwright | true | https://bremenports.de/en/press/ | [U] |
| Port of Zeebrugge | Ocean | News Page | Belgium | port_zeebrugge | official | 1 | 0.85 | playwright | true | https://www.portofzeebrugge.be/en/news | [U] |
| Port of Amsterdam | Ocean | RSS | Netherlands | port_amsterdam | official | 1 | 0.90 | rss | false | https://www.portofamsterdam.com/en/news/rss | [U] |

### Americas

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Port of New York/New Jersey (PANYNJ) | Ocean | News Page | US | port_nynj | official | 1 | 0.95 | playwright | true | https://www.panynj.gov/port-authority/en/press-room.html | [V] |
| Port of Savannah (Georgia Ports) | Ocean | News Page | US | port_savannah | official | 1 | 0.95 | playwright | true | https://gaports.com/press-releases/ | [U] |
| Port Houston | Ocean | News Page | US | port_houston | official | 1 | 0.95 | playwright | true | https://porthouston.com/about-us/news/ | [U] |
| Port of Virginia (Norfolk) | Ocean | News Page | US | port_virginia | official | 1 | 0.90 | playwright | true | https://www.portofvirginia.com/news/ | [U] |
| Port of Charleston | Ocean | News Page | US | port_charleston | official | 1 | 0.90 | playwright | true | https://scspa.com/news/ | [U] |
| JAXPORT (Jacksonville) | Ocean | RSS | US | port_jaxport | official | 1 | 0.90 | rss | false | https://www.jaxport.com/feed/ | [V] |
| Port of Oakland | Ocean | News Page | US | port_oakland | official | 1 | 0.90 | playwright | true | https://www.portofoakland.com/press-releases/ | [U] |
| Port of Seattle/Tacoma (NWSA) | Ocean | News Page | US | port_seattle | official | 1 | 0.90 | playwright | true | https://www.nwseaportalliance.com/about/news | [U] |
| Port of Baltimore | Ocean | News Page | US | port_baltimore | official | 1 | 0.90 | playwright | true | https://www.marylandports.com/press-releases | [U] |
| Port of Miami | Ocean | News Page | US | port_miami | official | 1 | 0.85 | playwright | true | https://www.portmiami.biz/news | [U] |
| Port of Santos | Ocean | News Page | Brazil | port_santos | official | 1 | 0.85 | playwright | true | https://www.portodesantos.com.br/en/news/ | [U] |
| Panama Canal Authority | Ocean | News Page | Panama | panama_canal | official | 1 | 0.95 | playwright | true | https://pancanal.com/en/press-releases/ | [U] |
| Port of Manzanillo | Ocean | News Page | Mexico | port_manzanillo | official | 1 | 0.85 | playwright | true | https://www.puertomanzanillo.com.mx/ | [U] |
| Port of Lazaro Cardenas | Ocean | News Page | Mexico | port_lazaro_cardenas | official | 1 | 0.85 | playwright | true | https://www.puertolazarocardenas.com.mx/ | [U] |
| Port of Callao | Ocean | News Page | Peru | port_callao | official | 1 | 0.85 | playwright | true | https://www.dpworldcallao.com.pe/noticias | [U] |
| Port of Cartagena | Ocean | News Page | Colombia | port_cartagena | official | 1 | 0.85 | playwright | true | https://www.puertocartagena.com/en/news | [U] |
| Port of Buenos Aires | Ocean | News Page | Argentina | port_buenos_aires | official | 1 | 0.85 | playwright | true | https://www.puertobuenosaires.gob.ar/noticias | [U] |
| Port of Montreal | Ocean | News Page | Canada | port_montreal | official | 1 | 0.90 | playwright | true | https://www.port-montreal.com/en/the-port-of-montreal/news | [U] |
| Port of Vancouver | Ocean | RSS | Canada | port_vancouver | official | 1 | 0.90 | rss | false | https://www.portvancouver.com/feed/ | [U] |
| Port of Prince Rupert | Ocean | News Page | Canada | port_prince_rupert | official | 1 | 0.85 | playwright | true | https://www.rupertport.com/news/ | [U] |

### Africa

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Transnet National Ports Authority (SA) | Ocean | News Page | South Africa | port_transnet | official | 1 | 0.85 | playwright | true | https://www.transnetnationalportsauthority.net/Media/Pages/Media.aspx | [U] |
| Port of Durban | Ocean | News Page | South Africa | port_durban | official | 1 | 0.85 | playwright | true | https://www.transnetnationalportsauthority.net/OurPorts/Durban/ | [U] |
| Port of Tanger Med | Ocean | News Page | Morocco | port_tanger_med | official | 1 | 0.90 | playwright | true | https://www.tangermed.ma/en/press/ | [U] |
| Port of Mombasa (Kenya Ports Authority) | Ocean | News Page | Kenya | port_mombasa | official | 1 | 0.85 | playwright | true | https://www.kpa.co.ke/Pages/News.aspx | [U] |
| Port of Djibouti | Ocean | News Page | Djibouti | port_djibouti | official | 1 | 0.85 | playwright | true | https://www.portdedjibouti.com/en/news/ | [U] |
| Port of Dar es Salaam (TPA) | Ocean | News Page | Tanzania | port_dar_es_salaam | official | 1 | 0.80 | playwright | true | https://www.ports.go.tz/news | [U] |
| Port of Lagos (Apapa/Tin Can) | Ocean | News Page | Nigeria | port_lagos | official | 1 | 0.80 | playwright | true | https://nigerianports.gov.ng/news/ | [U] |
| Port Said / Suez Canal Authority | Ocean | News Page | Egypt | suez_canal_authority | official | 1 | 0.95 | playwright | true | https://www.suezcanal.gov.eg/English/MediaCenter/Pages/News.aspx | [U] |

---

## B — National Maritime Authorities

> **Strategy**: National-level maritime safety and shipping regulation bodies. Many have RSS/Atom feeds for notices to mariners or press releases.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US MARAD (Maritime Administration) | Ocean | RSS | US | us_marad | official | 4 | 0.95 | rss | false | https://www.maritime.dot.gov/newsroom/rss.xml | [U] |
| US Coast Guard — Homeport Alerts | Ocean | API | US | uscg_alerts | official | 1 | 0.95 | api | false | https://homeport.uscg.mil/ | [U] |
| EMSA (EU Maritime Safety Agency) | Ocean | News Page | EU | emsa | official | 4 | 0.95 | playwright | true | https://www.emsa.europa.eu/newsroom/latest-news.html | [U] |
| UK MCA (Maritime and Coastguard) | Ocean | RSS | UK | uk_mca | official | 4 | 0.90 | rss | false | https://www.gov.uk/government/organisations/maritime-and-coastguard-agency.atom | [U] |
| AMSA (Australian Maritime Safety) | Ocean | RSS | Australia | amsa_au | official | 4 | 0.90 | rss | false | https://www.amsa.gov.au/news-community/rss.xml | [U] |
| Transport Canada — Marine Safety | Ocean | RSS | Canada | tc_marine | official | 4 | 0.90 | rss | false | https://www.canada.ca/en/transport-canada.atom | [U] |
| Japan Coast Guard | Ocean | News Page | Japan | japan_coastguard | official | 4 | 0.85 | playwright | true | https://www.kaiho.mlit.go.jp/e/ | [U] |
| Korea Maritime Safety Tribunal | Ocean | News Page | South Korea | kmst | official | 4 | 0.85 | playwright | true | https://www.kmst.go.kr/eng/ | [U] |
| China MSA (Maritime Safety Admin) | Ocean | News Page | China | china_msa | official | 4 | 0.85 | playwright | true | https://en.msa.gov.cn/ | [U] |
| India DG Shipping | Ocean | News Page | India | india_dg_shipping | official | 4 | 0.85 | playwright | true | https://www.dgshipping.gov.in/ | [U] |
| DNV — Maritime News | Ocean | RSS | Global | dnv_maritime | official | 2 | 0.90 | rss | false | https://www.dnv.com/news/?category=maritime/feed/ | [U] |
| Lloyd's Register — Maritime News | Ocean | News Page | Global | lloyds_register | official | 2 | 0.90 | playwright | true | https://www.lr.org/en/latest-news/ | [U] |
| Bureau Veritas — Marine | Ocean | News Page | Global | bv_marine | official | 2 | 0.85 | playwright | true | https://marine-offshore.bureauveritas.com/newsroom | [U] |
| ClassNK — News | Ocean | News Page | Japan | classnk | official | 4 | 0.85 | playwright | true | https://www.classnk.or.jp/hp/en/info_service/news/ | [U] |
| ABS — News | Ocean | News Page | US | abs_classification | official | 4 | 0.85 | playwright | true | https://ww2.eagle.org/en/news.html | [U] |
| Norwegian Maritime Authority | Ocean | News Page | Norway | nma_norway | official | 4 | 0.90 | playwright | true | https://www.sdir.no/en/news/ | [U] |
| Danish Maritime Authority | Ocean | News Page | Denmark | dma_denmark | official | 4 | 0.90 | playwright | true | https://dma.dk/news | [U] |
| Swedish Transport Agency — Maritime | Ocean | News Page | Sweden | sta_sweden | official | 4 | 0.85 | playwright | true | https://www.transportstyrelsen.se/en/ | [U] |
| Singapore MPA — Circulars | Ocean | News Page | Singapore | mpa_circulars | official | 1 | 0.95 | playwright | true | https://www.mpa.gov.sg/regulations/port-marine-circulars | [U] |

---

## C — Aviation & Air Cargo Authorities

> **Already in `sources.py`**: iata_cargo, icao, aci_aero

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FAA — Notices/Advisories | Air | RSS | US | faa_notams | official | 1 | 0.95 | rss | false | https://www.faa.gov/rss_feeds | [U] |
| EASA (EU Aviation Safety) | Air | RSS | EU | easa | official | 4 | 0.95 | rss | false | https://www.easa.europa.eu/en/rss-feeds | [U] |
| UK CAA — Cargo | Air | News Page | UK | uk_caa | official | 4 | 0.90 | playwright | true | https://www.caa.co.uk/news/ | [U] |
| CAAC (China Civil Aviation Admin) | Air | News Page | China | caac_china | official | 4 | 0.85 | playwright | true | http://www.caac.gov.cn/en/ | [U] |
| DGCA India | Air | News Page | India | dgca_india | official | 4 | 0.85 | playwright | true | https://dgca.gov.in/digigov-portal/ | [U] |
| Transport Canada — Civil Aviation | Air | RSS | Canada | tc_aviation | official | 4 | 0.90 | rss | false | https://tc.canada.ca/en/aviation.atom | [U] |
| CASA (Australia Civil Aviation) | Air | News Page | Australia | casa_au | official | 4 | 0.90 | playwright | true | https://www.casa.gov.au/news-and-media | [U] |
| Eurocontrol — NM Dashboard | Air | API | EU | eurocontrol | official | 1 | 0.95 | api | false | https://www.eurocontrol.int/dashboard/rss | [U] |
| TIACA (International Air Cargo Assn) | Air | News Page | Global | tiaca | official | 2 | 0.85 | playwright | true | https://tiaca.org/news/ | [U] |
| FIATA — Air Freight | Air | News Page | Global | fiata_air | official | 4 | 0.85 | playwright | true | https://fiata.org/what-we-do/air-freight/ | [U] |
| The International Air Cargo Association | Air | News Page | Global | iaca | official | 4 | 0.80 | playwright | true | https://www.tiaca.org/news/ | [U] |
| Airports Council International — Europe | Air | News Page | EU | aci_europe | official | 2 | 0.90 | playwright | true | https://www.aci-europe.org/media-room/press-releases.html | [U] |
| Airports Council International — Asia Pacific | Air | News Page | APAC | aci_apac | official | 2 | 0.85 | playwright | true | https://www.aci-asiapac.aero/media | [U] |
| Changi Airport Group — Cargo | Air | News Page | Singapore | changi_cargo | official | 1 | 0.90 | playwright | true | https://www.changiairport.com/corporate/media-centre/news-releases.html | [U] |
| Dubai DWC / Al Maktoum Cargo | Air | News Page | UAE | dwc_cargo | official | 1 | 0.85 | playwright | true | https://www.dubaiairports.ae/corporate/media-centre/press-releases | [U] |
| Hong Kong Airport Authority — Cargo | Air | News Page | Hong Kong | hk_airport_cargo | official | 1 | 0.90 | playwright | true | https://www.hongkongairport.com/en/media-centre/press-release/ | [U] |
| Incheon Airport — Cargo | Air | News Page | South Korea | incheon_cargo | official | 1 | 0.85 | playwright | true | https://www.airport.kr/co/en/cpr/prcenterMain.do | [U] |
| Heathrow — Cargo | Air | News Page | UK | heathrow_cargo | official | 1 | 0.90 | playwright | true | https://www.heathrow.com/company/about-heathrow/press-office | [U] |
| Frankfurt Airport — Cargo | Air | News Page | Germany | fra_cargo | official | 1 | 0.90 | playwright | true | https://www.fraport.com/en/newsroom.html | [U] |
| Schiphol — Cargo | Air | News Page | Netherlands | schiphol_cargo | official | 1 | 0.90 | playwright | true | https://www.schiphol.nl/en/schiphol-group/page/press-office/ | [U] |
| Memphis Airport (FedEx Hub) | Air | News Page | US | memphis_airport | official | 1 | 0.85 | playwright | true | https://flymemphis.com/news/ | [U] |
| Louisville SDF (UPS Worldport) | Air | News Page | US | louisville_airport | official | 1 | 0.85 | playwright | true | https://www.sdfairport.com/about/news-media | [U] |
| Anchorage Airport — Cargo | Air | News Page | US | anc_cargo | official | 1 | 0.85 | playwright | true | https://www.anchorageairport.com/news/ | [U] |

---

## D — Customs Agencies

> **Already in `sources.py`**: us_cbp, us_fed_register, eu_dg_taxud, uk_hmrc, wco, tr_trade

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EU TARIC (Tariff Database) | Multimodal | API | EU | eu_taric | official | 4 | 0.95 | api | false | https://ec.europa.eu/taxation_customs/dds2/taric/ | [U] |
| Canada CBSA — Trade | Multimodal | RSS | Canada | ca_cbsa | official | 4 | 0.90 | rss | false | https://www.cbsa-asfc.gc.ca/rss/menu-eng.html | [U] |
| Japan Customs | Multimodal | News Page | Japan | jp_customs | official | 4 | 0.85 | playwright | true | https://www.customs.go.jp/english/news/ | [U] |
| Korea Customs Service | Multimodal | News Page | South Korea | kr_customs | official | 4 | 0.85 | playwright | true | https://www.customs.go.kr/english/ | [U] |
| China Customs (GACC) | Multimodal | News Page | China | cn_customs | official | 4 | 0.85 | playwright | true | http://english.customs.gov.cn/News/ | [U] |
| India CBIC | Multimodal | News Page | India | in_cbic | official | 4 | 0.85 | playwright | true | https://www.cbic.gov.in/ | [U] |
| Singapore Customs | Multimodal | News Page | Singapore | sg_customs | official | 4 | 0.90 | playwright | true | https://www.customs.gov.sg/news-and-media/ | [U] |
| Australia ABF | Multimodal | News Page | Australia | au_abf | official | 4 | 0.90 | playwright | true | https://www.abf.gov.au/newsroom-subsite/Pages/Media.aspx | [U] |
| NZ Customs Service | Multimodal | News Page | NZ | nz_customs | official | 4 | 0.85 | playwright | true | https://www.customs.govt.nz/news/ | [U] |
| Brazil Receita Federal | Multimodal | News Page | Brazil | br_customs | official | 4 | 0.85 | playwright | true | https://www.gov.br/receitafederal/en/ | [U] |
| Mexico SAT | Multimodal | News Page | Mexico | mx_customs | official | 4 | 0.85 | playwright | true | https://www.sat.gob.mx/english | [U] |
| South Africa SARS — Customs | Multimodal | News Page | South Africa | za_customs | official | 4 | 0.85 | playwright | true | https://www.sars.gov.za/customs-and-excise/ | [U] |
| UAE Federal Customs Authority | Multimodal | News Page | UAE | uae_customs | official | 4 | 0.85 | playwright | true | https://www.fca.gov.ae/en/Pages/default.aspx | [U] |
| Saudi Customs (ZATCA) | Multimodal | News Page | Saudi Arabia | sa_customs | official | 4 | 0.85 | playwright | true | https://zatca.gov.sa/en/MediaCenter/Pages/News.aspx | [U] |
| Swiss Federal Customs | Multimodal | News Page | Switzerland | ch_customs | official | 4 | 0.90 | playwright | true | https://www.bazg.admin.ch/bazg/en/home.html | [U] |
| US OFAC — Sanctions | Multimodal | RSS | US | us_ofac | official | 4 | 0.95 | rss | false | https://ofac.treasury.gov/rss/recent-actions | [U] |
| EU Sanctions Map | Multimodal | News Page | EU | eu_sanctions | official | 4 | 0.95 | playwright | true | https://sanctionsmap.eu/ | [U] |
| BIS — Export Controls (US) | Multimodal | RSS | US | us_bis | official | 4 | 0.95 | rss | false | https://www.bis.gov/rss.xml | [U] |

---

## E — Logistics Company IR / Newsrooms

> **Strategy**: Major publicly traded shipping/logistics companies' investor relations and press pages. Key for earnings signals, capacity announcements, rate guidance.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A.P. Moller-Maersk — Press | Ocean | News Page | Global | maersk_ir | news | 2 | 0.95 | playwright | true | https://www.maersk.com/news | [U] |
| Hapag-Lloyd — Investor Relations | Ocean | News Page | Global | hapag_lloyd_ir | news | 2 | 0.90 | playwright | true | https://www.hapag-lloyd.com/en/company/ir.html | [U] |
| MSC — Media Room | Ocean | News Page | Global | msc_news | news | 2 | 0.90 | playwright | true | https://www.msc.com/newsroom | [U] |
| CMA CGM — Newsroom | Ocean | News Page | Global | cma_cgm_news | news | 2 | 0.90 | playwright | true | https://www.cmacgm-group.com/en/news-medias | [U] |
| COSCO Shipping — Announcements | Ocean | News Page | Global | cosco_news | news | 2 | 0.85 | playwright | true | https://en.coscoshipping.com/col/col7763/index.html | [U] |
| Evergreen Marine — News | Ocean | News Page | Global | evergreen_news | news | 2 | 0.85 | playwright | true | https://www.evergreen-line.com/tei1st/jsp/TEI1_News.jsp | [U] |
| ONE (Ocean Network Express) — News | Ocean | News Page | Global | one_news | news | 2 | 0.85 | playwright | true | https://www.one-line.com/en/news | [U] |
| Yang Ming — News | Ocean | News Page | Global | yang_ming_news | news | 2 | 0.85 | playwright | true | https://www.yangming.com/News/Press_Release.aspx | [U] |
| HMM — News | Ocean | News Page | Global | hmm_news | news | 2 | 0.85 | playwright | true | https://www.hmm21.com/cms/company/engn/introduce/media/news/index.jsp | [U] |
| ZIM — Investor Relations | Ocean | News Page | Global | zim_ir | news | 2 | 0.85 | playwright | true | https://www.zim.com/news | [U] |
| Kuehne+Nagel — Media | Multimodal | RSS | Global | kn_media | news | 2 | 0.90 | rss | false | https://www.kuehne-nagel.com/en/press-releases/feed | [U] |
| DSV — Press | Multimodal | News Page | Global | dsv_press | news | 2 | 0.90 | playwright | true | https://www.dsv.com/en/press | [U] |
| DHL Group — Press | Multimodal | RSS | Global | dhl_press | news | 2 | 0.95 | rss | false | https://group.dhl.com/en/media-relations/press-releases.rss | [U] |
| DB Schenker — News | Multimodal | News Page | Global | db_schenker_news | news | 2 | 0.85 | playwright | true | https://www.dbschenker.com/global/about/news | [U] |
| FedEx — Newsroom | Air/Road | RSS | Global | fedex_news | news | 2 | 0.90 | rss | false | https://newsroom.fedex.com/rss | [U] |
| UPS — Press Releases | Air/Road | News Page | Global | ups_news | news | 2 | 0.90 | playwright | true | https://about.ups.com/us/en/newsroom/press-releases.html | [U] |
| C.H. Robinson — News | Multimodal | News Page | Global | chr_news | news | 2 | 0.85 | playwright | true | https://www.chrobinson.com/en-us/newsroom/ | [U] |
| XPO Logistics — News | Road | News Page | US/EU | xpo_news | news | 2 | 0.80 | playwright | true | https://www.xpo.com/news/ | [U] |
| Expeditors — News | Multimodal | News Page | Global | expeditors_news | news | 2 | 0.85 | playwright | true | https://www.expeditors.com/news | [U] |
| Flexport — Blog/News | Multimodal | RSS | Global | flexport_blog | news | 2 | 0.75 | rss | false | https://www.flexport.com/blog/feed/ | [U] |
| CEVA Logistics — News | Multimodal | News Page | Global | ceva_news | news | 2 | 0.85 | playwright | true | https://www.cevalogistics.com/en/news | [U] |
| Bollore Logistics — News | Multimodal | News Page | Global | bollore_news | news | 2 | 0.80 | playwright | true | https://www.bollore-logistics.com/en/news/ | [U] |
| Wan Hai Lines — News | Ocean | News Page | Asia | wan_hai_news | news | 2 | 0.80 | playwright | true | https://www.wanhai.com/views/Main.xhtml | [U] |
| PIL (Pacific Int'l Lines) — News | Ocean | News Page | Asia | pil_news | news | 2 | 0.80 | playwright | true | https://www.pilship.com/en-pil-pacific-international-lines/news.html | [U] |
| Nippon Yusen (NYK Line) — News | Ocean | News Page | Japan | nyk_news | news | 2 | 0.85 | playwright | true | https://www.nyk.com/english/news/ | [U] |
| Mitsui O.S.K. Lines — Press | Ocean | News Page | Japan | mol_news | news | 2 | 0.85 | playwright | true | https://www.mol.co.jp/en/pr/ | [U] |
| "K" Line — News | Ocean | News Page | Japan | kline_news | news | 2 | 0.85 | playwright | true | https://www.kline.co.jp/en/news/ | [U] |

---

## F — Regional Freight News by Continent

> **Already in `sources.py`**: loadstar, freightwaves, joc, supplychaindive, gcaptain, splash247, etc.

### New Sources — Not in `sources.py`

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ship Technology | Ocean | RSS | Global | ship_technology | news | 2 | 0.75 | rss | false | https://www.ship-technology.com/feed/ | [V] |
| Offshore Energy | Ocean | RSS | Global | offshore_energy | news | 2 | 0.80 | rss | false | https://www.offshore-energy.biz/feed/ | [V] |
| Maritime Professional | Ocean | RSS | Global | maritime_professional | news | 2 | 0.80 | rss | false | https://www.maritimeprofessional.com/rss | [V] |
| SAFETY4SEA | Ocean | RSS | Global | safety4sea | news | 2 | 0.80 | rss | false | https://safety4sea.com/feed/ | [V] |
| DC Velocity | Multimodal | RSS | US | dc_velocity | news | 2 | 0.80 | rss | false | https://www.dcvelocity.com/rss/ | [V] |
| Ship & Bunker | Ocean | News Page | Global | ship_bunker | news | 2 | 0.75 | playwright | true | https://shipandbunker.com/news | [U] |
| Ship.Energy (Bunkerspot) | Ocean | RSS | Global | ship_energy | news | 2 | 0.75 | rss | false | https://ship.energy/rss | [V] |
| World Maritime News (Offshore Energy) | Ocean | RSS | Global | world_maritime_news | news | 2 | 0.75 | rss | false | https://worldmaritimenews.com/feed/ | [U] |
| Logistics Manager | Multimodal | RSS | UK | logistics_manager | news | 2 | 0.75 | rss | false | https://www.logisticsmanager.com/feed/ | [U] |
| Motor Transport | Road | RSS | UK | motor_transport | news | 2 | 0.70 | rss | false | https://motortransport.co.uk/feed/ | [U] |
| Shipping Watch | Ocean | News Page | EU | shipping_watch | news | 2 | 0.80 | playwright | true | https://shippingwatch.com/ | [P] |
| American Shipper | Multimodal | News Page | US | american_shipper | news | 2 | 0.80 | playwright | true | https://www.freightwaves.com/american-shipper | [U] |
| SupplyChainBrain | Multimodal | RSS | US | supplychainbrain | news | 2 | 0.75 | rss | false | https://www.supplychainbrain.com/rss | [U] |
| Logistics Management | Multimodal | RSS | US | logistics_mgmt | news | 2 | 0.75 | rss | false | https://www.logisticsmgmt.com/rss | [U] |
| Inbound Logistics | Multimodal | RSS | US | inbound_logistics | news | 2 | 0.70 | rss | false | https://www.inboundlogistics.com/feed/ | [U] |
| Global Trade Magazine | Multimodal | RSS | US | global_trade_mag | news | 2 | 0.70 | rss | false | https://www.globaltrademag.com/feed/ | [U] |
| Caixin Logistics (CN) | Multimodal | News Page | China | caixin_logistics | news | 2 | 0.80 | playwright | true | https://www.caixinglobal.com/ | [P] |
| Nikkei Asia — Logistics | Multimodal | News Page | Japan | nikkei_logistics | news | 2 | 0.80 | playwright | true | https://asia.nikkei.com/Business/Transportation | [P] |
| DVZ (Deutsche Verkehrs-Zeitung) | Multimodal | News Page | Germany | dvz | news | 2 | 0.80 | playwright | true | https://www.dvz.de/ | [P] |
| Verkehrsrundschau | Road | News Page | Germany | verkehrsrundschau | news | 2 | 0.75 | playwright | true | https://www.verkehrsrundschau.de/ | [P] |
| L'Antenne (Le Journal Maritime) | Ocean | News Page | France | lantenne | news | 2 | 0.75 | playwright | true | https://www.lantenne.com/ | [U] |
| ITJ (International Transport Journal) | Multimodal | News Page | EU | itj | news | 2 | 0.80 | playwright | true | https://www.transportjournal.com/ | [P] |
| Baltic Shipping | Ocean | News Page | Nordics | baltic_shipping | news | 2 | 0.75 | playwright | true | https://www.balticshipping.com/ | [U] |
| Port Strategy | Ocean | RSS | Global | port_strategy | news | 2 | 0.75 | rss | false | https://www.portstrategy.com/feed/ | [U] |
| Handy Shipping Guide | Ocean | News Page | Global | handy_shipping | news | 2 | 0.70 | playwright | true | https://www.handyshippingguide.com/shipping-news/ | [U] |
| SCM Globe | Multimodal | News Page | Global | scm_globe | news | 2 | 0.65 | playwright | true | https://www.scmglobe.com/ | [U] |
| Manifest — Modern Logistics | Multimodal | RSS | US | manifest_log | news | 2 | 0.70 | rss | false | https://www.manifest.group/blog-feed.xml | [U] |

---

## G — Port Community Systems & Congestion Data

> **Strategy**: Real-time port operational data — vessel schedules, gate statuses, congestion dashboards. High-value Tier 1 sources.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Signal (Port of LA Vessel Schedule) | Ocean | API | US | signal_pola | physical | 1 | 0.95 | api | false | https://www.portoflosangeles.org/business/supply-chain/signal | [U] |
| POLB — Supply Chain Info | Ocean | News Page | US | polb_supply_chain | physical | 1 | 0.95 | playwright | true | https://polb.com/business/port-performance/ | [U] |
| Marine Exchange of SoCal | Ocean | News Page | US | marine_exchange_socal | physical | 1 | 0.90 | playwright | true | https://www.mxsocal.org/ | [U] |
| PortXchange (Rotterdam PCS) | Ocean | API | Netherlands | portxchange | physical | 1 | 0.90 | api | false | https://www.portxchange.com/ | [U] |
| Portbase (NL PCS) | Ocean | API | Netherlands | portbase | physical | 1 | 0.90 | api | false | https://www.portbase.com/ | [U] |
| NxtPort (Antwerp PCS) | Ocean | API | Belgium | nxtport | physical | 1 | 0.90 | api | false | https://www.nxtport.com/ | [U] |
| dakosy (Hamburg PCS) | Ocean | API | Germany | dakosy | physical | 1 | 0.90 | api | false | https://www.dakosy.de/en/ | [U] |
| INTTRA (now e5) — Ocean Visibility | Ocean | API | Global | inttra | physical | 1 | 0.85 | api | false | https://www.e5.ai/ | [U] |
| CargoSmart | Ocean | API | Global | cargosmart | physical | 1 | 0.85 | api | false | https://www.cargosmart.com/ | [U] |
| Windward — Maritime AI | Ocean | API | Global | windward | physical | 1 | 0.90 | api | false | https://windward.ai/ | [U] |
| Kpler — Commodity Intelligence | Ocean | API | Global | kpler | pricing | 1 | 0.90 | api | false | https://www.kpler.com/ | [P] |
| Sinay — Port Congestion | Ocean | API | Global | sinay | physical | 1 | 0.85 | api | false | https://sinay.ai/ | [U] |
| Portcast — ETA Predictions | Ocean | API | Global | portcast | physical | 1 | 0.85 | api | false | https://www.portcast.io/ | [U] |
| Sea/ — Container Tracking | Ocean | API | Global | sea_rates | physical | 1 | 0.80 | api | false | https://www.searates.com/services/tracking/ | [U] |

---

## H — Geopolitical & Maritime Security

> **Already in `sources.py`**: ukmto, gdacs, reliefweb, cisa_alerts

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dryad Global — Maritime Security | Ocean | News Page | Global | dryad_global | news | 2 | 0.85 | playwright | true | https://www.dryad.global/maritime-security-threat-advisory | [U] |
| IMF PortWatch | Ocean | API | Global | imf_portwatch | official | 2 | 0.95 | api | false | https://portwatch.imf.org/ | [U] |
| ACLED (Armed Conflict) | Multimodal | API | Global | acled | official | 2 | 0.90 | api | false | https://acleddata.com/data-export-tool/ | [U] |
| IMB Piracy Reporting Centre | Ocean | News Page | Global | imb_piracy | official | 2 | 0.95 | playwright | true | https://www.icc-ccs.org/piracy-reporting-centre | [U] |
| ReCAAP (Asian Piracy) | Ocean | News Page | Asia | recaap | official | 2 | 0.90 | playwright | true | https://www.recaap.org/resources/ck/files/reports/ | [U] |
| MDAT-GoG (Gulf of Guinea) | Ocean | News Page | Africa | mdat_gog | official | 2 | 0.90 | playwright | true | https://gog-mdat.org/ | [U] |
| Combined Maritime Forces (CMF) | Ocean | RSS | Global | cmf | official | 2 | 0.90 | rss | false | https://combinedmaritimeforces.com/feed/ | [U] |
| EU NAVFOR — Operation Atalanta | Ocean | RSS | Indian Ocean | eu_navfor | official | 2 | 0.90 | rss | false | https://eunavfor.eu/feed/ | [U] |
| NATO MARCOM | Ocean | News Page | Global | nato_marcom | official | 2 | 0.90 | playwright | true | https://mc.nato.int/media-centre/news | [U] |
| Global Sanctions Dashboard | Multimodal | News Page | Global | sanctions_dashboard | official | 2 | 0.85 | playwright | true | https://sanctionsnews.bakermckenzie.com/ | [U] |
| Chatham House — Trade & Econ | Multimodal | RSS | Global | chatham_house | news | 2 | 0.85 | rss | false | https://www.chathamhouse.org/rss | [U] |
| IISS — Armed Conflict Survey | Multimodal | News Page | Global | iiss | news | 2 | 0.85 | playwright | true | https://www.iiss.org/press/ | [U] |
| STRATFOR | Multimodal | News Page | Global | stratfor | news | 2 | 0.80 | playwright | true | https://worldview.stratfor.com/ | [P] |
| Crisis Group | Multimodal | RSS | Global | crisis_group | news | 2 | 0.85 | rss | false | https://www.crisisgroup.org/latest-updates/rss | [U] |
| RAND — Homeland Security | Multimodal | RSS | US | rand_homeland | news | 2 | 0.80 | rss | false | https://www.rand.org/topics/homeland-security-and-terrorism.html/feed | [U] |

---

## I — Energy / Fuel / Bunker Pricing

> **Strategy**: Fuel/bunker prices are leading indicators for freight rate changes.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Ship & Bunker — Prices | Ocean | News Page | Global | ship_bunker_prices | pricing | 1 | 0.85 | playwright | true | https://shipandbunker.com/prices | [U] |
| Bunker Index | Ocean | News Page | Global | bunkerindex | pricing | 1 | 0.85 | playwright | true | https://www.bunkerindex.com/ | [U] |
| Platts — Shipping | Ocean | News Page | Global | platts_shipping | pricing | 2 | 0.90 | playwright | true | https://www.spglobal.com/commodityinsights/en/market-insights/topics/shipping | [P] |
| Argus Media — Freight | Multimodal | News Page | Global | argus_freight | pricing | 2 | 0.90 | playwright | true | https://www.argusmedia.com/en/news/freight | [P] |
| EIA (US Energy Info Admin) | Multimodal | API | US | eia_petroleum | pricing | 2 | 0.95 | api | false | https://api.eia.gov/v2/petroleum/ | [U] |
| OPEC Monthly Oil Report | Multimodal | News Page | Global | opec_monthly | pricing | 4 | 0.95 | playwright | true | https://www.opec.org/opec_web/en/publications/338.htm | [U] |
| IEA — Oil Market Report | Multimodal | News Page | Global | iea_oil | pricing | 4 | 0.95 | playwright | true | https://www.iea.org/reports/oil-market-report | [P] |
| Singapore MPA — Bunker Sales | Ocean | News Page | Singapore | mpa_bunker | pricing | 2 | 0.90 | playwright | true | https://www.mpa.gov.sg/regulations/port-marine-circulars | [U] |
| ENGINE (Bunker Brokers) | Ocean | News Page | Global | engine_bunker | pricing | 2 | 0.80 | playwright | true | https://engine.online/news | [U] |

---

## J — Commodity & Financial Indices

> **Strategy**: Commodity prices signal trade volume shifts. Financial indices track logistics company health.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CME Group — Freight Futures | Ocean | API | Global | cme_freight | pricing | 1 | 0.95 | api | false | https://www.cmegroup.com/markets/freight.html | [U] |
| ICE Futures — Commodities | Multimodal | API | Global | ice_futures | pricing | 1 | 0.95 | api | false | https://www.theice.com/market-data | [U] |
| LME (London Metal Exchange) | Multimodal | API | Global | lme | pricing | 1 | 0.95 | api | false | https://www.lme.com/Market-data | [U] |
| Shanghai Containerized Freight Index (SCFI) | Ocean | News Page | China | scfi | pricing | 1 | 0.90 | playwright | true | https://en.sse.net.cn/ | [U] |
| CCFI (China Containerized Freight Index) | Ocean | News Page | China | ccfi | pricing | 1 | 0.90 | playwright | true | https://en.sse.net.cn/ | [U] |
| New ConTex (Container Ship Time Charter) | Ocean | News Page | Global | new_contex | pricing | 1 | 0.90 | playwright | true | https://www.vhss.de/en/new-contex/ | [U] |
| Harpex (Container Ship Charter Index) | Ocean | News Page | Global | harpex | pricing | 1 | 0.90 | playwright | true | https://www.harperpetersen.com/harpex | [U] |
| ClarkSea Index | Ocean | News Page | Global | clarksea | pricing | 2 | 0.90 | playwright | true | https://www.clarksons.com/services/broking/clarksea-index/ | [P] |
| Shanghai Shipping Exchange | Ocean | News Page | China | sse_shipping | pricing | 1 | 0.90 | playwright | true | https://en.sse.net.cn/ | [U] |
| DAX Transport Sector (Germany) | Multimodal | API | EU | dax_transport | pricing | 2 | 0.85 | api | false | https://www.boerse-frankfurt.de/ | [U] |
| S&P Transportation Select Index | Multimodal | API | US | sp_transport | pricing | 2 | 0.85 | api | false | https://www.spglobal.com/ | [U] |
| Dow Jones Transportation Average | Multimodal | API | US | djta | pricing | 2 | 0.85 | api | false | https://www.wsj.com/market-data/quotes/index/DJT | [U] |
| Cass Freight Index | Road | News Page | US | cass_freight | pricing | 2 | 0.85 | playwright | true | https://www.cassinfo.com/freight-audit-payment/cass-transportation-indexes/cass-freight-index-report/ | [U] |
| Outbound Tender Reject Index (OTRI) | Road | API | US | otri_sonar | pricing | 1 | 0.85 | api | false | https://www.freightwaves.com/sonar | [P] |

---

## K — Social / Forums / Reddit

> **Already in `sources.py`**: reddit_logistics, reddit_freight, reddit_supplychain, reddit_shipping, reddit_truckers, reddit_aviation, reddit_freightbrokers, hackernews

### Additional Reddit Subreddits

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Reddit r/maritime | Ocean | API | Global | reddit_maritime | social | 3 | 0.30 | api | false | https://www.reddit.com/r/maritime/new.json?limit=50 | [U] |
| Reddit r/commercialshipping | Ocean | API | Global | reddit_commercialshipping | social | 3 | 0.30 | api | false | https://www.reddit.com/r/commercialshipping/new.json?limit=50 | [U] |
| Reddit r/merchantmarine | Ocean | API | Global | reddit_merchantmarine | social | 3 | 0.30 | api | false | https://www.reddit.com/r/merchantmarine/new.json?limit=50 | [U] |
| Reddit r/Longshoremen | Ocean | API | US | reddit_longshoremen | social | 3 | 0.30 | api | false | https://www.reddit.com/r/Longshoremen/new.json?limit=50 | [U] |
| Reddit r/portoperations | Ocean | API | Global | reddit_portops | social | 3 | 0.25 | api | false | https://www.reddit.com/r/portoperations/new.json?limit=50 | [U] |
| Reddit r/CustomsBroker | Multimodal | API | US | reddit_customs | social | 3 | 0.30 | api | false | https://www.reddit.com/r/CustomsBroker/new.json?limit=50 | [U] |
| Reddit r/Importexport | Multimodal | API | Global | reddit_importexport | social | 3 | 0.30 | api | false | https://www.reddit.com/r/Importexport/new.json?limit=50 | [U] |
| Reddit r/truckdrivers | Road | API | US | reddit_truckdrivers | social | 3 | 0.30 | api | false | https://www.reddit.com/r/truckdrivers/new.json?limit=50 | [U] |
| Reddit r/trains | Rail | API | Global | reddit_trains | social | 3 | 0.25 | api | false | https://www.reddit.com/r/trains/new.json?limit=50 | [U] |
| Reddit r/railroading | Rail | API | US | reddit_railroading | social | 3 | 0.30 | api | false | https://www.reddit.com/r/railroading/new.json?limit=50 | [U] |
| Reddit r/WarehouseWorkers | Multimodal | API | US | reddit_warehouse | social | 3 | 0.25 | api | false | https://www.reddit.com/r/WarehouseWorkers/new.json?limit=50 | [U] |
| Reddit r/ExportControls | Multimodal | API | US | reddit_exportcontrols | social | 3 | 0.30 | api | false | https://www.reddit.com/r/ExportControls/new.json?limit=50 | [U] |
| Reddit r/ecommerce | Multimodal | API | Global | reddit_ecommerce | social | 3 | 0.25 | api | false | https://www.reddit.com/r/ecommerce/new.json?limit=50 | [U] |
| Reddit r/FulfillmentByAmazon | Multimodal | API | US | reddit_fba | social | 3 | 0.25 | api | false | https://www.reddit.com/r/FulfillmentByAmazon/new.json?limit=50 | [U] |
| Reddit r/3PL | Multimodal | API | Global | reddit_3pl | social | 3 | 0.30 | api | false | https://www.reddit.com/r/3PL/new.json?limit=50 | [U] |
| Reddit r/LastMileDelivery | Road | API | Global | reddit_lastmile | social | 3 | 0.25 | api | false | https://www.reddit.com/r/LastMileDelivery/new.json?limit=50 | [U] |
| Reddit r/OilAndGasWorkers | Multimodal | API | Global | reddit_oilgas | social | 3 | 0.30 | api | false | https://www.reddit.com/r/oilandgasworkers/new.json?limit=50 | [U] |
| Reddit r/economics | Multimodal | API | Global | reddit_economics | social | 3 | 0.35 | api | false | https://www.reddit.com/r/economics/new.json?limit=50 | [U] |
| Reddit r/trade | Multimodal | API | Global | reddit_trade | social | 3 | 0.30 | api | false | https://www.reddit.com/r/trade/new.json?limit=50 | [U] |
| Reddit r/geopolitics | Multimodal | API | Global | reddit_geopolitics | social | 3 | 0.35 | api | false | https://www.reddit.com/r/geopolitics/new.json?limit=50 | [U] |
| Reddit r/energy | Multimodal | API | Global | reddit_energy | social | 3 | 0.30 | api | false | https://www.reddit.com/r/energy/new.json?limit=50 | [U] |

### Forums & Other Social

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gCaptain Forum | Ocean | News Page | Global | gcaptain_forum | social | 3 | 0.35 | playwright | true | https://gcaptain.com/forum/ | [U] |
| ShippingWatch Forum | Ocean | News Page | EU | shippingwatch_forum | social | 3 | 0.35 | playwright | true | https://shippingwatch.com/ | [P] |
| StackOverflow — Logistics Tag | Multimodal | API | Global | so_logistics | social | 3 | 0.30 | api | false | https://api.stackexchange.com/2.3/questions?tagged=logistics | [U] |
| LinkedIn Pulse — Logistics Tag | Multimodal | RSS | Global | linkedin_logistics | social | 3 | 0.35 | rss | false | https://www.linkedin.com/pulse/logistics | [U] |
| Quora — Shipping & Logistics | Multimodal | News Page | Global | quora_logistics | social | 3 | 0.25 | playwright | true | https://www.quora.com/topic/Logistics | [U] |

---

## L — Technology / Tracking / Visibility

> **Already in `sources.py`**: project44, fourkites, marinetraffic, vesselfinder, opensky, flightradar24

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Vizion API (Container Tracking) | Ocean | API | Global | vizion_api | physical | 1 | 0.85 | api | false | https://vizionapi.com/ | [U] |
| Terminal49 | Ocean | API | Global | terminal49 | physical | 1 | 0.85 | api | false | https://terminal49.com/ | [U] |
| Portchain | Ocean | API | Global | portchain | physical | 1 | 0.85 | api | false | https://www.portchain.com/ | [U] |
| DHL Resilience360 / Risk Intelligence | Multimodal | API | Global | dhl_risk | physical | 1 | 0.90 | api | false | https://www.dhl.com/global-en/home/our-divisions/global-forwarding-freight/risk-intelligence.html | [U] |
| Everstream Analytics | Multimodal | API | Global | everstream | physical | 1 | 0.85 | api | false | https://www.everstream.ai/ | [U] |
| Resilinc — Supply Chain Risk | Multimodal | API | Global | resilinc | physical | 1 | 0.85 | api | false | https://www.resilinc.com/ | [U] |
| Overhaul (Cargo Security) | Multimodal | API | Global | overhaul_track | physical | 1 | 0.80 | api | false | https://over-haul.com/ | [U] |
| Spire Maritime — AIS | Ocean | API | Global | spire_ais | geoint | 1 | 0.90 | api | false | https://spire.com/maritime/ | [U] |
| exactEarth — AIS | Ocean | API | Global | exactearth | geoint | 1 | 0.85 | api | false | https://www.exactearth.com/ | [U] |
| AIS Hub | Ocean | API | Global | ais_hub | geoint | 1 | 0.80 | api | false | https://www.aishub.net/ | [U] |
| Fleetmon | Ocean | API | Global | fleetmon | geoint | 1 | 0.80 | api | false | https://www.fleetmon.com/ | [U] |
| myShipTracking | Ocean | API | Global | myshiptracking | geoint | 1 | 0.75 | api | false | https://www.myshiptracking.com/ | [U] |

---

## M — Trade Associations & Industry Bodies

> **Already in `sources.py`**: bimco, iru, uic, aci_aero

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ICS (Int'l Chamber of Shipping) | Ocean | News Page | Global | ics | official | 4 | 0.90 | playwright | true | https://www.ics-shipping.org/press-releases/ | [U] |
| INTERTANKO | Ocean | News Page | Global | intertanko | official | 4 | 0.85 | playwright | true | https://www.intertanko.com/news/ | [U] |
| Intercargo | Ocean | News Page | Global | intercargo | official | 4 | 0.85 | playwright | true | https://www.intercargo.org/news/ | [U] |
| World Shipping Council | Ocean | News Page | Global | wsc | official | 4 | 0.90 | playwright | true | https://www.worldshipping.org/news | [U] |
| International Group of P&I Clubs | Ocean | News Page | Global | ig_pi | official | 4 | 0.85 | playwright | true | https://www.igpandi.org/news/ | [U] |
| FIATA | Multimodal | News Page | Global | fiata | official | 4 | 0.90 | playwright | true | https://fiata.org/media-news/ | [U] |
| Clecat (EU Freight Forwarders) | Multimodal | News Page | EU | clecat | official | 4 | 0.85 | playwright | true | https://www.clecat.org/news | [U] |
| CSCMP (Council of SC Professionals) | Multimodal | News Page | Global | cscmp | official | 4 | 0.85 | playwright | true | https://cscmp.org/CSCMP/Media/CSCMP/Educate/SCQ_Magazine.aspx | [U] |
| AAPA (American Assn Port Authorities) | Ocean | News Page | Americas | aapa | official | 4 | 0.85 | playwright | true | https://www.aapa-ports.org/advocating/Communications.aspx | [U] |
| ESPO (European Sea Ports Org) | Ocean | News Page | EU | espo | official | 4 | 0.85 | playwright | true | https://www.espo.be/news/ | [U] |
| IAPH (Int'l Assn Ports & Harbors) | Ocean | News Page | Global | iaph | official | 4 | 0.85 | playwright | true | https://www.iaphworldports.org/news | [U] |
| ATA (American Trucking Assns) | Road | News Page | US | ata | official | 4 | 0.85 | playwright | true | https://www.trucking.org/news-insights | [U] |
| IANA (Intermodal Assn NA) | Multimodal | News Page | US | iana | official | 4 | 0.85 | playwright | true | https://www.intermodal.org/news | [U] |
| AAR (Assn of American Railroads) | Rail | News Page | US | aar | official | 4 | 0.90 | playwright | true | https://www.aar.org/news/ | [U] |
| CER (Community of European Railway) | Rail | News Page | EU | cer | official | 4 | 0.85 | playwright | true | https://www.cer.be/news/ | [U] |
| SMI (Shipbuilders/Marine Eng) | Ocean | News Page | Global | smi | official | 4 | 0.75 | playwright | true | https://www.shipbuildingindustry.eu/news/ | [U] |
| TCA (Truckload Carriers Assn) | Road | News Page | US | tca | official | 4 | 0.80 | playwright | true | https://www.truckload.org/news | [U] |
| CITA (Cargo Incident Notification System) | Multimodal | News Page | Global | cins | official | 4 | 0.85 | playwright | true | https://www.cinsnet.com/ | [U] |
| Global Shippers Forum | Multimodal | News Page | Global | gsf | official | 4 | 0.80 | playwright | true | https://www.globalshippersforum.com/news/ | [U] |
| TT Club (Transport Insurance) | Multimodal | News Page | Global | tt_club | official | 4 | 0.80 | playwright | true | https://www.ttclub.com/news-and-resources/ | [U] |

---

## N — Research / Analytics / Consulting

> **Already in `sources.py`**: drewry, xeneta, sea_intelligence, alphaliner

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Clarksons Research | Ocean | News Page | Global | clarksons | news | 2 | 0.90 | playwright | true | https://www.clarksons.com/news/ | [P] |
| MSI (Maritime Strategies Int'l) | Ocean | News Page | Global | msi_maritime | news | 2 | 0.85 | playwright | true | https://www.msiltd.com/news/ | [P] |
| MDS Transmodal | Multimodal | News Page | Global | mds_transmodal | news | 2 | 0.80 | playwright | true | https://www.mdst.co.uk/articles/ | [U] |
| Ti Insight (Transport Intelligence) | Multimodal | News Page | Global | ti_insight | news | 2 | 0.85 | playwright | true | https://www.ti-insight.com/news/ | [P] |
| McKinsey — Logistics | Multimodal | RSS | Global | mckinsey_logistics | news | 2 | 0.80 | rss | false | https://www.mckinsey.com/industries/travel-logistics-and-infrastructure/rss | [U] |
| BCG — Logistics | Multimodal | News Page | Global | bcg_logistics | news | 2 | 0.80 | playwright | true | https://www.bcg.com/industries/transportation-logistics | [U] |
| Deloitte — Supply Chain | Multimodal | News Page | Global | deloitte_sc | news | 2 | 0.80 | playwright | true | https://www.deloitte.com/global/en/Industries/consumer/analysis/supply-chain.html | [U] |
| Gartner — Supply Chain Blog | Multimodal | RSS | Global | gartner_sc | news | 2 | 0.85 | rss | false | https://www.gartner.com/en/supply-chain/insights/rss | [U] |
| Container Trades Statistics (CTS) | Ocean | News Page | Global | cts | news | 4 | 0.90 | playwright | true | https://www.containerstatistics.com/ | [P] |
| UNCTAD Review of Maritime Transport | Ocean | News Page | Global | unctad_rmt | official | 4 | 0.95 | playwright | true | https://unctad.org/topic/transport-and-trade-logistics/review-of-maritime-transport | [U] |

---

## O — Rail Freight Operators & Authorities

> **Already in `sources.py`**: railfreight_com, railway_age, irj, uic, up_rail, bnsf_rail, csx_rail, ns_rail

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Canadian Pacific Kansas City (CPKC) | Rail | RSS | North America | cpkc_rail | official | 4 | 0.90 | rss | false | https://www.cpkcr.com/en/investors-and-media/media/news-releases/feed | [U] |
| Canadian National (CN) Rail | Rail | News Page | Canada | cn_rail | official | 4 | 0.90 | playwright | true | https://www.cn.ca/en/news/ | [U] |
| Deutsche Bahn Cargo | Rail | News Page | EU | db_cargo | official | 4 | 0.85 | playwright | true | https://www.dbcargo.com/rail-de-en/company/press-releases | [U] |
| Network Rail | Rail | RSS | UK | network_rail | official | 4 | 0.90 | rss | false | https://www.networkrail.co.uk/feeds/news/ | [U] |
| SNCF Fret (Freight) | Rail | News Page | France | sncf_fret | official | 4 | 0.85 | playwright | true | https://www.sncf.com/en/group/news | [U] |
| ÖBB Rail Cargo Group | Rail | News Page | Austria | obb_cargo | official | 4 | 0.85 | playwright | true | https://www.railcargo.com/en/news | [U] |
| SBB Cargo | Rail | News Page | Switzerland | sbb_cargo | official | 4 | 0.85 | playwright | true | https://www.sbbcargo.com/en/news.html | [U] |
| PKP Cargo | Rail | News Page | Poland | pkp_cargo | official | 4 | 0.80 | playwright | true | https://www.pkpcargo.com/en/press-room/ | [U] |
| China Railway Corporation | Rail | News Page | China | china_railway | official | 4 | 0.85 | playwright | true | http://www.china-railway.com.cn/en/ | [U] |
| Indian Railways — Freight | Rail | News Page | India | indian_railways | official | 4 | 0.85 | playwright | true | https://indianrailways.gov.in/railwayboard/ | [U] |
| Russian Railways (RZD) — Freight | Rail | News Page | Russia | rzd | official | 4 | 0.80 | playwright | true | https://eng.rzd.ru/en/9545 | [U] |
| Trans-Caspian Int'l Transport Route (TITR) | Rail | News Page | Central Asia | titr | official | 4 | 0.80 | playwright | true | https://middlecorridor.com/en/ | [U] |
| RailPulse (US Rail Visibility) | Rail | News Page | US | railpulse | physical | 2 | 0.80 | playwright | true | https://www.railpulse.com/news | [U] |
| Progressive Railroading | Rail | RSS | US | progressive_rail | news | 2 | 0.75 | rss | false | https://www.progressiverailroading.com/rss/ | [U] |
| Railway Gazette International | Rail | RSS | Global | railway_gazette | news | 2 | 0.80 | rss | false | https://www.railwaygazette.com/rss | [U] |
| Trains Magazine | Rail | RSS | US | trains_magazine | news | 2 | 0.70 | rss | false | https://www.trains.com/trn/feed/ | [U] |
| Rail Freight Forward | Rail | News Page | EU | rail_freight_forward | official | 4 | 0.80 | playwright | true | https://www.railfreightforward.eu/news | [U] |

---

## P — Trucking / Road Freight Regulators

> **Already in `sources.py`**: transport_topics, overdrive, fleetowner, iru, ccj, us_fmcsa

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DVSA (UK Driver & Vehicle Standards) | Road | RSS | UK | uk_dvsa | official | 4 | 0.90 | rss | false | https://www.gov.uk/government/organisations/driver-and-vehicle-standards-agency.atom | [U] |
| European Commission — Road Transport | Road | News Page | EU | ec_road_transport | official | 4 | 0.90 | playwright | true | https://transport.ec.europa.eu/transport-modes/road_en | [U] |
| FHWA (US Federal Highway Admin) | Road | RSS | US | fhwa | official | 4 | 0.90 | rss | false | https://highways.dot.gov/rss.xml | [U] |
| BGL (German Freight Transport Assn) | Road | News Page | Germany | bgl_de | official | 4 | 0.80 | playwright | true | https://www.bgl-ev.de/presse/ | [U] |
| FTA (Freight Transport Assn) — UK | Road | RSS | UK | fta_uk | official | 4 | 0.85 | rss | false | https://logistics.org.uk/media/press-releases/rss | [U] |
| TLN (Transport en Logistiek Nederland) | Road | News Page | Netherlands | tln | official | 4 | 0.80 | playwright | true | https://www.tln.nl/nieuws/ | [U] |
| FNTR (France Road Transport Fed) | Road | News Page | France | fntr | official | 4 | 0.80 | playwright | true | https://www.fntr.fr/actualites | [U] |
| FreightCar America | Road | RSS | US | freightcar_america | news | 2 | 0.70 | rss | false | https://www.freightcaramerica.com/blog/feed/ | [U] |
| Truckinginfo | Road | RSS | US | truckinginfo | news | 2 | 0.70 | rss | false | https://www.truckinginfo.com/rss/ | [U] |
| Heavy Duty Trucking | Road | RSS | US | hdt | news | 2 | 0.70 | rss | false | https://www.truckinginfo.com/heavy-duty-trucking/rss/ | [U] |
| Land Line Magazine (OOIDA) | Road | RSS | US | land_line | news | 2 | 0.70 | rss | false | https://landline.media/feed/ | [U] |
| Eurotransport | Road | News Page | EU | eurotransport | news | 2 | 0.75 | playwright | true | https://www.eurotransportmagazine.com/news/ | [U] |
| HAULAGE Exchange (UK) | Road | News Page | UK | haulage_exchange | news | 2 | 0.65 | playwright | true | https://www.haulageexchange.co.uk/blog/ | [U] |
| JB Hunt — Investor Relations | Road | News Page | US | jbhunt_ir | news | 2 | 0.85 | playwright | true | https://www.jbhunt.com/investor-relations/ | [U] |
| Schneider National — News | Road | News Page | US | schneider_news | news | 2 | 0.80 | playwright | true | https://schneider.com/company/news | [U] |
| Werner Enterprises — News | Road | News Page | US | werner_news | news | 2 | 0.80 | playwright | true | https://www.werner.com/blog/ | [U] |
| Old Dominion Freight — News | Road | News Page | US | old_dominion_news | news | 2 | 0.80 | playwright | true | https://www.odfl.com/us/en/about-od/newsroom.html | [U] |
| SAIA Inc — News | Road | News Page | US | saia_news | news | 2 | 0.75 | playwright | true | https://www.saia.com/about/news | [U] |
| Amazon Logistics — Press | Multimodal | RSS | Global | amazon_logistics | news | 2 | 0.85 | rss | false | https://www.aboutamazon.com/news/tag/transportation/feed | [U] |

---

---

## [AUTOMATED_BACKFILL] — Sources in Code Not in Catalog

> **Auto-generated**: 98 sources from `sources.py` that were missing from this catalog.
> Review and move entries to their proper sections above.

| Source Name | Primary Mode | Data Type | Geo Scope | source_key | source_type | tier | reliability | ingestion_method | needs_playwright | URL | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baltic Exchange (Dry Index) | Ocean | News Page | Global | baltic_exchange | pricing | 1 | 0.95 | playwright | true | https://www.balticexchange.com/en/data-services/market-information.html | [CODE] |
| BleepingComputer | Multimodal | RSS | Global | bleepingcomputer | cyber | 1 | 0.70 | rss | false | https://www.bleepingcomputer.com/feed/ | [CODE] |
| CISA Alerts | Multimodal | RSS | Global | cisa_alerts | cyber | 1 | 0.95 | rss | false | https://www.cisa.gov/cybersecurity-advisories/all.xml | [CODE] |
| DarkReading | Multimodal | RSS | Global | darkreading | cyber | 1 | 0.70 | rss | false | https://www.darkreading.com/rss.xml | [CODE] |
| DAT Freight & Analytics | Road | News Page | Global | dat_freight | pricing | 1 | 0.90 | playwright | true | https://www.dat.com/industry-trends/trendlines | [CODE] |
| FlightRadar24 — Disruptions | Air | RSS | Global | flightradar24 | geoint | 1 | 0.80 | rss | false | https://www.flightradar24.com/blog/feed/ | [CODE] |
| FourKites — Visibility Intel | Multimodal | RSS | Global | fourkites | news | 1 | 0.85 | rss | false | https://www.fourkites.com/blog/feed/ | [CODE] |
| Freightos FBX Live | Ocean | News Page | Global | freightos_fbx_live | pricing | 1 | 0.90 | playwright | true | https://fbx.freightos.com/ | [CODE] |
| ICS-CERT Advisories | Multimodal | RSS | Global | ics_cert | cyber | 1 | 0.95 | rss | false | https://www.cisa.gov/uscert/ics/advisories/advisories.xml | [CODE] |
| MarineTraffic News | Ocean | RSS | Global | marinetraffic | geoint | 1 | 0.85 | rss | false | https://www.marinetraffic.com/blog/feed/ | [CODE] |
| NASA FIRMS — Active Fire Data | Multimodal | API | Global | nasa_firms | geoint | 1 | 0.95 | api | false | https://firms.modaps.eosdis.nasa.gov/api/area/csv | [CODE] |
| OpenSky Network — ADS-B | Air | API | Global | opensky | geoint | 1 | 0.85 | api | false | https://opensky-network.org/api/states/all | [CODE] |
| Port of Antwerp-Bruges | Multimodal | RSS | Global | port_antwerp | official | 1 | 0.90 | rss | false | https://newsroom.portofantwerpbruges.com/rss | [CODE] |
| Port of Hamburg | Multimodal | RSS | Global | port_hamburg | official | 1 | 0.90 | rss | false | https://www.hafen-hamburg.de/en/feed/ | [CODE] |
| Port of Los Angeles — Signal | Ocean | RSS | Global | port_la | official | 1 | 0.95 | rss | false | https://www.portoflosangeles.org/references/news_newsfeed.xml | [CODE] |
| Port of Long Beach | Ocean | RSS | Global | port_long_beach | official | 1 | 0.95 | rss | false | https://polb.com/feed/ | [CODE] |
| Port of Rotterdam | Multimodal | RSS | Global | port_rotterdam | official | 1 | 0.95 | rss | false | https://www.portofrotterdam.com/en/news/rss | [CODE] |
| Port of Shanghai (SIPG) | Ocean | News Page | Global | port_shanghai | official | 1 | 0.90 | playwright | true | https://www.portshanghai.com.cn/en/news.html | [CODE] |
| Maritime and Port Authority of Singapore | Ocean | RSS | Global | port_singapore | official | 1 | 0.95 | rss | false | https://www.mpa.gov.sg/media-centre/rss | [CODE] |
| Project44 — Supply Chain Visibility | Multimodal | RSS | Global | project44 | news | 1 | 0.85 | rss | false | https://www.project44.com/blog/feed | [CODE] |
| The Record by Recorded Future | Multimodal | RSS | Global | recorded_future | cyber | 1 | 0.80 | rss | false | https://therecord.media/feed | [CODE] |
| Copernicus Sentinel Hub | Multimodal | API | Global | sentinel_hub | geoint | 1 | 0.90 | api | false | https://services.sentinel-hub.com/api/v1/ | [CODE] |
| TAC Index (Air Cargo Rates) | Air | News Page | Global | tac_index | pricing | 1 | 0.90 | playwright | true | https://www.tacindex.com/ | [CODE] |
| VesselFinder News | Ocean | RSS | Global | vesselfinder | geoint | 1 | 0.80 | rss | false | https://www.vesselfinder.com/news/rss | [CODE] |
| Windy — Severe Weather | Multimodal | API | Global | windy | geoint | 1 | 0.85 | api | false | https://api.windy.com/api/webcams/v3/ | [CODE] |
| Airport Council International | Air | RSS | Global | aci_aero | official | 2 | 0.90 | rss | false | https://aci.aero/feed/ | [CODE] |
| Air Cargo News | Air | RSS | Global | aircargo_news | news | 2 | 0.85 | rss | false | https://www.aircargonews.net/feed/ | [CODE] |
| Air Cargo World | Air | RSS | Global | aircargo_world | news | 2 | 0.80 | rss | false | https://aircargoworld.com/feed/ | [CODE] |
| Alphaliner | Ocean | News Page | Global | alphaliner | news | 2 | 0.90 | playwright | true | https://alphaliner.axsmarine.com/PublicTop100/ | [CODE] |
| BIMCO — Market Analysis | Ocean | News Page | Global | bimco | news | 2 | 0.90 | playwright | true | https://www.bimco.org/news-and-trends | [CODE] |
| Bloomberg Supply Chain | Multimodal | RSS | Global | bloomberg_supply_chain | news | 2 | 0.95 | rss | false | https://www.bloomberg.com/feed/supply-chain | [CODE] |
| Cargo Facts | Air | RSS | Global | cargo_facts | news | 2 | 0.80 | rss | false | https://cargofacts.com/feed/ | [CODE] |
| Commercial Carrier Journal | Road | RSS | Global | ccj | news | 2 | 0.70 | rss | false | https://www.ccjdigital.com/feed/ | [CODE] |
| Container News | Ocean | RSS | Global | container_news | news | 2 | 0.75 | rss | false | https://container-news.com/feed/ | [CODE] |
| Drewry Shipping Consultants | Ocean | RSS | Global | drewry | pricing | 2 | 0.90 | rss | false | https://www.drewry.co.uk/feed | [CODE] |
| FleetOwner | Road | RSS | Global | fleetowner | news | 2 | 0.75 | rss | false | https://www.fleetowner.com/rss | [CODE] |
| FlightGlobal Cargo | Air | RSS | Global | flightglobal | news | 2 | 0.80 | rss | false | https://www.flightglobal.com/rss | [CODE] |
| Freightos Blog (FBX Index) | Ocean | RSS | Global | freightos_fbx | pricing | 2 | 0.85 | rss | false | https://www.freightos.com/blog/feed/ | [CODE] |
| Freightwaves | Multimodal | RSS | Global | freightwaves | news | 2 | 0.80 | rss | false | https://www.freightwaves.com/feed | [CODE] |
| gCaptain | Ocean | RSS | Global | gcaptain | news | 2 | 0.80 | rss | false | https://gcaptain.com/feed/ | [CODE] |
| GDACS Disaster Alerts | Multimodal | RSS | Global | gdacs | official | 2 | 0.95 | rss | false | https://www.gdacs.org/xml/rss.xml | [CODE] |
| Hellenic Shipping News | Ocean | RSS | Global | hellenic_shipping | news | 2 | 0.70 | rss | false | https://www.hellenicshippingnews.com/feed/ | [CODE] |
| IMF — Data API | Multimodal | RSS | Global | imf | official | 2 | 0.95 | rss | false | https://www.imf.org/en/News/rss | [CODE] |
| International Railway Journal | Rail | RSS | Global | irj | news | 2 | 0.85 | rss | false | https://www.railjournal.com/feed/ | [CODE] |
| IRU — International Road Transport Union | Road | News Page | Global | iru | official | 2 | 0.90 | playwright | true | https://www.iru.org/news-resources/newsroom | [CODE] |
| Journal of Commerce | Multimodal | RSS | Global | joc | news | 2 | 0.90 | rss | false | https://www.joc.com/rss | [CODE] |
| Lloyd's List | Ocean | RSS | Global | lloyds_list | news | 2 | 0.90 | rss | false | https://lloydslist.maritimeintelligence.informa.com/rss | [CODE] |
| The Loadstar | Multimodal | RSS | Global | loadstar | news | 2 | 0.85 | rss | false | https://theloadstar.com/feed/ | [CODE] |
| Maritime Executive | Ocean | RSS | Global | maritime_executive | news | 2 | 0.75 | rss | false | https://maritime-executive.com/rss | [CODE] |
| NOAA Active Alerts | Multimodal | API | Global | noaa_alerts | official | 2 | 0.95 | api | false | https://api.weather.gov/alerts/active | [CODE] |
| OECD — Trade Policy | Multimodal | RSS | Global | oecd_trade | official | 2 | 0.90 | rss | false | https://www.oecd.org/trade/rss/ | [CODE] |
| Overdrive Online | Road | RSS | Global | overdrive | news | 2 | 0.70 | rss | false | https://www.overdriveonline.com/feed/ | [CODE] |
| Payload Asia | Air | RSS | Global | payload_asia | news | 2 | 0.75 | rss | false | https://www.payloadasia.com/feed/ | [CODE] |
| Port Technology International | Ocean | RSS | Global | port_tech_intl | news | 2 | 0.80 | rss | false | https://www.porttechnology.org/feed/ | [CODE] |
| RailFreight.com | Rail | RSS | Global | railfreight_com | news | 2 | 0.85 | rss | false | https://www.railfreight.com/feed/ | [CODE] |
| Railway Age | Rail | RSS | Global | railway_age | news | 2 | 0.75 | rss | false | https://www.railwayage.com/feed/ | [CODE] |
| ReliefWeb — Disasters | Multimodal | RSS | Global | reliefweb | official | 2 | 0.90 | rss | false | https://reliefweb.int/updates/rss.xml?content-format=report&primary_country=world | [CODE] |
| Reuters — Supply Chain | Multimodal | RSS | Global | reuters_supply_chain | news | 2 | 0.95 | rss | false | https://www.reuters.com/arc/outboundfeeds/rss/category/supply-chain/ | [CODE] |
| Sea-Intelligence | Ocean | News Page | Global | sea_intelligence | news | 2 | 0.90 | playwright | true | https://sea-intelligence.com/press-room | [CODE] |
| Seatrade Maritime | Ocean | RSS | Global | seatrade | news | 2 | 0.75 | rss | false | https://www.seatrade-maritime.com/rss.xml | [CODE] |
| Simple Flying — Cargo | Air | RSS | Global | simple_flying | news | 2 | 0.65 | rss | false | https://simpleflying.com/feed/ | [CODE] |
| Splash247 | Ocean | RSS | Global | splash247 | news | 2 | 0.75 | rss | false | https://splash247.com/feed/ | [CODE] |
| STAT Trade Times | Air | RSS | Global | stat_trade_times | news | 2 | 0.80 | rss | false | https://www.stattimes.com/feed/ | [CODE] |
| Supply Chain Dive | Multimodal | RSS | Global | supplychaindive | news | 2 | 0.75 | rss | false | https://www.supplychaindive.com/feeds/news/ | [CODE] |
| TradeWinds | Ocean | RSS | Global | tradewinds | news | 2 | 0.85 | rss | false | https://www.tradewindsnews.com/rss | [CODE] |
| Transport Topics | Road | RSS | Global | transport_topics | news | 2 | 0.80 | rss | false | https://www.ttnews.com/rss.xml | [CODE] |
| UIC — International Union of Railways | Rail | News Page | Global | uic | official | 2 | 0.90 | playwright | true | https://uic.org/com/enews/ | [CODE] |
| UKMTO Maritime Security | Ocean | News Page | Global | ukmto | official | 2 | 0.95 | playwright | true | https://www.ukmto.org/recent-incidents | [CODE] |
| UN Comtrade — Trade Statistics | Multimodal | API | Global | un_comtrade | api | 2 | 0.95 | api | false | https://comtradeapi.un.org/public/v1/preview/C/A/HS | [CODE] |
| UNCTAD — Trade & Development | Multimodal | RSS | Global | unctad | official | 2 | 0.90 | rss | false | https://unctad.org/rss.xml | [CODE] |
| World Bank — Trade Data | Multimodal | RSS | Global | world_bank | official | 2 | 0.95 | rss | false | https://blogs.worldbank.org/feed | [CODE] |
| WTO — Trade News | Multimodal | RSS | Global | wto | official | 2 | 0.95 | rss | false | https://www.wto.org/english/news_e/news_e.rss | [CODE] |
| Xeneta Updates | Multimodal | RSS | Global | xeneta | pricing | 2 | 0.85 | rss | false | https://www.xeneta.com/blog/rss.xml | [CODE] |
| Hacker News — Logistics/Supply Chain | Multimodal | API | Global | hackernews | social | 3 | 0.40 | api | false | https://hn.algolia.com/api/v1/search_by_date | [CODE] |
| Reddit r/aviationmaintenance | Air | API | Global | reddit_aviation | social | 3 | 0.25 | api | false | https://www.reddit.com/r/aviationmaintenance/new.json?limit=50 | [CODE] |
| Reddit r/freightforwarding | Multimodal | API | Global | reddit_freight | social | 3 | 0.35 | api | false | https://www.reddit.com/r/FreightForwarding/new.json?limit=50 | [CODE] |
| Reddit r/freightbrokers | Multimodal | API | Global | reddit_freightbrokers | social | 3 | 0.35 | api | false | https://www.reddit.com/r/FreightBrokers/new.json?limit=50 | [CODE] |
| Reddit r/logistics | Multimodal | API | Global | reddit_logistics | social | 3 | 0.35 | api | false | https://www.reddit.com/r/logistics/new.json?limit=50 | [CODE] |
| Reddit r/shipping | Multimodal | API | Global | reddit_shipping | social | 3 | 0.30 | api | false | https://www.reddit.com/r/shipping/new.json?limit=50 | [CODE] |
| Reddit r/supplychain | Multimodal | API | Global | reddit_supplychain | social | 3 | 0.30 | api | false | https://www.reddit.com/r/supplychain/new.json?limit=50 | [CODE] |
| Reddit r/truckers | Road | API | Global | reddit_truckers | social | 3 | 0.30 | api | false | https://www.reddit.com/r/Truckers/new.json?limit=50 | [CODE] |
| BNSF Service Alerts | Rail | News Page | Global | bnsf_rail | official | 4 | 0.90 | playwright | true | https://www.bnsf.com/ship-with-bnsf/maps-and-shipping-locations/service-alerts.html | [CODE] |
| CSX Service Alerts | Rail | News Page | Global | csx_rail | official | 4 | 0.90 | playwright | true | https://www.csx.com/index.cfm/library/files/about-us/news-feed/ | [CODE] |
| EU DG TAXUD News | Multimodal | News Page | Global | eu_dg_taxud | official | 4 | 0.95 | playwright | true | https://taxation-customs.ec.europa.eu/news_en | [CODE] |
| ERA — EU Agency for Railways | Rail | News Page | Global | eu_era | official | 4 | 0.90 | playwright | true | https://www.era.europa.eu/content/press-releases_en | [CODE] |
| IATA Cargo Updates | Air | News Page | Global | iata_cargo | official | 4 | 0.95 | playwright | true | https://www.iata.org/en/programs/cargo/ | [CODE] |
| ICAO — Safety & Security | Air | News Page | Global | icao | official | 4 | 0.95 | playwright | true | https://www.icao.int/Newsroom/Pages/default.aspx | [CODE] |
| IMO News | Ocean | News Page | Global | imo | official | 4 | 0.95 | playwright | true | https://www.imo.org/en/MediaCentre/Pages/WhatsNew.aspx | [CODE] |
| Norfolk Southern Service Updates | Rail | News Page | Global | ns_rail | official | 4 | 0.90 | playwright | true | https://www.norfolksouthern.com/en/ship-with-us/service-updates | [CODE] |
| Türkiye Ticaret Bakanlığı | Multimodal | RSS | Global | tr_trade | official | 4 | 0.85 | rss | false | https://www.ticaret.gov.tr/rss | [CODE] |
| UK HMRC Trade | Multimodal | RSS | Global | uk_hmrc | official | 4 | 0.90 | rss | false | https://www.gov.uk/government/organisations/hm-revenue-customs.atom | [CODE] |
| Union Pacific Service Alerts | Rail | News Page | Global | up_rail | official | 4 | 0.90 | playwright | true | https://www.up.com/customers/announcements/index.htm | [CODE] |
| US CBP Trade Updates | Multimodal | RSS | Global | us_cbp | official | 4 | 0.95 | rss | false | https://www.cbp.gov/newsroom/rss-feeds | [CODE] |
| US Federal Register — Trade | Multimodal | RSS | Global | us_fed_register | official | 4 | 0.95 | rss | false | https://www.federalregister.gov/documents/search.atom?conditions[agencies][]=customs-and-border-protection&conditions[type][]=RULE&per_page=20 | [CODE] |
| US FMC — Federal Maritime Commission | Ocean | RSS | Global | us_fmc | official | 4 | 0.95 | rss | false | https://www.fmc.gov/feed/ | [CODE] |
| FMCSA — Motor Carrier Safety | Road | RSS | Global | us_fmcsa | official | 4 | 0.95 | rss | false | https://www.fmcsa.dot.gov/newsroom/rss.xml | [CODE] |
| STB — Surface Transportation Board | Rail | RSS | Global | us_stb | official | 4 | 0.95 | rss | false | https://www.stb.gov/news-communications/latest-news/feed/ | [CODE] |
| WCO News | Multimodal | News Page | Global | wco | official | 4 | 0.95 | playwright | true | https://www.wcoomd.org/en/media/newsroom.aspx | [CODE] |

## Source Count Summary

| Section | Category | Count |
|---|---|---|
| A | Port Authorities (Top 100 Ports) | 73 |
| B | National Maritime Authorities | 19 |
| C | Aviation & Air Cargo Authorities | 23 |
| D | Customs Agencies | 18 |
| E | Logistics Company IR / Newsrooms | 27 |
| F | Regional Freight News | 27 |
| G | Port Community Systems & Congestion | 14 |
| H | Geopolitical & Maritime Security | 15 |
| I | Energy / Fuel / Bunker Pricing | 9 |
| J | Commodity & Financial Indices | 14 |
| K | Social / Forums / Reddit | 26 |
| L | Technology / Tracking / Visibility | 12 |
| M | Trade Associations & Industry Bodies | 20 |
| N | Research / Analytics / Consulting | 10 |
| O | Rail Freight Operators | 17 |
| P | Trucking / Road Freight | 19 |
| **TOTAL NEW** | | **343** |
| **Existing in sources.py** | | **~85** |
| **Catalog total** | | **~428** |

---

## Expansion Roadmap to 1000+

> The 428 above are the **high-value aggregators**. Each expands into 2-5 sub-sources:

### Phase 2: Per-Country Port Authorities (400+ sources)
- **UN Member States**: 193 countries × 1-3 port authorities each
- Priority: All UNCTAD-listed "liner shipping connectivity" countries (top 100)
- Each country's primary port authority news page is a source
- Reference: https://unctad.org/topic/transport-and-trade-logistics/ports

### Phase 3: Per-Country Customs (100+ sources)
- WCO has 184 member customs administrations
- Each with news/tariff update pages
- Reference: https://www.wcoomd.org/en/about-us/wco-members.aspx

### Phase 4: Per-Country Civil Aviation (100+ sources)
- ICAO has 193 member states, each with a national CAA
- Cargo-relevant subset: top 50 air cargo nations
- Reference: https://www.icao.int/about-icao/Pages/member-states.aspx

### Phase 5: Logistics Subreddits & Niche Forums (100+ sources)
- Reddit has 50+ logistics-adjacent subreddits
- Regional trucking forums (trucker.de, routiers.com, camionisti.it)
- Country-specific port worker forums

### Phase 6: Stock Exchange Filings (50+ sources)
- All publicly traded logistics companies with RSS-accessible IR pages
- SEC EDGAR RSS for US-listed maritime/logistics companies
- HKEX, SGX, TSE filings for Asian shipping lines

---

## Next Steps

1. **Validate `[U]` sources**: Run feed verification script against all URLs
2. **Register verified sources**: Add to `sources.py` in batches of 50
3. **Build scrapers**: For `playwright`-tagged sources, create handlers in `app/ingestion/scraper.py`
4. **API key procurement**: Sources tagged `api` may need API key registration
5. **Paywall triage**: `[P]` sources need manual evaluation for public RSS endpoints
