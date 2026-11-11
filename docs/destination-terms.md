# Reviewed destination terms

Checked all **sixteen** supported harbors on 11 November 2026, 18:31 CET. Each was sampled through the live backend in Harbor and Wider views, with Spotlight off. Each response is capped at forty markers; this reviews the displayed sample, not every AIS message or every ship in the region. No extra AIS subscription or credentials were needed.

## Southworth / Seattle

`WSFSWUSSEAWSFSW` appears to contain `WSFSW` + `USSEA` + `WSFSW`: a Southworth–Seattle round trip. `USSEA` is Seattle's code. Kitsap Transit’s [Southworth service](https://www.kitsaptransit.com/service/fast-ferry/southworth-fast-ferry) verifies Southworth Ferry Terminal and Seattle Pier 50 as endpoints, and its [fleet page](https://www.kitsaptransit.com/agency-information/our-ferry-fleet) identifies SOLANO as a Kitsap Transit vessel acquired from WETA in 2021.

The operator's onboard `WSFSW` shorthand is not defined on those public pages. The exact string is displayed as **Route: Southworth ↔ Seattle, USA**, with `inferred: true`, source URL and `direction_known: false` retained in API metadata. Reviewed route interpretations use the same concise on-screen label as other routes; uncertainty remains in metadata and this documentation. It does not prove the next port or current direction, and does not make Washington State Ferries SOLANO's operator. `WSF` by itself expands only as a destination note with no route specified.

The [West Seattle Water Taxi page](https://kingcounty.gov/en/dept/metro/travel-options/water-taxi/west-seattle) verifies Pier 50–West Seattle. The [Weser ferry operator](https://www.weserfaehre.de/) verifies Bremerhaven–Blexen. Named route strings are shown with ↔ as declared endpoints, never inferred actual previous-port records. The misspelled Nordenham variant is explicitly interpreted. Other route/location source links are attached to each entry in [destination_terms.py](../port_of_call/destination_terms.py).

## All-harbor review

| Harbor | Unique displayed voyage labels | Added term/reference matches | Examples deferred |
|---|---:|---|---|
| rotterdam | 33 | DELFT → Delft; FRLEH → Le Havre | BEGEN; GBKYN; NIJMEGENR-DAM; NLROT; NLROZ |
| antwerp | 21 | NLVLI → Vlissingen | FRLAV |
| hamburg | 17 | BRUNSBUTTEL-HAMBURG → Route: Brunsbüttel ↔ Hamburg, Germany; DESTA → Stade; HH--SALZGITTER---HH → Route: Hamburg ↔ Salzgitter, Germany; KEHL → Kehl | — |
| bremerhaven | 19 | BEZEE → Zeebrugge; BREMERHAFEN-BLEXEN → Route: Bremerhaven ↔ Blexen, Germany; BREMERHAVEN-NORDENAM → Route: Bremerhaven ↔ Nordenham, Germany; DECUX → Cuxhaven; FIKTK → Kotka; Patrol → Activity: Patrol; Survey OPS Weser → Activity: Survey operations on the Weser; Undervanns Arbeid → Activity: Underwater work | LTKLP; NOJOS |
| felixstowe | 8 | BEZEE → Zeebrugge; GBIPS → Ipswich | GBFTX |
| southampton | 14 | ESLPA → Las Palmas; Solent Bunkering → Activity: Bunkering in the Solent | COWES; ESMOT; GBFAW; Tanger-Med, MA |
| los-angeles-long-beach | 13 | USPDX → Portland, Oregon | CCNGB; CHANNELISLHARBOR; LB-216 & Oil Islands; PH |
| new-york-new-jersey | 18 | USSSI → Brunswick, Georgia | NY; PIER83; USBOY |
| savannah | 4 | No source-backed additions in this sample | — |
| houston | 7 | No source-backed additions in this sample | GALVESTONLIGHTERING |
| seattle | 17 | CAVAN → Vancouver; Ferry → Activity: Ferry service (route unspecified); Fishing → Activity: Fishing; Fishing Grounds → Activity: Fishing grounds; Local → Activity: Local operations; Local Tour → Activity: Local tour; P50 & West Seattle → Route: Seattle Pier 50 ↔ West Seattle, USA; Pier 50 / W Seattle → Route: Seattle Pier 50 ↔ West Seattle, USA; WSF → Destination note: Washington State Ferries (route unspecified); WSFSWUSSEAWSFSW → Route: Southworth ↔ Seattle, USA | — |
| charleston | 4 | No source-backed additions in this sample | CABAS |
| singapore | 32 | TWKHH → Kaohsiung | AEBA-SG; AEBB; AEPB; AWPA; BRPDM |
| helsinki | 17 | FIKTK → Kotka; Sar → Activity: Search and rescue; Seatrial → Activity: Sea trials; TRIAL → Activity: Trials | ML R O |
| turku | 19 | Assistance → Activity: Assistance; For Sale → Status: For sale; Hydrographic Survey → Activity: Hydrographic survey; KUMLINGE-ENKLINGE → Route: Kumlinge ↔ Enklinge, Finland; Nav Training → Activity: Navigation training; SESTO → Stockholm; Sar Turku Area → Activity: Search and rescue in the Turku area; TURKU-AIRISTO-TURKU → Route: Turku ↔ Airisto, Finland | FINLIFILANSEKAP |
| rauma | 6 | Assistance → Activity: Assistance; Towage → Activity: Towage | — |

Remaining strings such as `VLA-IMM-VLA`, `ABOSJALONAGU`, Singapore anchorage codes, private berth identifiers and valid-looking code typos need stronger source evidence. They remain unchanged. No fuzzy typo correction or operator-prefix decoding runs on arbitrary input.

## Rules and sources

Known activities (search and rescue, towage, hydrographic survey, sea trials, underwater work, local operations) are labeled **Activity**, not `To …`. `FOR SALE` is a status note. These are translations of the crew-entered text, not independent proof of the ship's work. The [US Coast Guard AIS data-field reference](https://www.navcen.uscg.gov/ais-class-a-static-and-voyage-related-data) documents the destination field; semantic expansions do not replace raw values.

Fourteen exact Wikidata P1937 port/location entities were reviewed from the existing CC0 snapshot to resolve city/port duplicate matches: BEZEE (Zeebrugge), FRLEH (Le Havre), FIKTK (Kotka), SESTO (Stockholm), NLVLI (Vlissingen), TWKHH (Kaohsiung), GBIPS (Ipswich), USPDX (Portland, Oregon), CAVAN (Vancouver), DECUX (Cuxhaven), DESTA (Stade), ESLPA (Las Palmas), USSSI (Brunswick, Georgia), and DEKEH (Kehl). Entity IDs and source links are retained in the code; no coordinates are added. Reviewed spelling variants include Southamton, Bremerhafen, Brunsbuettel and Brunsbuttel. Delft (NLDFT) and Kehl (DEKEH) now resolve as named places instead of looking like opaque codes. Ambiguous short forms such as bare `NY` and unqualified `COWES` (present in both the UK and Australia) are not globally expanded.

Both ordinary labels and Ship Spotlight use the same exact-term dictionary. Raw destination values and independently sourced previous-port facts remain in the API. Reviewed non-port notes are excluded from external port-name lookups, preserving the free request budget. The parser is not a self-learning dictionary: additions require review.
