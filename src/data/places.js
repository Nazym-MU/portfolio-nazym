// ============================================================================
// The travel gallery's content
// ----------------------------------------------------------------------------
// Hand-tagged: no EXIF parsing, no dates scraped from filenames. Adding a photo
// is one line here plus a file in the source folder.
//
// The globe (public/models/gallery/globe.glb) holds every country as a mesh
// named CTRY-<iso>; the countries listed here are the ones lit up and
// clickable. A city appears as a pin at its lat/lon once its country is open.
//
// `night: true` dims the diorama's lights so its own glow carries it.
//
// `model` is OPTIONAL and that is the point. A city with one opens as a toy
// diorama under a glass dome; a city without one just shows its photos.
// Adding a model later is dropping in a .glb (scripts/blender/<city>.py) and
// adding one key, never a code change.
//
// `objects` are the clickable things in a model: each key is a mesh named
// OBJ-<key> in the .glb. Clicking one shows its `photos`. An object with no
// photos yet still highlights and says so.
// ============================================================================

export const countries = [
    // `tone` picks one of the globe palette's hues, so the visited countries
    // read as a set of separate trips rather than one blob.
    { iso: 'US', slug: 'usa', name: 'United States', tone: 'mint', cities: ['new-york', 'san-francisco'] },
    { iso: 'GB', slug: 'uk', name: 'United Kingdom', tone: 'red', cities: ['london', 'manchester'] },
    { iso: 'AR', slug: 'argentina', name: 'Argentina', tone: 'sky', cities: ['buenos-aires'] },
    { iso: 'EG', slug: 'egypt', name: 'Egypt', tone: 'sand' },
    { iso: 'KZ', slug: 'kazakhstan', name: 'Kazakhstan', tone: 'sky', cities: ['astana', 'almaty'] },
    { iso: 'UZ', slug: 'uzbekistan', name: 'Uzbekistan', tone: 'violet' },
    { iso: 'DE', slug: 'germany', name: 'Germany', tone: 'amber' },
    { iso: 'TR', slug: 'turkey', name: 'Turkey', tone: 'red' },
    { iso: 'AE', slug: 'uae', name: 'United Arab Emirates', tone: 'sand' },
    { iso: 'JP', slug: 'japan', name: 'Japan', tone: 'rose', cities: ['tokyo'] },
    { iso: 'KR', slug: 'south-korea', name: 'South Korea', tone: 'violet', cities: ['seoul'] },
    { iso: 'TW', slug: 'taiwan', name: 'Taiwan', tone: 'mint' },
    { iso: 'TH', slug: 'thailand', name: 'Thailand', tone: 'amber' },
    { iso: 'CN', slug: 'china', name: 'China', tone: 'rose', cities: ['shanghai'] },
];

