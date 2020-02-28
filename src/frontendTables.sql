CREATE TABLE sources ( source_name text, sp_id text, sp_name text, sp_ver text, sp_param text);
INSERT INTO "sources" VALUES('localRBD','0','rbd','0.1.0','{"pool": "rbd", "mon_host": "10.2.3.44", "user": "cephadmin", "key": "abcdefghijklmnopqrstuvwxyz=="}');
CREATE TABLE targets ( target_name text, tp_id text, tp_name text, tp_ver text, tp_param text);
INSERT INTO "targets" VALUES('remote S3','1001','s3','0.1.0','{"url": "aws.notarealurl.com:8080", "region": "default", "password": "opensesame", "container": "snappybackups", "user": "alice"}');
CREATE TABLE tenants ( name text, auth_type text, password text, target_name text);
INSERT INTO "tenants" VALUES('defaultS3','Basic','YWJjMTIzCg==','remote S3');
INSERT INTO "tenants" VALUES('defaultS3noauth','None','N/A','remote S3');
