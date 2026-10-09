DROP TABLE IF EXISTS Traitement CASCADE;
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
  pii_positions JSONB,
  params JSONB -- chemin d'enregistrement du document caviarde
);

-- Table d'association Many-to-Many
CREATE TABLE Traitement (
  id_person INT NOT NULL,
  id_doc INT NOT NULL,
  action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_person, id_doc),
  FOREIGN KEY (id_person) REFERENCES Person(id) ON DELETE CASCADE,
  FOREIGN KEY (id_doc) REFERENCES RedactedDoc(id) ON DELETE CASCADE
);
