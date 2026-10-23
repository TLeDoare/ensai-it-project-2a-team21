
-- Utilisateurs fictifs pour les tests de PersonDAO

INSERT INTO Person (email, password, role, access_token)
VALUES
(
    'noah.test@example.com',
    'Test1234!',
    'utilisateur',
    NULL
),
(
    'ryan.test@example.com',
    'Test5678!',
    'superviseur',
    'token-test-ryan'
);
