DROP TABLE IF EXISTS detects CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash TEXT,
  provider VARCHAR(50) NOT NULL,
  provider_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (provider, provider_id)
);

CREATE TABLE detects (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  image BYTEA NOT NULL,
  image_mime_type VARCHAR(50),
  detected_ingredients TEXT[],
  recommendation TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);