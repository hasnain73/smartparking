SELECT * FROM public.spot_signals
ORDER BY id ASC
INSERT INTO public.spot_signals (spot_id, signal_type, source_type, confidence_score, created_at) VALUES
('7531598524563-54155165-5481665111478', 'free', 'passive', 0.82, NOW()),
('7484519529525-15136510-3265118481699', 'occupied', 'passive', 0.91, NOW()),
('5988523515485-54646543-5156532168465', 'free', 'user', 0.76, NOW()),
('3639282471457-89214569-6598236471269', 'occupied', 'user', 0.88, NOW()),
('6546546542435-95163284-7418529634567', 'free', 'passive', 0.67, NOW()),
('6668596341632-12599632-1478523654122', 'occupied', 'passive', 0.93, NOW()),
('9357125258655-51244121-5555245455633', 'free', 'user', 0.79, NOW()),
('4225699874555-12365478-5464682168465', 'occupied', 'user', 0.85, NOW()),
('2165116465165-54511565-7441555698744', 'free', 'passive', 0.74, NOW()),
('1245936874553-51846546-5458326295661', 'occupied', 'passive', 0.89, NOW());
