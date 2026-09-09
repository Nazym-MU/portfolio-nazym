// ============================================================================
// The travel gallery's content
// ----------------------------------------------------------------------------
// Hand-tagged: no EXIF parsing, no dates scraped from filenames. Adding a photo
// is one line here plus a file in the source folder.
//
// `model` is OPTIONAL and that is the point. A city with one gets a 3D disc; a
// city without one shows its photos and nothing else changes. Adding a model
// later is dropping in a .glb and adding one key, never a code change, so the
// Blender work never blocks shipping a city.
//
// `building` on a photo is the mesh name baked into the city's .glb WITHOUT the
// "BLD-" prefix, and may be null. Photos of food and trains legitimately belong
// to no building.
// ============================================================================

// `iso` keys into COUNTRY_PATHS in world-map.js, which is where the shape comes
// from. Everything not listed here still draws, just muted and unclickable.
export const countries = [
    // `iso` keys into COUNTRY_PATHS in world-map.js, which is where the shape
    // comes from. `tone` picks one of the map palette's hues, so the map reads
    // as a set of trips rather than one undifferentiated blob. Countries not
    // listed here still draw, just muted and unclickable.
    { iso: 'US', slug: 'usa', name: 'United States', tone: 'mint',
      blurb: 'New York, and a great deal of walking.', cities: ['new-york'] },
    { iso: 'GB', slug: 'uk', name: 'United Kingdom', tone: 'red',
      blurb: 'London, and the one ground I had to see.', cities: ['london', 'manchester'] },
    { iso: 'AR', slug: 'argentina', name: 'Argentina', tone: 'sky' },
    { iso: 'EG', slug: 'egypt', name: 'Egypt', tone: 'sand' },
    { iso: 'KZ', slug: 'kazakhstan', name: 'Kazakhstan', tone: 'sky' },
    { iso: 'UZ', slug: 'uzbekistan', name: 'Uzbekistan', tone: 'violet' },
    { iso: 'DE', slug: 'germany', name: 'Germany', tone: 'amber' },
    { iso: 'TR', slug: 'turkey', name: 'Turkey', tone: 'red' },
    { iso: 'AE', slug: 'uae', name: 'United Arab Emirates', tone: 'sand' },
    { iso: 'JP', slug: 'japan', name: 'Japan', tone: 'rose' },
    { iso: 'KR', slug: 'south-korea', name: 'South Korea', tone: 'violet' },
    { iso: 'TW', slug: 'taiwan', name: 'Taiwan', tone: 'mint' },
    { iso: 'TH', slug: 'thailand', name: 'Thailand', tone: 'amber' },
    { iso: 'CN', slug: 'china', name: 'China', tone: 'rose' },
];

export const cities = [
    {
        slug: 'new-york',
        country: 'usa',
        name: 'New York',
        // model: added once the Blender file exists — photo-only until then.
        photos: [],
    },
    {
        slug: 'london',
        country: 'uk',
        name: 'London',
        photos: [],
    },
    {
        slug: 'manchester',
        country: 'uk',
        name: 'Manchester',
        // The stadium stands in for the city: it is the part actually explored.
        // Textures halved to 1024 (69MB -> 37MB of GPU memory); geometry left
        // alone, because joining its 3,643 placed bricks destroys the seating.
        model: 'models/gallery/cities/manchester.glb',
        photos: [],
    },
];

// ---- Derived lookups. The arrays above stay authoritative for ordering. ----
export const countryBySlug = Object.fromEntries(countries.map((c) => [c.slug, c]));
export const cityBySlug = Object.fromEntries(cities.map((c) => [c.slug, c]));

// Paths are derived from the slug so there is no src field to drift out of sync
// with the files on disk. One place to change if the ladder ever changes.
export const thumbUrl = (slug) => `gallery/thumb/${slug}.webp`;
export const fullUrl = (slug) => `gallery/full/${slug}.webp`;
