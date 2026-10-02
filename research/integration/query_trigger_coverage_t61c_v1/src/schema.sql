PRAGMA journal_mode=DELETE;
PRAGMA synchronous=FULL;
CREATE TABLE meta(identity TEXT NOT NULL);
CREATE TABLE global_version(revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=0));
INSERT INTO global_version VALUES(0);
CREATE TABLE scopes(tenant TEXT PRIMARY KEY, epoch INTEGER NOT NULL CHECK(typeof(epoch)='integer' AND epoch>=0));
INSERT INTO scopes VALUES('A',0),('B',0);
CREATE TABLE items(id INTEGER PRIMARY KEY,tenant TEXT NOT NULL CHECK(tenant IN ('A','B')),active INTEGER NOT NULL CHECK(active IN (0,1)),payload INTEGER NOT NULL,revision INTEGER NOT NULL CHECK(typeof(revision)='integer' AND revision>=1));
CREATE TABLE effects(request_id TEXT PRIMARY KEY,tenant TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TRIGGER item_insert AFTER INSERT ON items BEGIN
 UPDATE global_version SET revision=revision+1;
 UPDATE scopes SET epoch=epoch+1 WHERE tenant=NEW.tenant AND NEW.active=1;
END;
CREATE TRIGGER item_delete AFTER DELETE ON items BEGIN
 UPDATE global_version SET revision=revision+1;
 UPDATE scopes SET epoch=epoch+1 WHERE tenant=OLD.tenant AND OLD.active=1;
END;
CREATE TRIGGER item_update AFTER UPDATE ON items BEGIN
 UPDATE global_version SET revision=revision+1;
 UPDATE scopes SET epoch=epoch+1 WHERE tenant=OLD.tenant AND OLD.active=1;
 UPDATE scopes SET epoch=epoch+1 WHERE tenant=NEW.tenant AND NEW.active=1 AND (OLD.active<>1 OR NEW.tenant<>OLD.tenant);
END;
