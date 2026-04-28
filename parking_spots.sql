SELECT * FROM public.parking_spots
ORDER BY id ASC INSERT INTO public.parking_spot (
    id, latitude, longitude, parking_type, spot_type, address, is_active
)
VALUES
(gen_random_uuid(), 15.4581, 75.0069, 'street', 'sedan', 'Near College Gate', true),
(gen_random_uuid(), 15.4583, 75.0072, 'private', 'suv', 'Opp Library', true),
(gen_random_uuid(), 15.4578, 75.0065, 'street', 'two_wheeler', 'Main Road Side', true),
(gen_random_uuid(), 15.4585, 75.0078, 'private', 'hatchback', 'Parking Lot A', true),
(gen_random_uuid(), 15.4590, 75.0060, 'street', 'sedan', 'Bus Stop Area', true),
(gen_random_uuid(), 15.4575, 75.0075, 'private', 'structured', 'Mall Basement', true),
(gen_random_uuid(), 15.4587, 75.0067, 'street', 'suv', 'Near Park', true),
(gen_random_uuid(), 15.4589, 75.0071, 'private', 'sedan', 'Apartment Parking', true),
(gen_random_uuid(), 15.4579, 75.0063, 'street', 'two_wheeler', 'Side Lane', true),
(gen_random_uuid(), 15.4582, 75.0079, 'private', 'hatchback', 'Office Parking', true);