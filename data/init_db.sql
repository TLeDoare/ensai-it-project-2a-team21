DROP TABLE IF EXISTS RedactedDoc CASCADE;
DROP TABLE IF EXISTS Person CASCADE;

-- Table des utilisateurs (Person)
CREATE TABLE Person (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(25) NOT NULL, -- 'utilisateur', 'superviseur', 'administrateur'
  access_token VARCHAR(50)
);

-- Table des documents traites (RedactedDoc)
CREATE TABLE RedactedDoc (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  pii_count INT DEFAULT 0,
  pii_positions VARCHAR(1000),
  author_email VARCHAR(100),
  params VARCHAR(1000) -- chemin d'enregistrement du document caviarde
);