export const cities = [
    {
        slug: 'new-york',
        country: 'usa',
        name: 'New York',
        lat: 40.71, lon: -74.01,
        model: 'models/gallery/cities/new-york.glb',
        objects: {
            'times-square': { name: 'Times Square', photos: [] },
            'empire-state': { name: 'Empire State Building', photos: [] },
            'statue-of-liberty': { name: 'Statue of Liberty', photos: [] },
            'strawberry-fields': { name: 'Strawberry Fields', photos: [] },
            'the-pond': { name: 'Central Park', photos: [] },
            'subway': { name: 'The subway', photos: [] },
            'hop-on-hop-off': { name: 'Hop-on hop-off bus', photos: [] },
            'yellow-cab': { name: 'Yellow cab', photos: [] },
        },
    },
    {
        slug: 'san-francisco',
        country: 'usa',
        name: 'San Francisco',
        lat: 37.77, lon: -122.42,
        model: 'models/gallery/cities/san-francisco.glb',
        objects: {
            'golden-gate': { name: 'Golden Gate Bridge', photos: [] },
            'bay-bridge': { name: 'Bay Bridge', photos: [] },
            'cable-car': { name: 'Cable car', photos: [] },
            'bay-wheels': { name: 'Bay Wheels', photos: [] },
            'transamerica': { name: 'Transamerica Pyramid', photos: [] },
            'salesforce-tower': { name: 'Salesforce Tower', photos: [] },
            'painted-ladies': { name: 'Painted Ladies', photos: [] },
            'coit-tower': { name: 'Coit Tower', photos: [] },
            'alcatraz': { name: 'Alcatraz', photos: [] },
            'ferry-building': { name: 'Ferry Building', photos: [] },
        },
    },
    {
        slug: 'london',
        country: 'uk',
        name: 'London',
        lat: 51.51, lon: -0.13,
        tagline: 'May London always keep its ✶ spark ✶',
        model: 'models/gallery/cities/london.glb',
        objects: {
            'big-ben': { name: 'Big Ben', photos: [] },
            'shard': { name: 'The Shard', photos: [] },
            'london-eye': { name: 'London Eye', photos: [] },
            'phone-box': { name: 'Phone box', photos: [] },
            'lamp': { name: 'Фонарь', photos: [] },
            'underground': { name: 'The Underground', photos: [] },
            'bookshop': { name: 'A bookshop', photos: [] },
            'bus': { name: 'Double-decker', photos: [] },
        },
    },
    {
        slug: 'manchester',
        country: 'uk',
        name: 'Manchester',
        lat: 53.46, lon: -2.29,
        // The stadium stands in for the city: it is the part actually explored.
        // Built from the Dear United LEGO model by scripts/build-manchester.mjs.
        model: 'models/gallery/cities/manchester.glb',
        objects: {
            'stretford-end': { name: 'Stretford End', photos: [] },
            'sir-alex-ferguson-stand': { name: 'Sir Alex Ferguson Stand', photos: [] },
            'east-stand': { name: 'East Stand', photos: [] },
            'sir-bobby-charlton-stand': { name: 'Sir Bobby Charlton Stand', photos: [] },
            'pitch': { name: 'The pitch', photos: [] },
        },
    },
    {
        slug: 'buenos-aires',
        country: 'argentina',
        name: 'Buenos Aires',
        lat: -34.60, lon: -58.38,
        model: 'models/gallery/cities/buenos-aires.glb',
        objects: {
            'obelisco': { name: 'Obelisco', photos: [] },
            'caminito': { name: 'El Caminito', photos: [] },
            'la-bombonera': { name: 'La Bombonera', photos: [] },
            'teatro-colon': { name: 'Teatro Colón', photos: [] },
            'empanadas': { name: 'Empanadas', photos: [] },
            'puente-de-la-mujer': { name: 'Puente de la Mujer', photos: [] },
        },
    },
    {
        slug: 'astana',
        country: 'kazakhstan',
        name: 'Astana',
        lat: 51.17, lon: 71.45,
        model: 'models/gallery/cities/astana.glb',
        objects: {
            'baiterek': { name: 'Baiterek', photos: [] },
            'khan-shatyr': { name: 'Khan Shatyr', photos: [] },
            'pyramid': { name: 'Palace of Peace and Reconciliation', photos: [] },
            'abu-dhabi-plaza': { name: 'Abu Dhabi Plaza', photos: [] },
            'nur-alem': { name: 'Nur Alem', photos: [] },
            'expo': { name: 'EXPO pavilions', photos: [] },
            'atyrau-bridge': { name: 'Atyrau bridge', photos: [] },
        },
    },
    {
        slug: 'almaty',
        country: 'kazakhstan',
        name: 'Almaty',
        lat: 43.24, lon: 76.89,
        model: 'models/gallery/cities/almaty.glb',
        objects: {
            'koktobe-tv-tower': { name: 'Koktobe TV tower', photos: [] },
            'ferris-wheel': { name: 'Koktobe Ferris wheel', photos: [] },
            'cable-car': { name: 'Koktobe cable car', photos: [] },
            'kolsay': { name: 'Kolsay Lake', photos: [] },
            'hotel-kazakhstan': { name: 'Hotel Kazakhstan', photos: [] },
            'al-farabi': { name: 'Al-Farabi', photos: [] },
            'nurly-tau': { name: 'Nurly Tau', photos: [] },
            'first-presidents-park': { name: "First President's Park", photos: [] },
            'home': { name: 'Home, Kaskelen', photos: [] },
        },
    },
    {
        slug: 'seoul',
        country: 'south-korea',
        name: 'Seoul',
        lat: 37.55, lon: 126.99,
        model: 'models/gallery/cities/seoul.glb',
        objects: {
            'n-seoul-tower': { name: 'N Seoul Tower', photos: [] },
            'namsan-cable-car': { name: 'Namsan cable car', photos: [] },
            'gyeongbokgung': { name: 'Gyeongbokgung', photos: [] },
            'bukchon': { name: 'Bukchon Hanok Village', photos: [] },
            'myeongdong': { name: 'Myeongdong', photos: [] },
            'ddp': { name: 'Dongdaemun Design Plaza', photos: [] },
            'gangnam': { name: 'Gangnam', photos: [] },
        },
    },
    {
        slug: 'tokyo',
        country: 'japan',
        name: 'Tokyo',
        lat: 35.68, lon: 139.69,
        model: 'models/gallery/cities/tokyo.glb',
        objects: {
            'mt-fuji': { name: 'Mt. Fuji', photos: [] },
            'tokyo-tower': { name: 'Tokyo Tower', photos: [] },
            'shibuya-crossing': { name: 'Shibuya crossing', photos: [] },
            '7-eleven': { name: '7-Eleven', photos: [] },
            'familymart': { name: 'FamilyMart', photos: [] },
            'seventeen-ice': { name: 'Seventeen Ice', photos: [] },
            'torii': { name: 'Torii and sakura', photos: [] },
        },
    },
    {
        slug: 'shanghai',
        country: 'china',
        name: 'Shanghai',
        lat: 31.23, lon: 121.47,
        // Drawn at night: the lights go down so the skyline's own glow shows.
        night: true,
        model: 'models/gallery/cities/shanghai.glb',
        objects: {
            'shanghai-tower': { name: 'Shanghai Tower', photos: [] },
            'swfc': { name: 'Shanghai World Financial Center', photos: [] },
            'jin-mao': { name: 'Jin Mao Tower', photos: [] },
            'oriental-pearl': { name: 'Oriental Pearl Tower', photos: [] },
            'lujiazui-skywalk': { name: 'Lujiazui skywalk', photos: [] },
            'the-bund': { name: 'The Bund', photos: [] },
            'yu-garden': { name: 'Yu Garden', photos: [] },
            'disney-castle': { name: 'Shanghai Disneyland', photos: [] },
            'zootopia': { name: 'Zootopia', photos: [] },
            'river-cruise': { name: 'Huangpu river cruise', photos: [] },
        },
    },
];

// ---- Derived lookups. The arrays above stay authoritative for ordering. ----
export const countryBySlug = Object.fromEntries(countries.map((c) => [c.slug, c]));
export const countryByIso = Object.fromEntries(countries.map((c) => [c.iso, c]));
export const cityBySlug = Object.fromEntries(cities.map((c) => [c.slug, c]));

// Paths are derived from the slug so there is no src field to drift out of sync
// with the files on disk. One place to change if the ladder ever changes.
export const thumbUrl = (slug) => `gallery/thumb/${slug}.webp`;
export const fullUrl = (slug) => `gallery/full/${slug}.webp`;
