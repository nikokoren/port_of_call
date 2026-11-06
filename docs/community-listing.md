# Community recipe listing — draft

**Name:** Port of Call: Harbor Map

**Short description:** Real vessel positions around your chosen harbor, with an optional Ship Spotlight.

**Description:** A quiet harbor map using TRMNL's native mapping framework. Pick one port, several to cycle through, or none to tour every port; show vessel names if desired, or spotlight one ship with available voyage, flag, speed and ship facts. The shared backend handles data collection; individual users need no AIS account or API key.

**Initial coverage:** Helsinki, Turku and Rauma, Finland. Replace this line with the deployment's verified catalog only after an approved AISStream deployment; do not advertise all fifteen candidates or worldwide completeness.

**Settings:** Harbors (optional, multi-select), ship labels, Spotlight a ship, port facts. The map framing is fixed per harbor.

**Sources:** Fintraffic / digitraffic.fi (CC BY 4.0), optional Wikidata structured data (CC0), OpenStreetMap map data (ODbL) through TRMNL's framework. An AISStream listing must use its approved source terms and correct attribution instead of claiming Fintraffic is its position source.

**Limitations:** AIS observations can be incomplete, delayed or inaccurate. Counts describe recent observations in the selected port area. Destination/ETA fields are intentions supplied through AIS, not confirmed schedules. Previous port appears only where a relevant official record supports it. Not for navigation.

**Support/source:** https://github.com/nikokoren/port_of_call/issues

## Before submitting

Use the generated ZIP with a verified production polling origin. Import it into a private plugin and confirm its form, native maps, four layouts and dark mode using TRMNL's renderer and physical devices. Replace representative archived browser screenshots with final TRMNL captures for the listing. Finish the multi-day health/coverage/quota review. Follow the current publishing form in the user's TRMNL account; its fields and review cannot be completed from an unauthenticated workspace. This file does not submit or publish a community recipe.
