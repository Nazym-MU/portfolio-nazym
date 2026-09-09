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

export const countries = [
    {
        slug: 'usa',
        name: 'United States',
        mesh: 'CTRY-usa',
        blurb: 'New York, and a great deal of walking.',
        cities: ['new-york'],
    },
    {
        slug: 'england',
        name: 'England',
        mesh: 'CTRY-england',
        blurb: 'London, and the one ground I had to see.',
        cities: ['london', 'manchester'],
    },
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
        country: 'england',
        name: 'London',
        photos: [],
    },
    {
        slug: 'manchester',
        country: 'england',
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
