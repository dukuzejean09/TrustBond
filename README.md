**Incident covered by my system**

INSERT INTO incident_types (type_name, description, severity_weight) VALUES
    ('Theft',               'Stealing of property',                          0.70),
    ('Vandalism',           'Deliberate destruction of property',            0.50),
    ('Suspicious Activity', 'Unusual or concerning behavior',                0.40),
    ('Assault',             'Physical attack on a person',                   0.90),
    ('Fraud',               'Deceptive practices for personal gain',         0.60),
    ('Drug Activity',       'Drug-related incidents',                        0.80),
    ('Trespassing',         'Unauthorized entry onto property',              0.30),
    ('Noise Disturbance',   'Excessive or disruptive noise',                 0.20),
    ('Traffic Incident',    'Road accidents or violations',                  0.50),
    ('Other',               'Incidents not covered by other categories',     0.30);
