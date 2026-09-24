CREATE TABLE history (
    id          INTEGER PRIMARY KEY,
    created_at  TEXT    NOT NULL,
    operation   TEXT    NOT NULL CHECK (operation IN ('encrypt', 'decrypt')),
    kind        TEXT    NOT NULL CHECK (kind IN ('text', 'file')),
    engine_id   TEXT    NOT NULL,
    label       TEXT    NOT NULL DEFAULT '',
    input_size  INTEGER NOT NULL DEFAULT 0,
    output_path TEXT    NOT NULL DEFAULT '',
    duration_ms INTEGER NOT NULL DEFAULT 0,
    status      TEXT    NOT NULL CHECK (status IN ('ok', 'error', 'cancelled'))
);

CREATE INDEX history_created_at ON history (created_at DESC);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
