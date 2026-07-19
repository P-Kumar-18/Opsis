-- ============================================================================
-- 1. CUSTOM ENUMERATED TYPES (ENUMs)
-- ============================================================================

-- Track the operational or publication status of a fanfiction
CREATE TYPE status AS ENUM ('completed', 'on_going');

-- Track user-specific emotional sentiment or rating for a fanfiction
CREATE TYPE rating_types AS ENUM ('disliked', 'liked', 'loved');


-- ============================================================================
-- 2. CORE METADATA & USER BEHAVIOR TABLES
-- ============================================================================

-- Core Table: Stores global metadata for each fanfiction (e.g., scraped from AO3)
CREATE TABLE fics (
	fic_id BIGINT PRIMARY KEY,
	url TEXT NOT NULL,
    name TEXT NOT NULL,
    author TEXT,
    summary TEXT,
    hits INTEGER NOT NULL,
    bookmarks INTEGER NOT NULL,
    kudos INTEGER NOT NULL,
    current_chapters INTEGER NOT NULL,
    total_chapters INTEGER,
    words INTEGER NOT NULL,
    last_date DATE,
    status status,
    language TEXT NOT NULL,
    rating TEXT NOT NULL
);

-- Behavioral Table: Tracks a specific user's interaction with each fiction
CREATE TABLE behaviour (
	fic_id BIGINT PRIMARY KEY REFERENCES fics(fic_id),
	chapters_read INT NOT NULL,
	completed BOOL NOT NULL,
	return_visits INT NOT NULL,
	ratings rating_types
)


-- ============================================================================
-- 3. LOOKUP / VALUE TABLES (Normalization)
-- ============================================================================

-- Master list of content warnings (e.g., Graphic Violence, Major Character Death)
CREATE TABLE warning_value (
	warning_id SERIAL PRIMARY KEY,
	warning TEXT NOT NULL
);

-- Master list of relationship categories (e.g., M/M, F/M, Gen, Multi)
CREATE TABLE categories_value (
	categories_id SERIAL PRIMARY KEY,
	categories TEXT NOT NULL
);

-- Master list of media universes or fandoms (e.g., Harry Potter, Marvel)
CREATE TABLE fandom_value (
	fandom_id SERIAL PRIMARY KEY,
	fandom TEXT NOT NULL
);

-- Master list of specific romantic/platonic pairings
CREATE TABLE relationship_value (
	relationship_id SERIAL PRIMARY KEY,
	relationship TEXT NOT NULL
);

-- Master list of individual fictional characters
CREATE TABLE characters_value (
	characters_id SERIAL PRIMARY KEY,
	characters TEXT NOT NULL
);

-- Master list of additional freeform/additional tags (e.g., "Angst", "Fluff")
CREATE TABLE freeform_value (
	freeform_id SERIAL PRIMARY KEY,
	freeform TEXT NOT NULL
);


-- ============================================================================
-- 4. MANY-TO-MANY JOIN TABLES
-- ============================================================================

-- Maps multiple content warnings to multiple fanfictions
CREATE TABLE warning_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	warning_id INTEGER REFERENCES warning_value(warning_id),
	PRIMARY KEY (fic_id, warning_id)
);

-- Maps multiple demographic categories to multiple fanfictions
CREATE TABLE categories_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	categories_id INTEGER REFERENCES categories_value(categories_id),
	PRIMARY KEY (fic_id, categories_id)
);

-- Maps crossover stories or single-fandom stories to their respective fandoms
CREATE TABLE fandom_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	fandom_id INTEGER REFERENCES fandom_value(fandom_id),
	PRIMARY KEY (fic_id, fandom_id)
);

-- Maps romantic or platonic pairings to the fanfictions they appear in
CREATE TABLE relationship_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	relationship_id INTEGER REFERENCES relationship_value(relationship_id),
	PRIMARY KEY (fic_id, relationship_id)
);

-- Maps appearing characters to the fanfictions they appear in
CREATE TABLE characters_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	characters_id INTEGER REFERENCES characters_value(characters_id),
	PRIMARY KEY (fic_id, characters_id)
);

-- Maps searchable freeform tags to the fanfictions they describe
CREATE TABLE freeform_join (
	fic_id BIGINT REFERENCES fics(fic_id),
	freeform_id INTEGER REFERENCES freeform_value(freeform_id),
	PRIMARY KEY (fic_id, freeform_id)
);

--============================================================================
--- 5. UNIQUE CONSTRAINTS
--============================================================================

ALTER TABLE fandom_value
ADD CONSTRAINT unique_fandom UNIQUE (fandom);

ALTER TABLE warning_value
ADD CONSTRAINT unique_warning UNIQUE (warning);

ALTER TABLE categories_value
ADD CONSTRAINT unique_category UNIQUE (categories);

ALTER TABLE relationship_value
ADD CONSTRAINT unique_relationship UNIQUE (relationship);

ALTER TABLE characters_value
ADD CONSTRAINT unique_character UNIQUE (characters);

ALTER TABLE freeform_value
ADD CONSTRAINT unique_freeform UNIQUE (freeform);

-- ============================================================================
--- 6. EMBEDDINGS TABLE
-- ============================================================================

CREATE TABLE embeddings (
    fic_id BIGINT PRIMARY KEY,
    model_name TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    payload BYTEA NOT NULL,

    CONSTRAINT fk_embeddings_fic
        FOREIGN KEY (fic_id)
        REFERENCES fics(fic_id)
        ON DELETE CASCADE
);

----------------------------------------------------------------------------
-- 7. ON DELETE CASCADE FOR JOIN TABLES
----------------------------------------------------------------------------

BEGIN;

ALTER TABLE warning_join
DROP CONSTRAINT warning_join_fic_id_fkey;

ALTER TABLE warning_join
ADD CONSTRAINT warning_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;


ALTER TABLE categories_join
DROP CONSTRAINT categories_join_fic_id_fkey;

ALTER TABLE categories_join
ADD CONSTRAINT categories_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;


ALTER TABLE fandom_join
DROP CONSTRAINT fandom_join_fic_id_fkey;

ALTER TABLE fandom_join
ADD CONSTRAINT fandom_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;


ALTER TABLE relationship_join
DROP CONSTRAINT relationship_join_fic_id_fkey;

ALTER TABLE relationship_join
ADD CONSTRAINT relationship_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;


ALTER TABLE characters_join
DROP CONSTRAINT characters_join_fic_id_fkey;

ALTER TABLE characters_join
ADD CONSTRAINT characters_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;


ALTER TABLE freeform_join
DROP CONSTRAINT freeform_join_fic_id_fkey;

ALTER TABLE freeform_join
ADD CONSTRAINT freeform_join_fic_id_fkey
FOREIGN KEY (fic_id)
REFERENCES fics(fic_id)
ON DELETE CASCADE;

COMMIT;