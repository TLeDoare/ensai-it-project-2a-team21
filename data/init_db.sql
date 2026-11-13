DROP TABLE IF EXISTS RedactedDoc CASCADE;
DROP TABLE IF EXISTS Person CASCADE;
DROP TABLE IF EXISTS prompt_injection_attempt CASCADE;

-- Table des utilisateurs (Person)
CREATE TABLE Person (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(25) NOT NULL, -- 'utilisateur', 'superviseur', 'administrateur'
  access_token VARCHAR(50),
  access_token_hash VARCHAR(64),
  access_token_expires_at TIMESTAMPTZ
);

-- Table des documents traites (RedactedDoc)
CREATE TABLE RedactedDoc (
  id SERIAL PRIMARY KEY,
  doc_hash VARCHAR(255) NOT NULL,
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  pii_count INT DEFAULT 0,
  pii_positions TEXT,
  author_email VARCHAR(100),
  params VARCHAR(1000) -- chemin d'enregistrement du document caviarde
);

-- Table des tentatives d'injection de prompt
CREATE TABLE prompt_injection_attempt (
  id SERIAL PRIMARY KEY,
  attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user_email VARCHAR(255) NOT NULL,
  content_hash VARCHAR(255) NOT NULL,
  pattern_detected VARCHAR(255)
);